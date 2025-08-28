import streamlit as st
import time
from typing import Dict, Any
import logging
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import config
from enhanced_rag_service import EnhancedRAGService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Salesforce Schema AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .error-message {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    .context-info {
        background-color: #fff3e0;
        padding: 0.5rem;
        border-radius: 5px;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_rag_service():
    """Initialize the RAG service with caching"""
    try:
        # Check if environment variables are set (try Streamlit secrets first, then .env)
        import os
        from dotenv import load_dotenv
        
        # Try to get from Streamlit secrets first
        try:
            pinecone_key = st.secrets.get("PINECONE_API_KEY")
            openai_key = st.secrets.get("OPENAI_API_KEY")
            anthropic_key = st.secrets.get("ANTHROPIC_API_KEY")
            google_key = st.secrets.get("GOOGLE_API_KEY")
        except:
            # Fallback to .env file for local development
            load_dotenv()
            pinecone_key = os.getenv("PINECONE_API_KEY")
            openai_key = os.getenv("OPENAI_API_KEY")
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            google_key = os.getenv("GOOGLE_API_KEY")
        
        if not pinecone_key or not any([openai_key, anthropic_key, google_key]):
            return None
            
        return EnhancedRAGService()
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {str(e)}")
        return None

def display_status(rag_service: EnhancedRAGService):
    """Display the status of the RAG service"""
    status = rag_service.get_status()
    
    with st.sidebar:
        st.markdown("### 🔧 System Status")
        
        # Connection status
        if status["pinecone_connected"]:
            st.success("✅ Pinecone Connected")
        else:
            st.error("❌ Pinecone Not Connected")
        
        # LLM provider
        if status["llm_provider"]:
            st.info(f"🤖 LLM: {status['llm_provider'].title()}")
        else:
            st.error("❌ No LLM Provider")
        
        # Index name
        st.info(f"📊 Index: {status['index_name']}")
        
        # Available providers
        if status["available_providers"]:
            st.markdown("**Available Providers:**")
            for provider in status["available_providers"]:
                st.markdown(f"- {provider.title()}")

def display_chat_message(role: str, content: str, context_info: Dict[str, Any] = None):
    """Display a chat message with proper styling"""
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>Assistant:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
        
        # Display context information if available
        if context_info and context_info.get("context_documents", 0) > 0:
            st.markdown(f"""
            <div class="context-info">
                📚 Retrieved {context_info['context_documents']} relevant documents from your Salesforce org
            </div>
            """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Salesforce Schema AI Assistant</h1>
        <p>Ask questions about your Salesforce org schema, automation, security, and data!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize RAG service
    rag_service = initialize_rag_service()
    
    if not rag_service:
        st.warning("""
        ## ⚠️ Configuration Required
        
        The RAG service is not configured. This is normal if you haven't set up your API keys yet.
        
        **For Streamlit Cloud deployment:**
        1. Go to your app settings in Streamlit Cloud
        2. Click "Secrets" and add your API keys
        3. The app will automatically redeploy
        
        **For local development:**
        1. Create a `.env` file in the root directory
        2. Add your API keys (see SETUP.md for details)
        3. Restart the application
        
        **Required keys:**
        - `PINECONE_API_KEY` - For vector database access
        - At least one LLM provider key:
          - `OPENAI_API_KEY` (recommended)
          - `ANTHROPIC_API_KEY`
          - `GOOGLE_API_KEY`
        
        The chat interface will still work for testing, but responses will be limited.
        """)
        
        # Continue with limited functionality
        rag_service = None
    
    # Display status in sidebar
    if rag_service:
        display_status(rag_service)
    else:
        with st.sidebar:
            st.markdown("### 🔧 System Status")
            st.error("❌ RAG Service Not Configured")
            st.info("📋 Check SETUP.md for configuration instructions")
    
    # Sidebar with example questions
    with st.sidebar:
        st.markdown("### 💡 Example Questions")
        example_questions = [
            "What fields are available on the Account object?",
            "Show me all automation related to Contact creation",
            "What are the field-level security settings for Opportunity?",
            "Which objects have the highest data quality scores?",
            "What permission sets exist in my org?",
            "Tell me about validation rules on the Lead object",
            "What flows are triggered when a Case is created?",
            "Show me the sharing settings for Account records"
        ]
        
        for question in example_questions:
            if st.button(question, key=f"example_{hash(question)}"):
                st.session_state.user_input = question
                st.rerun()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "context_info" not in st.session_state:
        st.session_state.context_info = {}
    
    # Display chat history
    for i, message in enumerate(st.session_state.messages):
        context_info = st.session_state.context_info.get(i, {})
        display_chat_message(message["role"], message["content"], context_info)
    
    # Chat input
    user_input = st.chat_input("Ask about your Salesforce schema...")
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        display_chat_message("user", user_input)
        
        # Show typing indicator
        with st.spinner("🤖 Thinking..."):
            if rag_service:
                try:
                    # Get response from RAG service
                    result = rag_service.query(user_input)
                    
                    # Add assistant response to chat
                    st.session_state.messages.append({"role": "assistant", "content": result["response"]})
                    
                    # Store context info
                    message_index = len(st.session_state.messages) - 1
                    st.session_state.context_info[message_index] = {
                        "context_documents": result["context_documents"],
                        "context": result["context"]
                    }
                    
                    # Display assistant response
                    display_chat_message("assistant", result["response"], {
                        "context_documents": result["context_documents"]
                    })
                    
                except Exception as e:
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
                    display_chat_message("assistant", error_message)
                    logger.error(f"Error processing query: {e}")
            else:
                # Limited functionality when RAG service is not configured
                response = """
                ⚠️ **Configuration Required**
                
                I can't process your request because the RAG service is not configured.
                
                **To enable full functionality:**
                1. Create a `.env` file in the root directory
                2. Add your API keys (see SETUP.md for details)
                3. Restart the application
                
                **Required keys:**
                - `PINECONE_API_KEY` - For vector database access
                - At least one LLM provider key:
                  - `OPENAI_API_KEY` (recommended)
                  - `ANTHROPIC_API_KEY`
                  - `GOOGLE_API_KEY`
                
                Once configured, I'll be able to answer questions about your Salesforce org!
                """
                st.session_state.messages.append({"role": "assistant", "content": response})
                display_chat_message("assistant", response)
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            <p>Powered by LangChain, Pinecone, and OpenAI/Anthropic/Google AI</p>
            <p>Your Salesforce data is processed securely and privately</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Clear chat button
    if st.sidebar.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.context_info = {}
        st.rerun()

if __name__ == "__main__":
    main()
