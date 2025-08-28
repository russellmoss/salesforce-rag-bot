#!/usr/bin/env python3
"""
Test script for Enhanced RAG Service
"""

import sys
import os
sys.path.append('src')

from chatbot.enhanced_rag_service import EnhancedRAGService

def test_enhanced_rag():
    """Test the enhanced RAG service"""
    print("🔍 Testing Enhanced RAG Service...")
    
    try:
        # Initialize enhanced RAG service
        rag_service = EnhancedRAGService()
        
        # Test queries
        test_queries = [
            "what fields are in my contact object?",
            "show me account object fields",
            "what security permissions exist for user object?",
            "tell me about lead automation",
            "what validation rules are on opportunity?"
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print('='*60)
            
            result = rag_service.query(query)
            
            print(f"Response length: {len(result['response'])} characters")
            print(f"Context documents: {result['context_documents']}")
            print(f"Response preview: {result['response'][:300]}...")
            
            if result['context_documents'] > 0:
                print("✅ SUCCESS: Found relevant documents!")
            else:
                print("❌ FAILED: No documents found")
        
        # Test status
        print(f"\n{'='*60}")
        print("Service Status:")
        print('='*60)
        status = rag_service.get_status()
        for key, value in status.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_rag()
