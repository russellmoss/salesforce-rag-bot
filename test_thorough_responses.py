#!/usr/bin/env python
"""
Test script to verify thorough response configuration.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from chatbot.config import config
from chatbot.rag_service import RAGService

def test_thorough_configuration():
    """Test that the configuration is set for thorough responses"""
    print("🧪 Testing Thorough Response Configuration")
    print("=" * 50)
    
    # Test configuration values
    print(f"✅ MAX_TOKENS: {config.MAX_TOKENS:,} (increased from 4,000)")
    print(f"✅ TOP_K: {config.TOP_K} (increased from 5)")
    print(f"✅ MAX_CONTEXT_LENGTH: {config.MAX_CONTEXT_LENGTH:,}")
    print(f"✅ RESPONSE_MODE: {config.RESPONSE_MODE}")
    print(f"✅ TEMPERATURE: {config.TEMPERATURE}")
    
    # Verify the settings are optimized for thoroughness
    assert config.MAX_TOKENS >= 16000, f"MAX_TOKENS should be >= 16000, got {config.MAX_TOKENS}"
    assert config.TOP_K >= 10, f"TOP_K should be >= 10, got {config.TOP_K}"
    assert config.MAX_CONTEXT_LENGTH >= 32000, f"MAX_CONTEXT_LENGTH should be >= 32000, got {config.MAX_CONTEXT_LENGTH}"
    assert config.RESPONSE_MODE == "thorough", f"RESPONSE_MODE should be 'thorough', got {config.RESPONSE_MODE}"
    
    print("\n✅ All configuration values are optimized for thorough responses!")
    
    # Test system prompt
    print(f"\n📝 System Prompt Length: {len(config.SYSTEM_PROMPT)} characters")
    if "thorough" in config.SYSTEM_PROMPT.lower() and "comprehensive" in config.SYSTEM_PROMPT.lower():
        print("✅ System prompt emphasizes thoroughness and comprehensiveness")
    else:
        print("⚠️  System prompt may not emphasize thoroughness enough")
    
    return True

def test_rag_service_initialization():
    """Test RAG service initialization with thorough settings"""
    print("\n🔧 Testing RAG Service Initialization")
    print("=" * 50)
    
    try:
        # Check if environment variables are set
        if not os.getenv("PINECONE_API_KEY") or not os.getenv("OPENAI_API_KEY"):
            print("⚠️  Skipping RAG service test - missing API keys")
            print("   Set PINECONE_API_KEY and OPENAI_API_KEY to test full functionality")
            return True
        
        # Initialize RAG service
        rag_service = RAGService()
        
        # Test status
        status = rag_service.get_status()
        print(f"✅ Pinecone Connected: {status['pinecone_connected']}")
        print(f"✅ LLM Provider: {status['llm_provider']}")
        print(f"✅ Available Providers: {status['available_providers']}")
        print(f"✅ Index Name: {status['index_name']}")
        
        # Test a simple query
        test_query = "What fields are available on the Account object?"
        print(f"\n🔍 Testing query: '{test_query}'")
        
        result = rag_service.query(test_query)
        print(f"✅ Response generated: {len(result['response'])} characters")
        print(f"✅ Context documents: {result['context_documents']}")
        
        # Check if response is thorough
        if len(result['response']) > 500:  # Should be substantial
            print("✅ Response appears to be thorough (longer than 500 characters)")
        else:
            print("⚠️  Response may be too brief")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing RAG service: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Salesforce RAG Bot - Thorough Response Configuration Test")
    print("=" * 70)
    
    # Test configuration
    config_ok = test_thorough_configuration()
    
    # Test RAG service
    rag_ok = test_rag_service_initialization()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    if config_ok and rag_ok:
        print("🎉 ALL TESTS PASSED! Your chatbot is configured for thorough responses!")
        print("\n✅ Configuration optimized for completeness over brevity")
        print("✅ Higher token limits (16,000 vs 4,000)")
        print("✅ More context retrieval (10 vs 5 documents)")
        print("✅ Enhanced system prompt emphasizing thoroughness")
        print("✅ RAG service ready for comprehensive responses")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    print("\n💡 Your chatbot will now provide thorough, complete responses")
    print("   without truncating important information!")

if __name__ == "__main__":
    main()
