import streamlit as st
import time
from typing import Dict, Any
import logging

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
</style>
""", unsafe_allow_html=True)

def display_chat_message(role: str, content: str):
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

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Salesforce Schema AI Assistant</h1>
        <p>Ask questions about your Salesforce org schema, automation, security, and data!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for environment variables
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check configuration
    pinecone_key = os.getenv("PINECONE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    # Display status in sidebar
    with st.sidebar:
        st.markdown("### 🔧 System Status")
        
        if pinecone_key:
            st.success("✅ Pinecone API Key Found")
        else:
            st.error("❌ Pinecone API Key Missing")
        
        if openai_key:
            st.success("✅ OpenAI API Key Found")
        elif anthropic_key:
            st.success("✅ Anthropic API Key Found")
        elif google_key:
            st.success("✅ Google API Key Found")
        else:
            st.error("❌ No LLM API Key Found")
        
        if not pinecone_key or not any([openai_key, anthropic_key, google_key]):
            st.warning("⚠️ Please configure your API keys in the .env file")
            st.markdown("""
            **Required:**
            - `PINECONE_API_KEY`
            - At least one LLM provider key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`)
            
            See `SETUP.md` for detailed instructions.
            """)
    
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
    
    # Display chat history
    for message in st.session_state.messages:
        display_chat_message(message["role"], message["content"])
    
    # Chat input
    user_input = st.chat_input("Ask about your Salesforce schema...")
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        display_chat_message("user", user_input)
        
        # Check if services are configured
        if not pinecone_key or not any([openai_key, anthropic_key, google_key]):
            response = """
            ⚠️ **Configuration Required**
            
            I can't process your request because the required API keys are not configured.
            
            **To get started:**
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
        else:
            # Show typing indicator
            with st.spinner("🤖 Thinking..."):
                try:
                    # Try to import and use the RAG service
                    from .rag_service import RAGService
                    rag_service = RAGService()
                    result = rag_service.query(user_input)
                    response = result["response"]
                except Exception as e:
                    response = f"""
                    ⚠️ **Service Error**
                    
                    I encountered an error while processing your request: {str(e)}
                    
                    **Possible causes:**
                    - Pinecone index doesn't exist or is inaccessible
                    - API keys are invalid or expired
                    - Network connectivity issues
                    
                    Please check your configuration and try again.
                    """
                    logger.error(f"Error processing query: {e}")
        
        # Add assistant response to chat
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
        st.rerun()

if __name__ == "__main__":
    main()
