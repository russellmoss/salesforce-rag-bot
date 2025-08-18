import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Salesforce RAG Bot"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    # Google Configuration
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GOOGLE_MODEL: str = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")
    
    # Pinecone Configuration
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
    PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "salesforce-schema")
    
    # RAG Configuration - Optimized for Thorough Responses
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "16000"))  # Increased for comprehensive responses
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    TOP_K: int = int(os.getenv("TOP_K", "10"))  # Increased for more context
    TOP_P: float = float(os.getenv("TOP_P", "0.95"))
    
    # Additional settings for thorough responses
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "32000"))  # Large context window
    RESPONSE_MODE: str = os.getenv("RESPONSE_MODE", "thorough")  # thorough, concise, or detailed
    
    # System prompt for the AI assistant - Optimized for Thorough Responses
    SYSTEM_PROMPT = """You are a Salesforce Schema AI Assistant, an expert in Salesforce data architecture, automation, security, and best practices. 

Your role is to help users understand their Salesforce org by providing comprehensive, thorough insights about:
- Object and field definitions
- Automation (flows, triggers, validation rules)
- Security model (profiles, permission sets, sharing rules)
- Data quality and usage patterns
- Best practices and recommendations

CRITICAL INSTRUCTIONS FOR THOROUGH RESPONSES:
1. **ALWAYS provide complete, comprehensive answers** - never truncate or summarize unless specifically asked
2. **Use ALL available context** from the retrieved Salesforce org data
3. **Include specific details** - field names, object relationships, automation details, etc.
4. **Explain technical concepts thoroughly** - assume the user wants complete understanding
5. **Provide actionable insights** with specific recommendations
6. **Include relevant metadata** - object types, field types, automation triggers, etc.
7. **Mention best practices** whenever relevant to the context
8. **If information is missing**, clearly state what additional data would be helpful
9. **Structure responses clearly** with headers, bullet points, and organized sections
10. **Prioritize completeness over brevity** - thorough responses are preferred

Remember: The user values thorough, complete information over token efficiency. Provide comprehensive answers that leave no important details out."""

    @classmethod
    def validate_config(cls) -> dict:
        """Validate configuration and return available providers"""
        available_providers = {}
        
        if cls.OPENAI_API_KEY:
            available_providers["openai"] = {
                "model": cls.OPENAI_MODEL,
                "api_key": cls.OPENAI_API_KEY
            }
        
        if cls.ANTHROPIC_API_KEY:
            available_providers["anthropic"] = {
                "model": cls.ANTHROPIC_MODEL,
                "api_key": cls.ANTHROPIC_API_KEY
            }
        
        if cls.GOOGLE_API_KEY:
            available_providers["google"] = {
                "model": cls.GOOGLE_MODEL,
                "api_key": cls.GOOGLE_API_KEY
            }
        
        if not cls.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is required for RAG functionality")
        
        return available_providers

# Global config instance
config = Config()
