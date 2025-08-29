import os
from typing import List, Dict, Any, Optional
import logging
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
import pinecone
import sys
import hashlib
import time
from functools import lru_cache

# Add the current directory to the path so we can import config
sys.path.append(os.path.dirname(__file__))
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    """Service class for RAG operations with multiple LLM providers"""
    
    def __init__(self):
        self.vector_store = None
        self.llm = None
        self.available_providers = config.validate_config()
        self._search_cache = {}  # Simple in-memory cache
        self._cache_timestamps = {}  # Track cache timestamps
        self._initialize_pinecone()
        self._initialize_llm()
    
    def _get_cache_key(self, query: str, top_k: int) -> str:
        """Generate a cache key for search results"""
        # Add timestamp to force cache misses for testing
        import time
        timestamp = int(time.time() / 30)  # Cache expires every 30 seconds
        cache_string = f"{query.lower().strip()}:{top_k}:{timestamp}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _normalize_profile_names(self, query: str) -> str:
        """Normalize profile names in the query to match actual Salesforce profile names"""
        query_lower = query.lower()
        
        # Profile name mapping - map common aliases to actual profile names
        # Order matters: longer, more specific patterns first
        profile_mappings = [
            ('admin profile', 'system administrator'),
            ('sys admin', 'system administrator'),
            ('system admin', 'system administrator'),
            ('administrator', 'system administrator'),
            ('admin', 'system administrator'),
            ('standard user', 'standard user'),
            ('read only', 'read only'),
            ('marketing user', 'marketing user'),
            ('sales user', 'custom: sales profile'),
            ('support user', 'custom: support profile'),
            ('contract manager', 'contract manager'),
            ('solution manager', 'solution manager')
        ]
        
        # Apply profile name mapping to the query (only first match)
        normalized_query = query
        for alias, actual_name in profile_mappings:
            if alias in query_lower:
                # Replace the alias with the actual profile name (case-insensitive)
                import re
                pattern = re.compile(re.escape(alias), re.IGNORECASE)
                normalized_query = pattern.sub(actual_name, normalized_query, count=1)  # Only replace first occurrence
                logger.info(f"🔍 Profile mapping: '{alias}' -> '{actual_name}'")
                break  # Only apply one mapping to avoid conflicts
        
        # Prevent double mapping by checking if the result already contains the target
        if 'system administrator' in normalized_query.lower() and 'administratoristrator' in normalized_query.lower():
            # Fix the double mapping issue
            normalized_query = normalized_query.replace('administratoristrator', 'administrator')
            logger.info("🔍 Fixed double mapping issue")
        
        return normalized_query
    
    def _fetch_document_by_id(self, doc_id: str):
        """Fetch a document directly by ID using Pinecone API"""
        try:
            import os
            from pinecone import Pinecone
            from langchain.schema import Document
            
            # Initialize Pinecone directly
            pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
            index_name = os.getenv('PINECONE_INDEX_NAME', 'salesforce-schema')
            index = pc.Index(index_name)
            
            # Fetch the document by ID
            fetch_result = index.fetch(ids=[doc_id])
            if doc_id in fetch_result.vectors:
                vector_data = fetch_result.vectors[doc_id]
                # Convert to Document format
                doc = Document(
                    page_content=vector_data.metadata.get('content', ''),
                    metadata=vector_data.metadata
                )
                return doc
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch document {doc_id}: {e}")
            return None
    
    def _smart_direct_lookup(self, query: str) -> List[Document]:
        """Smart direct lookup for common query patterns"""
        query_lower = query.lower()
        results = []
        
        # Pattern 1: "fields in [Object]" -> salesforce_object_[Object]
        import re
        field_pattern = r'fields?\s+in\s+(?:my\s+)?(\w+)\s+object'
        match = re.search(field_pattern, query_lower)
        if match:
            object_name = match.group(1)
            doc_id = f"salesforce_object_{object_name.capitalize()}"
            doc = self._fetch_document_by_id(doc_id)
            if doc:
                results.append(doc)
                logger.info(f"🔍 DIRECT LOOKUP: Found {doc_id} for 'fields in {object_name}' query")
        
        # Pattern 2: "Admin profile edit on [Object]" -> security_[Object]
        admin_pattern = r'(?:admin|system\s+administrator).*?(?:edit|permission).*?(?:on\s+)?(\w+)'
        match = re.search(admin_pattern, query_lower)
        if match:
            object_name = match.group(1)
            doc_id = f"security_{object_name.capitalize()}"
            doc = self._fetch_document_by_id(doc_id)
            if doc:
                results.append(doc)
                logger.info(f"🔍 DIRECT LOOKUP: Found {doc_id} for 'Admin profile {object_name}' query")
        
        # Pattern 3: Direct object name queries
        object_pattern = r'\b(account|contact|lead|opportunity|case|user|profile)\b'
        matches = re.findall(object_pattern, query_lower)
        for obj_name in matches:
            # Try both object and security documents
            for prefix in ["salesforce_object_", "security_"]:
                doc_id = f"{prefix}{obj_name.capitalize()}"
                doc = self._fetch_document_by_id(doc_id)
                if doc and doc not in results:
                    results.append(doc)
                    logger.info(f"🔍 DIRECT LOOKUP: Found {doc_id} for '{obj_name}' query")
        
        return results
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        current_time = time.time()
        cache_age = current_time - self._cache_timestamps[cache_key]
        return cache_age < config.CACHE_TTL_SECONDS
    
    def _cache_search_result(self, cache_key: str, results: List[Document]):
        """Cache search results with timestamp"""
        if config.ENABLE_SEARCH_CACHING:
            self._search_cache[cache_key] = results
            self._cache_timestamps[cache_key] = time.time()
            logger.info(f"🔍 Cached search result for key: {cache_key[:8]}...")
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[Document]]:
        """Get cached search result if valid"""
        if (config.ENABLE_SEARCH_CACHING and 
            cache_key in self._search_cache and 
            self._is_cache_valid(cache_key)):
            logger.info(f"🔍 Using cached search result for key: {cache_key[:8]}...")
            return self._search_cache[cache_key]
        return None
    
    def _initialize_pinecone(self):
        """Initialize Pinecone vector store with updated API"""
        try:
            # Initialize Pinecone with new API
            pc = pinecone.Pinecone(api_key=config.PINECONE_API_KEY)
            
            # Get or create index
            indexes = pc.list_indexes()
            if config.PINECONE_INDEX_NAME not in [idx.name for idx in indexes]:
                logger.warning(f"Index {config.PINECONE_INDEX_NAME} not found. Please ensure the pipeline has been run.")
                return
            
            # Create embedding function for querying
            from openai import OpenAI
            from langchain_openai import OpenAIEmbeddings
            
            # Initialize OpenAI embeddings
            embedding_function = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=config.OPENAI_API_KEY
            )
            
            # Initialize vector store
            self.vector_store = PineconeVectorStore(
                index_name=config.PINECONE_INDEX_NAME,
                embedding=embedding_function
            )
            logger.info(f"Connected to Pinecone index: {config.PINECONE_INDEX_NAME}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    
    def _initialize_llm(self):
        """Initialize the LLM based on available providers with thorough response settings"""
        try:
            # Priority: OpenAI > Anthropic > Google
            if "openai" in self.available_providers:
                self.llm = ChatOpenAI(
                    model=self.available_providers["openai"]["model"],
                    temperature=config.TEMPERATURE,
                    max_tokens=config.MAX_TOKENS,  # Now 16,000 for thorough responses
                    api_key=self.available_providers["openai"]["api_key"]
                )
                logger.info(f"Using OpenAI model: {self.available_providers['openai']['model']} with {config.MAX_TOKENS} max tokens")
                
            elif "anthropic" in self.available_providers:
                self.llm = ChatAnthropic(
                    model=self.available_providers["anthropic"]["model"],
                    temperature=config.TEMPERATURE,
                    max_tokens=config.MAX_TOKENS,  # Now 16,000 for thorough responses
                    api_key=self.available_providers["anthropic"]["api_key"]
                )
                logger.info(f"Using Anthropic model: {self.available_providers['anthropic']['model']} with {config.MAX_TOKENS} max tokens")
                
            elif "google" in self.available_providers:
                self.llm = ChatGoogleGenerativeAI(
                    model=self.available_providers["google"]["model"],
                    temperature=config.TEMPERATURE,
                    max_output_tokens=config.MAX_TOKENS,  # Now 16,000 for thorough responses
                    google_api_key=self.available_providers["google"]["api_key"]
                )
                logger.info(f"Using Google model: {self.available_providers['google']['model']} with {config.MAX_TOKENS} max tokens")
                
            else:
                raise ValueError("No LLM provider configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def search_context(self, query: str, top_k: int = 10) -> List[Document]:
        """Enhanced search context with optimized strategies for large databases"""
        start_time = time.time()
        
        try:
            if not self.vector_store:
                logger.error("Vector store not initialized")
                return []
            
            # Normalize profile names in the query first
            normalized_query = self._normalize_profile_names(query)
            logger.info(f"🔍 Original query: '{query}'")
            logger.info(f"🔍 Normalized query: '{normalized_query}'")
            
            # Check cache first (use normalized query for cache key)
            cache_key = self._get_cache_key(normalized_query, top_k)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"🔍 Cache hit! Returning cached results in {time.time() - start_time:.2f}s")
                return cached_result
            
            logger.info(f"🔍 Cache miss. Performing fresh search...")
            
            # Get total document count for logging
            try:
                # Use a small search to get total count efficiently
                total_docs = len(self.vector_store.similarity_search("", k=1))
                logger.info(f"🔍 Total documents in vector store: {total_docs}")
            except:
                logger.info("🔍 Total documents in vector store: Unknown")
            
            # OPTIMIZATION 0: Smart direct lookup for common queries
            logger.info(f"🔍 DIRECT LOOKUP: Attempting direct lookup for query: '{normalized_query}'")
            direct_results = self._smart_direct_lookup(normalized_query)
            logger.info(f"🔍 DIRECT LOOKUP: Direct lookup returned {len(direct_results)} results")
            if direct_results:
                logger.info(f"🔍 DIRECT LOOKUP: Found {len(direct_results)} documents via direct lookup")
                self._cache_search_result(cache_key, direct_results)
                logger.info(f"🔍 Direct lookup completed in {time.time() - start_time:.2f}s")
                return direct_results
            else:
                logger.info(f"🔍 DIRECT LOOKUP: No direct lookup results, proceeding to object-specific search")
            
            # Extract target objects from normalized query (case-insensitive)
            query_lower = normalized_query.lower()
            target_objects = []
            
            # Enhanced object detection with better patterns
            import re
            # Look for object names in quotes, after "for the", or standalone
            object_patterns = [
                r'"([^"]+)"',  # Objects in quotes
                r'for the (\w+) object',  # "for the Account object"
                r'the (\w+) object',  # "the Contact object"
                r'(\w+) object',  # "Account object"
                r'(\w+) records?',  # "Lead records"
                r'(\w+) data',  # "Account data"
                r'in our (\w+)',  # "in our contacts"
                r'of our (\w+)',  # "of our accounts"
                r'for (\w+)',  # "for contacts"
                r'about (\w+)',  # "about leads"
                r'in (\w+)',  # "in Contact"
                r'on (\w+)',  # "on Account" - FIXED!
                r'(\w+) have',  # "Contact have"
                r'(\w+) fields',  # "Contact fields"
                r'(\w+) object',  # "contact object" (redundant but explicit)
                r'contact',  # Direct match for "contact"
            ]
            
            for pattern in object_patterns:
                matches = re.findall(pattern, query_lower)
                target_objects.extend(matches)
            
            # Remove duplicates and filter out common words
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'what', 'how', 'when', 'where', 'why', 'which', 'who', 'whom', 'whose', 'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall', 'our'}
            target_objects = list(set([obj for obj in target_objects if obj.lower() not in common_words and len(obj) > 2]))
            
            # Convert common plural Salesforce object names to singular
            plural_to_singular = {
                'contacts': 'contact',
                'accounts': 'account', 
                'leads': 'lead',
                'opportunities': 'opportunity',
                'cases': 'case',
                'users': 'user',
                'profiles': 'profile',
                'roles': 'role',
                'permissions': 'permission',
                'validation': 'validation',
                'workflows': 'workflow',
                'triggers': 'trigger',
                'fields': 'field',
                'objects': 'object'
            }
            
            # Apply plural-to-singular conversion
            normalized_objects = []
            for obj in target_objects:
                obj_lower = obj.lower()
                if obj_lower in plural_to_singular:
                    normalized_objects.append(plural_to_singular[obj_lower])
                    logger.info(f"🔍 Converted '{obj}' to '{plural_to_singular[obj_lower]}'")
                else:
                    normalized_objects.append(obj)
            
            target_objects = normalized_objects
            
            if target_objects:
                logger.info(f"🔍 OBJECT-SPECIFIC SEARCH: Looking for target objects: {target_objects}")
            
            # OPTIMIZATION 1: Security-related query detection with better patterns
            security_keywords = [
                'security', 'permission', 'profile', 'crud', 'create', 'read', 'edit', 'delete', 'access',
                'field-level', 'object-level', 'sharing', 'role', 'user access', 'data access'
            ]
            
            is_security_query = any(keyword in query_lower for keyword in security_keywords)
            
            if is_security_query:
                logger.info("🔍 Security-related query detected - using enhanced search strategy")
                
                # OPTIMIZATION 2: Use more efficient search for security queries
                # First, try to find object-specific security documents
                if target_objects:
                    # Search for exact security documents first
                    security_results = []
                    
                    # Use a more targeted search approach
                    for target_obj in target_objects:
                        # Try multiple search strategies for the security document
                        search_queries = [
                            f"security_{target_obj}",
                            f"security permissions {target_obj}",
                            f"{target_obj} field-level security",
                            f"{target_obj} System Administrator profile"
                        ]
                        
                        for security_query in search_queries:
                            try:
                                obj_security_docs = self.vector_store.similarity_search(security_query, k=config.SEARCH_BATCH_SIZE)
                                for doc in obj_security_docs:
                                    doc_type = doc.metadata.get('type', '')
                                    doc_id = doc.metadata.get('id', '')
                                    object_name = doc.metadata.get('object_name', '')
                                    
                                    # Check if this is a security document for our target object
                                    if (doc_type == 'security_permissions' and 
                                        (object_name.lower() == target_obj.lower() or 
                                         doc_id == f"security_{target_obj}")):
                                        security_results.append(doc)
                                        logger.info(f"🔍 FOUND {target_obj.upper()} SECURITY DOC: ID={doc_id}, Object={object_name}")
                                        break  # Found the document, no need to continue searching
                                        
                                # If we found the security document, break out of the search queries loop
                                if any(doc.metadata.get('id', '') == f"security_{target_obj}" for doc in security_results):
                                    break
                                    
                            except Exception as e:
                                logger.warning(f"Error searching for {target_obj} security with query '{security_query}': {e}")
                    
                    # If we found object-specific security docs, return them
                    if security_results:
                        logger.info(f"🔍 Found {len(security_results)} object-specific security documents")
                        results = security_results[:top_k]
                        self._cache_search_result(cache_key, results)
                        logger.info(f"🔍 Security search completed in {time.time() - start_time:.2f}s")
                        return results
                
                # OPTIMIZATION 3: Try direct document fetch for specific security documents
                if target_objects:
                    logger.info("🔍 Attempting direct document fetch for security documents")
                    for target_obj in target_objects:
                        # Try both lowercase and capitalized versions
                        security_doc_ids = [
                            f"security_{target_obj}",
                            f"security_{target_obj.capitalize()}"
                        ]
                        for security_doc_id in security_doc_ids:
                            logger.info(f"🔍 Trying to fetch document: {security_doc_id}")
                            try:
                                # Try to fetch the document directly by ID using Pinecone API
                                doc = self._fetch_document_by_id(security_doc_id)
                                if doc:
                                    logger.info(f"🔍 FOUND DIRECT SECURITY DOC: {security_doc_id}")
                                    security_results.append(doc)
                                    break  # Found the document, no need to try other variations
                                else:
                                    logger.info(f"🔍 Direct fetch returned None for: {security_doc_id}")
                            except Exception as e:
                                logger.warning(f"Direct fetch failed for {security_doc_id}: {e}")
                    
                    # If we found direct security docs, return them
                    if security_results:
                        logger.info(f"🔍 Found {len(security_results)} direct security documents")
                        results = security_results[:top_k]
                        self._cache_search_result(cache_key, results)
                        logger.info(f"🔍 Direct security search completed in {time.time() - start_time:.2f}s")
                        return results

                # OPTIMIZATION 4: Fallback to general security search with better filtering
                logger.info("🔍 Performing general security search")
                
                # Use a more efficient search strategy
                security_query = "security permissions field-level object-level access control"
                all_results = self.vector_store.similarity_search(security_query, k=min(config.MAX_SEARCH_RESULTS, top_k * 50))
                
                # Enhanced filtering with better categorization
                object_security_docs = []
                other_security_docs = []
                
                for doc in all_results:
                    doc_type = doc.metadata.get('type', '')
                    doc_id = doc.metadata.get('id', '')
                    object_name = doc.metadata.get('object_name', '')
                    
                    # PRIORITY 1: Object-specific security documents
                    if doc_type == 'security_permissions' and target_objects:
                        for target_obj in target_objects:
                            if (object_name.lower() == target_obj.lower() or 
                                doc_id == f"security_{target_obj}"):
                                object_security_docs.append(doc)
                                logger.info(f"🔍 PRIORITY: Added {object_name} security doc: {doc_id}")
                                break
                        continue
                    
                    # PRIORITY 2: Other security permissions
                    if doc_type == 'security_permissions':
                        other_security_docs.append(doc)
                        logger.info(f"🔍 Added security doc: {doc_id} (Object: {object_name})")
                        continue
                    
                    # PRIORITY 3: Security-related content
                    content = getattr(doc, 'page_content', '') or getattr(doc, 'text', '') or str(doc)
                    content_lower = content.lower()
                    
                    if any(term in content_lower for term in ['security', 'permission', 'profile', 'crud', 'create', 'read', 'edit', 'delete', 'access']):
                        other_security_docs.append(doc)
                        logger.info(f"🔍 Added security content doc: {doc_id} (Object: {object_name})")
                
                # Combine results with priority
                security_results = object_security_docs + other_security_docs
                logger.info(f"🔍 Combined {len(object_security_docs)} object-specific security docs + {len(other_security_docs)} other security docs = {len(security_results)} total")
                
                if security_results:
                    logger.info(f"🔍 Retrieved {len(security_results)} security-related documents")
                    
                    # Log summary instead of full details for performance
                    doc_types = {}
                    for doc in security_results[:top_k]:
                        doc_type = doc.metadata.get('type', 'unknown')
                        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                    
                    logger.info(f"🔍 Document types found: {doc_types}")
                    results = security_results[:top_k]
                    self._cache_search_result(cache_key, results)
                    logger.info(f"🔍 Security search completed in {time.time() - start_time:.2f}s")
                    return results
                else:
                    logger.warning("🔍 No security-related documents found!")
            
            # OPTIMIZATION 4: Object-specific search with better efficiency
            if target_objects:
                logger.info(f"🔍 OBJECT-SPECIFIC SEARCH: Looking for target objects: {target_objects}")
                
                # Use a more efficient search strategy
                exact_matches = []
                partial_matches = []
                
                # Search for each target object specifically
                for target_obj in target_objects:
                    try:
                        # Search for this specific object with multiple query variations
                        search_queries = [
                            f"{target_obj} object fields relationships",
                            f"{target_obj} fields metadata",
                            f"Object: {target_obj}",
                            f"salesforce_object_{target_obj}",
                            target_obj
                        ]
                        
                        all_obj_results = []
                        for query in search_queries:
                            logger.info(f"🔍 OBJECT-SPECIFIC: Searching with query: '{query}'")
                            try:
                                query_results = self.vector_store.similarity_search(query, k=config.SEARCH_BATCH_SIZE)
                                logger.info(f"🔍 OBJECT-SPECIFIC: Found {len(query_results)} results for query '{query}'")
                                all_obj_results.extend(query_results)
                            except Exception as e:
                                logger.warning(f"Error with query '{query}': {e}")
                        
                        # Remove duplicates based on document ID
                        seen_ids = set()
                        obj_results = []
                        for doc in all_obj_results:
                            doc_id = doc.metadata.get('id', 'unknown')
                            if doc_id not in seen_ids:
                                seen_ids.add(doc_id)
                                obj_results.append(doc)
                        
                        logger.info(f"🔍 OBJECT-SPECIFIC: Total unique results after deduplication: {len(obj_results)}")
                        
                        # Log all results for debugging
                        for i, doc in enumerate(obj_results[:5]):  # Log first 5 docs
                            doc_id = doc.metadata.get('id', 'unknown')
                            object_name = doc.metadata.get('object_name', 'unknown')
                            doc_type = doc.metadata.get('type', 'unknown')
                            logger.info(f"🔍 OBJECT-SPECIFIC: Result {i+1}: ID={doc_id}, Object={object_name}, Type={doc_type}")
                        
                        for doc in obj_results:
                            object_name = doc.metadata.get('object_name', '')
                            doc_id = doc.metadata.get('id', '')
                            
                            # PRIORITY 1: Exact object name matches
                            if object_name.lower() == target_obj.lower():
                                exact_matches.append(doc)
                                logger.info(f"🔍 OBJECT-SPECIFIC: Found EXACT target object: {object_name} (ID: {doc_id})")
                            # PRIORITY 2: Exact document ID matches (case-insensitive)
                            elif (doc_id == f"security_{target_obj}" or 
                                  doc_id == f"security_{target_obj.capitalize()}" or
                                  doc_id == f"salesforce_object_{target_obj}" or
                                  doc_id == f"salesforce_object_{target_obj.capitalize()}" or
                                  doc_id == f"salesforce_object_{target_obj.title()}"):
                                exact_matches.append(doc)
                                logger.info(f"🔍 OBJECT-SPECIFIC: Found EXACT target object by ID: {doc_id}")
                            # PRIORITY 3: Document ID contains the object name
                            elif target_obj.lower() in doc_id.lower():
                                exact_matches.append(doc)
                                logger.info(f"🔍 OBJECT-SPECIFIC: Found target object in ID: {doc_id}")
                            # PRIORITY 4: Partial matches (only if no exact matches found)
                            elif target_obj.lower() in object_name.lower():
                                partial_matches.append(doc)
                                logger.info(f"🔍 OBJECT-SPECIFIC: Found PARTIAL target object: {object_name} (ID: {doc_id})")
                    except Exception as e:
                        logger.warning(f"Error searching for {target_obj}: {e}")
                
                # Return exact matches first, then partial matches
                results = exact_matches + partial_matches
                if len(results) > top_k:
                    results = results[:top_k]
                
                # Check if we found the specific target objects we were looking for
                found_target_objects = set()
                for doc in results:
                    object_name = doc.metadata.get('object_name', '').lower()
                    doc_id = doc.metadata.get('id', '').lower()
                    for target_obj in target_objects:
                        if (object_name == target_obj.lower() or 
                            target_obj.lower() in doc_id):
                            found_target_objects.add(target_obj.lower())
                
                if results and len(found_target_objects) == len(target_objects):
                    # Found all target objects
                    logger.info(f"🔍 OBJECT-SPECIFIC: Retrieved {len(results)} target objects")
                    # Log the actual documents found for debugging
                    for i, doc in enumerate(results[:3]):  # Log first 3 docs
                        doc_id = doc.metadata.get('id', 'unknown')
                        object_name = doc.metadata.get('object_name', 'unknown')
                        logger.info(f"🔍 OBJECT-SPECIFIC: Doc {i+1}: ID={doc_id}, Object={object_name}")
                    self._cache_search_result(cache_key, results)
                    logger.info(f"🔍 Object-specific search completed in {time.time() - start_time:.2f}s")
                    return results
                elif results:
                    # Found some results but not all target objects
                    missing_objects = [obj for obj in target_objects if obj.lower() not in found_target_objects]
                    logger.warning(f"🔍 OBJECT-SPECIFIC: Found {len(results)} results but missing target objects: {missing_objects}")
                else:
                    logger.warning(f"🔍 OBJECT-SPECIFIC: No results found for target objects: {target_objects}")
                
                # If we didn't find all target objects, try direct fetch fallback
                if len(found_target_objects) < len(target_objects):
                    missing_objects = [obj for obj in target_objects if obj.lower() not in found_target_objects]
                    logger.warning(f"🔍 OBJECT-SPECIFIC: Missing target objects: {missing_objects}")
                    
                    # OPTIMIZATION: Try direct fetch for missing target objects as fallback
                    logger.info("🔍 OBJECT-SPECIFIC: Trying direct fetch fallback for missing target objects")
                    for target_obj in missing_objects:
                        try:
                            # Try different case variations for the document ID
                            possible_ids = [
                                f"salesforce_object_{target_obj}",
                                f"salesforce_object_{target_obj.capitalize()}",
                                f"salesforce_object_{target_obj.title()}",
                                f"security_{target_obj}",
                                f"security_{target_obj.capitalize()}"
                            ]
                            
                            for doc_id in possible_ids:
                                doc = self._fetch_document_by_id(doc_id)
                                if doc:
                                    logger.info(f"🔍 OBJECT-SPECIFIC: Found document via direct fetch: {doc_id}")
                                    results.append(doc)
                                    break  # Found the document, no need to try other IDs
                        except Exception as e:
                            logger.warning(f"Direct fetch failed for {target_obj}: {e}")
                    
                    if results:
                        logger.info(f"🔍 OBJECT-SPECIFIC: Retrieved {len(results)} target objects via direct fetch")
                        self._cache_search_result(cache_key, results)
                        logger.info(f"🔍 Object-specific search completed in {time.time() - start_time:.2f}s")
                        return results
                    
                    # Try a broader search as fallback
                    logger.info("🔍 Trying broader search for object information...")
                    for target_obj in target_objects:
                        try:
                            broader_query = f"{target_obj} fields relationships metadata"
                            broader_results = self.vector_store.similarity_search(broader_query, k=5)
                            if broader_results:
                                logger.info(f"🔍 BROADER SEARCH: Found {len(broader_results)} results for '{target_obj}'")
                                for doc in broader_results[:2]:
                                    doc_id = doc.metadata.get('id', 'unknown')
                                    object_name = doc.metadata.get('object_name', 'unknown')
                                    logger.info(f"🔍 BROADER SEARCH: Doc: ID={doc_id}, Object={object_name}")
                                results = broader_results[:top_k]
                                self._cache_search_result(cache_key, results)
                                logger.info(f"🔍 Broader search completed in {time.time() - start_time:.2f}s")
                                return results
                        except Exception as e:
                            logger.warning(f"Error in broader search for {target_obj}: {e}")
                    
                    # SPECIAL FALLBACK: Try to find Contact object specifically
                    # Check if Contact was requested but not found in broader search
                    contact_requested = 'contact' in [obj.lower() for obj in target_objects]
                    contact_found_in_broader = any(
                        doc.metadata.get('id') == 'salesforce_object_Contact' or 
                        doc.metadata.get('object_name', '').lower() == 'contact'
                        for doc in results
                    ) if 'results' in locals() else False
                    
                    if contact_requested and not contact_found_in_broader:
                        logger.info("🔍 SPECIAL FALLBACK: Looking for Contact object specifically...")
                        try:
                            # Search for Contact object with multiple specific queries
                            contact_queries = [
                                "salesforce_object_Contact",
                                "Object: Contact",
                                "Contact object fields",
                                "Contact fields metadata"
                            ]
                            
                            contact_results = []
                            for contact_query in contact_queries:
                                try:
                                    query_results = self.vector_store.similarity_search(contact_query, k=10)
                                    for doc in query_results:
                                        doc_id = doc.metadata.get('id', 'unknown')
                                        if doc_id == 'salesforce_object_Contact':
                                            contact_results.append(doc)
                                            logger.info(f"🔍 SPECIAL FALLBACK: Found Contact object! ID={doc_id}")
                                            break
                                    if contact_results:
                                        break
                                except Exception as e:
                                    logger.warning(f"Error with contact query '{contact_query}': {e}")
                            
                            if contact_results:
                                logger.info(f"🔍 SPECIAL FALLBACK: Retrieved Contact object")
                                self._cache_search_result(cache_key, contact_results)
                                logger.info(f"🔍 Special fallback completed in {time.time() - start_time:.2f}s")
                                return contact_results
                            else:
                                # ULTIMATE FALLBACK: Try direct fetch from Pinecone
                                logger.info("🔍 ULTIMATE FALLBACK: Trying direct fetch for Contact object...")
                                try:
                                    from pinecone import Pinecone
                                    import os
                                    from dotenv import load_dotenv
                                    load_dotenv()
                                    
                                    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
                                    index_name = os.getenv('PINECONE_INDEX_NAME', 'salesforce-schema')
                                    index = pc.Index(index_name)
                                    
                                    # Fetch Contact document directly
                                    contact_fetch = index.fetch(ids=['salesforce_object_Contact'])
                                    if 'salesforce_object_Contact' in contact_fetch.vectors:
                                        contact_vector = contact_fetch.vectors['salesforce_object_Contact']
                                        
                                        # Convert to LangChain document format
                                        from langchain.schema import Document
                                        contact_doc = Document(
                                            page_content=contact_vector.metadata.get('content', ''),
                                            metadata=contact_vector.metadata
                                        )
                                        
                                        logger.info("🔍 ULTIMATE FALLBACK: Successfully fetched Contact object directly!")
                                        self._cache_search_result(cache_key, [contact_doc])
                                        logger.info(f"🔍 Ultimate fallback completed in {time.time() - start_time:.2f}s")
                                        return [contact_doc]
                                    else:
                                        logger.warning("🔍 ULTIMATE FALLBACK: Contact object not found in direct fetch")
                                except Exception as fetch_error:
                                    logger.warning(f"Error in ultimate fallback for Contact: {fetch_error}")
                        except Exception as e:
                            logger.warning(f"Error in special fallback for Contact: {e}")
            else:
                logger.info("🔍 No target objects detected in query")
            
            # OPTIMIZATION 5: Fallback to similarity search with better parameters
            logger.info("🔍 Using fallback similarity search")
            results = self.vector_store.similarity_search(normalized_query, k=top_k)
            logger.info(f"🔍 Fallback search found {len(results)} documents")
            
            self._cache_search_result(cache_key, results)
            logger.info(f"🔍 Fallback search completed in {time.time() - start_time:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"Error searching context: {e}")
            return []
    
    def format_context(self, documents: List[Document]) -> str:
        """Format retrieved documents into context string"""
        if not documents:
            return "No relevant context found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            # Extract metadata and content
            metadata = doc.metadata
            # Try different content fields - LangChain Pinecone uses page_content, but our data has text
            content = getattr(doc, 'page_content', None) or getattr(doc, 'text', None) or str(doc)
            
            # Format the document
            doc_info = f"Document {i}:\n"
            if metadata.get('object_name'):
                doc_info += f"Object: {metadata['object_name']}\n"
            if metadata.get('field_name'):
                doc_info += f"Field: {metadata['field_name']}\n"
            if metadata.get('type'):
                doc_info += f"Type: {metadata['type']}\n"
            
            doc_info += f"Content: {content}\n"
            doc_info += "-" * 50 + "\n"
            context_parts.append(doc_info)
        
        return "\n".join(context_parts)
    
    def generate_response(self, query: str, context: str) -> str:
        """Generate thorough response using the LLM with context"""
        if not self.llm:
            return "Error: No LLM provider configured."
        
        try:
            # Create the prompt template with emphasis on thoroughness
            human_prompt = f"""Based on the following context from your Salesforce org, please provide a THOROUGH and COMPREHENSIVE answer to the user's question.

IMPORTANT: Provide a complete, detailed response. Do not truncate or summarize unless specifically asked. Include all relevant details, specific field names, object relationships, and actionable insights.

Context:
{context}

User Question: {query}

Please provide a thorough, comprehensive response that includes:
- All relevant details from the context
- Specific field names, object names, and relationships
- Technical explanations where appropriate
- Best practices and recommendations
- Any missing information that would be helpful
- Clear structure with headers and organized sections

Remember: The user values completeness over brevity. Provide a thorough answer that leaves no important details out."""

            prompt_template = ChatPromptTemplate.from_messages([
                ("system", config.SYSTEM_PROMPT),
                ("human", human_prompt)
            ])
            
            # Create the chain
            chain = (
                {"context": lambda x: x["context"], "query": lambda x: x["query"]}
                | prompt_template
                | self.llm
                | StrOutputParser()
            )
            
            # Generate response
            response = chain.invoke({
                "context": context,
                "query": query
            })
            
            logger.info(f"Generated thorough response with {len(response)} characters")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def query(self, user_query: str) -> Dict[str, Any]:
        """Main method to process a user query"""
        try:
            # Normalize profile names in the query
            normalized_query = self._normalize_profile_names(user_query)
            
            # Search for relevant context
            documents = self.search_context(user_query)
            context = self.format_context(documents)
            
            # Generate response using the original query for user-facing response
            response = self.generate_response(user_query, context)
            
            return {
                "response": response,
                "context_documents": len(documents),
                "context": context,
                "query": user_query,
                "normalized_query": normalized_query
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": f"Error processing your request: {str(e)}",
                "context_documents": 0,
                "context": "",
                "query": user_query
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the RAG service"""
        cache_stats = {
            "cache_enabled": config.ENABLE_SEARCH_CACHING,
            "cache_size": len(self._search_cache),
            "cache_ttl_seconds": config.CACHE_TTL_SECONDS,
            "search_batch_size": config.SEARCH_BATCH_SIZE,
            "max_search_results": config.MAX_SEARCH_RESULTS
        }
        
        return {
            "pinecone_connected": self.vector_store is not None,
            "llm_provider": list(self.available_providers.keys())[0] if self.available_providers else None,
            "available_providers": list(self.available_providers.keys()),
            "index_name": config.PINECONE_INDEX_NAME,
            "performance": cache_stats
        }
    
    def clear_cache(self):
        """Clear the search cache"""
        self._search_cache.clear()
        self._cache_timestamps.clear()
        logger.info("🔍 Search cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        valid_cache_entries = 0
        expired_cache_entries = 0
        
        for cache_key, timestamp in self._cache_timestamps.items():
            if current_time - timestamp < config.CACHE_TTL_SECONDS:
                valid_cache_entries += 1
            else:
                expired_cache_entries += 1
        
        return {
            "total_cache_entries": len(self._search_cache),
            "valid_cache_entries": valid_cache_entries,
            "expired_cache_entries": expired_cache_entries,
            "cache_hit_rate": "N/A"  # Would need to track hits/misses over time
        }
