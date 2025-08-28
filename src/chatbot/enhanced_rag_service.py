#!/usr/bin/env python3
"""
Enhanced RAG Service with Hierarchical Vector DB Organization
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import time
from functools import lru_cache

# LangChain imports
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# Pinecone imports
import pinecone
from pinecone import Pinecone

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Document types for better organization"""
    SALESFORCE_OBJECT = "salesforce_object"
    SECURITY_PERMISSIONS = "security_permissions"
    AUTOMATION = "automation"
    FIELD_METADATA = "field_metadata"
    RELATIONSHIP = "relationship"
    CUSTOM_OBJECT = "custom_object"
    STANDARD_OBJECT = "standard_object"

class SearchStrategy(Enum):
    """Search strategies for different query types"""
    OBJECT_SPECIFIC = "object_specific"
    FIELD_SPECIFIC = "field_specific"
    SECURITY_SPECIFIC = "security_specific"
    AUTOMATION_SPECIFIC = "automation_specific"
    RELATIONSHIP_SPECIFIC = "relationship_specific"
    BROAD_SEARCH = "broad_search"

@dataclass
class SearchContext:
    """Context for search operations"""
    query: str
    target_objects: List[str]
    target_fields: List[str]
    document_types: List[DocumentType]
    search_strategy: SearchStrategy
    max_results: int = 10

class EnhancedRAGService:
    """
    Enhanced RAG Service with hierarchical search and better organization
    """
    
    def __init__(self):
        self.vector_store = None
        self.llm = None
        self.pinecone_client = None
        self.index = None
        self.available_providers = config.validate_config()
        self._search_cache = {}
        self._cache_timestamps = {}
        self._object_index = {}  # Cache for object metadata
        self._field_index = {}   # Cache for field metadata
        
        self._initialize_pinecone()
        self._initialize_llm()
        self._build_metadata_indexes()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone connection"""
        try:
            self.pinecone_client = Pinecone(api_key=config.PINECONE_API_KEY)
            self.index = self.pinecone_client.Index(config.PINECONE_INDEX_NAME)
            
            # Initialize LangChain vector store
            embedding_function = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=config.OPENAI_API_KEY
            )
            
            self.vector_store = PineconeVectorStore(
                index_name=config.PINECONE_INDEX_NAME,
                embedding=embedding_function
            )
            
            logger.info(f"Connected to Pinecone index: {config.PINECONE_INDEX_NAME}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    
    def _initialize_llm(self):
        """Initialize LLM with available providers"""
        if config.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=config.OPENAI_MODEL,
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
                openai_api_key=config.OPENAI_API_KEY
            )
            logger.info(f"Using OpenAI model: {config.OPENAI_MODEL}")
        elif config.ANTHROPIC_API_KEY:
            self.llm = ChatAnthropic(
                model=config.ANTHROPIC_MODEL,
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
                anthropic_api_key=config.ANTHROPIC_API_KEY
            )
            logger.info(f"Using Anthropic model: {config.ANTHROPIC_MODEL}")
        elif config.GOOGLE_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model=config.GOOGLE_MODEL,
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
                google_api_key=config.GOOGLE_API_KEY
            )
            logger.info(f"Using Google model: {config.GOOGLE_MODEL}")
        else:
            raise ValueError("No LLM provider configured")
    
    def _build_metadata_indexes(self):
        """Build in-memory indexes for fast object and field lookups"""
        try:
            logger.info("Building metadata indexes...")
            
            # Get all documents to build indexes
            all_docs = self.vector_store.similarity_search("", k=1000)
            
            for doc in all_docs:
                metadata = doc.metadata
                doc_id = metadata.get('id', '')
                object_name = metadata.get('object_name', '')
                doc_type = metadata.get('type', '')
                
                # Build object index
                if object_name and doc_type == 'salesforce_object':
                    self._object_index[object_name.lower()] = {
                        'id': doc_id,
                        'name': object_name,
                        'type': doc_type,
                        'fields_count': metadata.get('fields_count', 0),
                        'record_count': metadata.get('record_count', 0)
                    }
                
                # Build field index (if we have field-specific documents)
                if 'field_name' in metadata:
                    field_name = metadata['field_name']
                    if object_name not in self._field_index:
                        self._field_index[object_name] = {}
                    self._field_index[object_name][field_name] = {
                        'id': doc_id,
                        'field_name': field_name,
                        'object_name': object_name,
                        'type': doc_type
                    }
            
            logger.info(f"Built indexes: {len(self._object_index)} objects, {len(self._field_index)} objects with fields")
            
        except Exception as e:
            logger.warning(f"Failed to build metadata indexes: {e}")
    
    def _analyze_query(self, query: str) -> SearchContext:
        """Analyze query to determine search strategy and targets"""
        query_lower = query.lower()
        
        # Extract target objects
        target_objects = []
        for obj_name in self._object_index.keys():
            if obj_name in query_lower:
                target_objects.append(obj_name)
        
        # Extract target fields
        target_fields = []
        for obj_name, fields in self._field_index.items():
            for field_name in fields.keys():
                if field_name.lower() in query_lower:
                    target_fields.append(field_name)
        
        # Determine document types
        document_types = []
        if any(keyword in query_lower for keyword in ['field', 'fields', 'column', 'attribute']):
            document_types.append(DocumentType.FIELD_METADATA)
        if any(keyword in query_lower for keyword in ['security', 'permission', 'access', 'crud']):
            document_types.append(DocumentType.SECURITY_PERMISSIONS)
        if any(keyword in query_lower for keyword in ['automation', 'flow', 'workflow', 'trigger']):
            document_types.append(DocumentType.AUTOMATION)
        if any(keyword in query_lower for keyword in ['relationship', 'lookup', 'master-detail']):
            document_types.append(DocumentType.RELATIONSHIP)
        
        # If no specific types detected, default to object search
        if not document_types:
            document_types = [DocumentType.SALESFORCE_OBJECT]
        
        # Special case: If asking about object fields, prioritize object search
        if (target_objects and 
            any(keyword in query_lower for keyword in ['field', 'fields']) and
            any(keyword in query_lower for keyword in ['object', 'in my', 'are in'])):
            document_types = [DocumentType.SALESFORCE_OBJECT]
        
        # Determine search strategy
        if target_objects and document_types:
            if DocumentType.SECURITY_PERMISSIONS in document_types:
                search_strategy = SearchStrategy.SECURITY_SPECIFIC
            elif DocumentType.AUTOMATION in document_types:
                search_strategy = SearchStrategy.AUTOMATION_SPECIFIC
            elif DocumentType.FIELD_METADATA in document_types:
                search_strategy = SearchStrategy.FIELD_SPECIFIC
            else:
                search_strategy = SearchStrategy.OBJECT_SPECIFIC
        else:
            search_strategy = SearchStrategy.BROAD_SEARCH
        
        return SearchContext(
            query=query,
            target_objects=target_objects,
            target_fields=target_fields,
            document_types=document_types,
            search_strategy=search_strategy
        )
    
    def _search_by_strategy(self, context: SearchContext) -> List[Document]:
        """Search using the determined strategy"""
        logger.info(f"🔍 Using search strategy: {context.search_strategy.value}")
        
        if context.search_strategy == SearchStrategy.OBJECT_SPECIFIC:
            return self._search_object_specific(context)
        elif context.search_strategy == SearchStrategy.FIELD_SPECIFIC:
            return self._search_field_specific(context)
        elif context.search_strategy == SearchStrategy.SECURITY_SPECIFIC:
            return self._search_security_specific(context)
        elif context.search_strategy == SearchStrategy.AUTOMATION_SPECIFIC:
            return self._search_automation_specific(context)
        else:
            return self._search_broad(context)
    
    def _search_object_specific(self, context: SearchContext) -> List[Document]:
        """Search for specific objects with multiple fallback strategies"""
        results = []
        
        for target_obj in context.target_objects:
            logger.info(f"🔍 Searching for object: {target_obj}")
            
            # Strategy 1: Direct object lookup from index
            if target_obj in self._object_index:
                obj_info = self._object_index[target_obj]
                doc_id = obj_info['id']
                
                # Try to fetch directly from Pinecone
                try:
                    fetch_result = self.index.fetch(ids=[doc_id])
                    if doc_id in fetch_result.vectors:
                        vector_data = fetch_result.vectors[doc_id]
                        doc = Document(
                            page_content=vector_data.metadata.get('content', ''),
                            metadata=vector_data.metadata
                        )
                        results.append(doc)
                        logger.info(f"✅ Found {target_obj} via direct fetch")
                        continue
                except Exception as e:
                    logger.warning(f"Direct fetch failed for {target_obj}: {e}")
            
            # Strategy 2: Enhanced similarity search with object-specific queries
            object_queries = [
                f"Object: {target_obj}",
                f"salesforce_object_{target_obj}",
                f"{target_obj} object fields",
                f"{target_obj} fields metadata",
                f"{target_obj} schema definition"
            ]
            
            for query in object_queries:
                try:
                    search_results = self.vector_store.similarity_search(query, k=5)
                    for doc in search_results:
                        doc_id = doc.metadata.get('id', '')
                        object_name = doc.metadata.get('object_name', '').lower()
                        
                        if (doc_id == f"salesforce_object_{target_obj}" or 
                            object_name == target_obj.lower()):
                            results.append(doc)
                            logger.info(f"✅ Found {target_obj} via similarity search: {query}")
                            break
                    if results:
                        break
                except Exception as e:
                    logger.warning(f"Similarity search failed for {query}: {e}")
            
            # Strategy 3: Metadata filtering with broader search
            if not results:
                try:
                    # Use Pinecone's metadata filtering
                    filter_dict = {
                        "object_name": {"$eq": target_obj}
                    }
                    
                    # Create a dummy embedding for the query
                    from openai import OpenAI
                    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                    response = openai_client.embeddings.create(
                        input=[target_obj],
                        model="text-embedding-3-small"
                    )
                    query_embedding = response.data[0].embedding
                    
                    # Query with metadata filter
                    filter_results = self.index.query(
                        vector=query_embedding,
                        top_k=5,
                        filter=filter_dict,
                        include_metadata=True
                    )
                    
                    for match in filter_results.matches:
                        doc = Document(
                            page_content=match.metadata.get('content', ''),
                            metadata=match.metadata
                        )
                        results.append(doc)
                        logger.info(f"✅ Found {target_obj} via metadata filtering")
                        break
                        
                except Exception as e:
                    logger.warning(f"Metadata filtering failed for {target_obj}: {e}")
        
        return results[:context.max_results]
    
    def _search_field_specific(self, context: SearchContext) -> List[Document]:
        """Search for field-specific information"""
        results = []
        
        for target_obj in context.target_objects:
            if target_obj in self._field_index:
                for field_name in self._field_index[target_obj].keys():
                    field_info = self._field_index[target_obj][field_name]
                    doc_id = field_info['id']
                    
                    try:
                        fetch_result = self.index.fetch(ids=[doc_id])
                        if doc_id in fetch_result.vectors:
                            vector_data = fetch_result.vectors[doc_id]
                            doc = Document(
                                page_content=vector_data.metadata.get('content', ''),
                                metadata=vector_data.metadata
                            )
                            results.append(doc)
                    except Exception as e:
                        logger.warning(f"Failed to fetch field {field_name}: {e}")
        
        return results[:context.max_results]
    
    def _search_security_specific(self, context: SearchContext) -> List[Document]:
        """Search for security-specific information"""
        results = []
        
        # Search for security documents
        security_queries = [
            "security permissions",
            "field-level security",
            "object-level security",
            "sharing rules",
            "permission sets"
        ]
        
        for query in security_queries:
            try:
                search_results = self.vector_store.similarity_search(query, k=10)
                for doc in search_results:
                    if doc.metadata.get('type') == 'security_permissions':
                        results.append(doc)
            except Exception as e:
                logger.warning(f"Security search failed for {query}: {e}")
        
        return results[:context.max_results]
    
    def _search_automation_specific(self, context: SearchContext) -> List[Document]:
        """Search for automation-specific information"""
        results = []
        
        automation_queries = [
            "automation flows",
            "process builder",
            "workflow rules",
            "triggers",
            "validation rules"
        ]
        
        for query in automation_queries:
            try:
                search_results = self.vector_store.similarity_search(query, k=10)
                for doc in search_results:
                    if doc.metadata.get('type') == 'automation':
                        results.append(doc)
            except Exception as e:
                logger.warning(f"Automation search failed for {query}: {e}")
        
        return results[:context.max_results]
    
    def _search_broad(self, context: SearchContext) -> List[Document]:
        """Broad search fallback"""
        try:
            results = self.vector_store.similarity_search(context.query, k=context.max_results)
            logger.info(f"🔍 Broad search found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Broad search failed: {e}")
            return []
    
    def search_context(self, query: str, top_k: int = 10) -> List[Document]:
        """Main search method with enhanced strategy"""
        start_time = time.time()
        
        try:
            # Analyze the query
            context = self._analyze_query(query)
            logger.info(f"🔍 Query analysis: {len(context.target_objects)} objects, {len(context.target_fields)} fields, strategy: {context.search_strategy.value}")
            
            # Search using determined strategy
            results = self._search_by_strategy(context)
            
            # If no results found, try fallback strategies
            if not results:
                logger.info("🔍 No results found, trying fallback strategies...")
                
                # Fallback 1: Try broader search
                results = self._search_broad(context)
                
                # Fallback 2: Try direct object lookup for each target object
                if not results and context.target_objects:
                    for target_obj in context.target_objects:
                        if target_obj in self._object_index:
                            obj_info = self._object_index[target_obj]
                            doc_id = obj_info['id']
                            
                            try:
                                fetch_result = self.index.fetch(ids=[doc_id])
                                if doc_id in fetch_result.vectors:
                                    vector_data = fetch_result.vectors[doc_id]
                                    doc = Document(
                                        page_content=vector_data.metadata.get('content', ''),
                                        metadata=vector_data.metadata
                                    )
                                    results.append(doc)
                                    logger.info(f"✅ Fallback: Found {target_obj} via direct lookup")
                                    break
                            except Exception as e:
                                logger.warning(f"Fallback lookup failed for {target_obj}: {e}")
            
            logger.info(f"🔍 Search completed in {time.time() - start_time:.2f}s, found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in enhanced search: {e}")
            return []
    
    def format_context(self, documents: List[Document]) -> str:
        """Format retrieved documents into context string"""
        if not documents:
            return "No relevant context found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.metadata
            content = doc.page_content
            
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
        """Generate response using LLM with context"""
        try:
            prompt = ChatPromptTemplate.from_template("""
            You are a Salesforce expert AI assistant. Answer the user's question based on the provided context from their Salesforce org.

            Context from Salesforce org:
            {context}

            User Question: {query}

            Instructions:
            1. Provide a comprehensive and accurate answer based on the context
            2. If the context doesn't contain the specific information, clearly state what's missing
            3. Include relevant details like field types, relationships, and metadata
            4. Be specific about what you found in their org vs. general Salesforce knowledge
            5. If you find the information, provide it in a clear, organized way

            Answer:
            """)
            
            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({"query": query, "context": context})
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Sorry, I encountered an error while generating a response: {str(e)}"
    
    def query(self, query: str) -> Dict[str, Any]:
        """Main query method that combines search and generation"""
        try:
            # Search for relevant context
            documents = self.search_context(query)
            
            # Format context
            context = self.format_context(documents)
            
            # Generate response
            response = self.generate_response(query, context)
            
            return {
                "response": response,
                "context_documents": len(documents),
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Error in query: {e}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "context_documents": 0,
                "context": ""
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "pinecone_connected": self.vector_store is not None,
            "llm_provider": list(self.available_providers)[0] if self.available_providers else None,
            "index_name": config.PINECONE_INDEX_NAME,
            "available_providers": self.available_providers,
            "object_index_size": len(self._object_index),
            "field_index_size": sum(len(fields) for fields in self._field_index.values())
        }
