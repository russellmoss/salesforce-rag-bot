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
        cache_string = f"{query.lower().strip()}:{top_k}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
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
            
            # Check cache first
            cache_key = self._get_cache_key(query, top_k)
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
            
            # Extract target objects from query (case-insensitive)
            query_lower = query.lower()
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
            ]
            
            for pattern in object_patterns:
                matches = re.findall(pattern, query_lower)
                target_objects.extend(matches)
            
            # Remove duplicates and filter out common words
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'what', 'how', 'when', 'where', 'why', 'which', 'who', 'whom', 'whose', 'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'}
            target_objects = list(set([obj for obj in target_objects if obj.lower() not in common_words and len(obj) > 2]))
            
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
                        # Search for security documents for this specific object
                        security_query = f"security permissions {target_obj}"
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
                                    logger.info(f"🔍 FOUND {target_obj.upper()} DOC: ID={doc_id}, Object={object_name}")
                        except Exception as e:
                            logger.warning(f"Error searching for {target_obj} security: {e}")
                    
                    # If we found object-specific security docs, return them
                    if security_results:
                        logger.info(f"🔍 Found {len(security_results)} object-specific security documents")
                        results = security_results[:top_k]
                        self._cache_search_result(cache_key, results)
                        logger.info(f"🔍 Security search completed in {time.time() - start_time:.2f}s")
                        return results
                
                # OPTIMIZATION 3: Fallback to general security search with better filtering
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
                        # Search for this specific object
                        obj_query = f"{target_obj} object fields relationships"
                        obj_results = self.vector_store.similarity_search(obj_query, k=config.SEARCH_BATCH_SIZE)
                        
                        for doc in obj_results:
                            object_name = doc.metadata.get('object_name', '')
                            doc_id = doc.metadata.get('id', '')
                            
                            # PRIORITY 1: Exact object name matches
                            if object_name.lower() == target_obj.lower():
                                exact_matches.append(doc)
                                logger.info(f"🔍 OBJECT-SPECIFIC: Found EXACT target object: {object_name} (ID: {doc_id})")
                            # PRIORITY 2: Exact document ID matches
                            elif (doc_id == f"security_{target_obj}" or 
                                  doc_id == f"salesforce_object_{target_obj}"):
                                exact_matches.append(doc)
                                logger.info(f"🔍 OBJECT-SPECIFIC: Found EXACT target object by ID: {doc_id}")
                            # PRIORITY 3: Partial matches (only if no exact matches found)
                            elif target_obj.lower() in object_name.lower():
                                partial_matches.append(doc)
                                logger.info(f"🔍 OBJECT-SPECIFIC: Found PARTIAL target object: {object_name} (ID: {doc_id})")
                    except Exception as e:
                        logger.warning(f"Error searching for {target_obj}: {e}")
                
                # Return exact matches first, then partial matches
                results = exact_matches + partial_matches
                if len(results) > top_k:
                    results = results[:top_k]
                
                if results:
                    logger.info(f"🔍 OBJECT-SPECIFIC: Retrieved {len(results)} target objects")
                    self._cache_search_result(cache_key, results)
                    logger.info(f"🔍 Object-specific search completed in {time.time() - start_time:.2f}s")
                    return results
                else:
                    logger.warning(f"🔍 OBJECT-SPECIFIC: No target objects found for: {target_objects}")
            else:
                logger.info("🔍 No target objects detected in query")
            
            # OPTIMIZATION 5: Fallback to similarity search with better parameters
            logger.info("🔍 Using fallback similarity search")
            results = self.vector_store.similarity_search(query, k=top_k)
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
            # Search for relevant context
            documents = self.search_context(user_query)
            context = self.format_context(documents)
            
            # Generate response
            response = self.generate_response(user_query, context)
            
            return {
                "response": response,
                "context_documents": len(documents),
                "context": context,
                "query": user_query
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
