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
        self._initialize_pinecone()
        self._initialize_llm()
    
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
    
    def search_context(self, query: str, top_k: int = None) -> List[Document]:
        """Search for relevant context in Pinecone with enhanced retrieval for thorough responses"""
        if not self.vector_store:
            return []
        
        try:
            # Use higher top_k for more comprehensive context
            top_k = top_k or config.TOP_K  # Now defaults to 10 instead of 5
            
            # Simple direct approach: Get all documents and filter by object name
            all_results = self.vector_store.similarity_search("", k=1000)  # Get all results
            
            # Filter for specific objects mentioned in query
            target_objects = []
            query_lower = query.lower()
            
            if 'account' in query_lower:
                target_objects.append('account')
            if 'contact' in query_lower:
                target_objects.append('contact')
            if 'lead' in query_lower:
                target_objects.append('lead')
            if 'opportunity' in query_lower:
                target_objects.append('opportunity')
            if 'case' in query_lower:
                target_objects.append('case')
            
            # If specific objects are mentioned, prioritize them
            if target_objects:
                results = []
                for doc in all_results:
                    object_name = doc.metadata.get('object_name', '').lower()
                    if object_name in target_objects:
                        results.append(doc)
                        if len(results) >= top_k:
                            break
                
                # If we found target objects, return them
                if results:
                    logger.info(f"Retrieved {len(results)} target objects: {[doc.metadata.get('object_name', 'Unknown') for doc in results]}")
                    return results
            
            # Fallback to similarity search
            results = self.vector_store.similarity_search(query, k=top_k)
            logger.info(f"Retrieved {len(results)} documents via similarity search: {[doc.metadata.get('object_name', 'Unknown') for doc in results]}")
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
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", config.SYSTEM_PROMPT),
                ("human", """Based on the following context from your Salesforce org, please provide a THOROUGH and COMPREHENSIVE answer to the user's question.

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

Remember: The user values completeness over brevity. Provide a thorough answer that leaves no important details out.""")
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
        return {
            "pinecone_connected": self.vector_store is not None,
            "llm_provider": list(self.available_providers.keys())[0] if self.available_providers else None,
            "available_providers": list(self.available_providers.keys()),
            "index_name": config.PINECONE_INDEX_NAME
        }
