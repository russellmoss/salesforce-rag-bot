#!/usr/bin/env python3
"""
Test script to directly search for the Account security document
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'chatbot'))

from rag_service import RAGService

def test_direct_search():
    """Test direct search for Account security document"""
    
    # Create RAG service instance
    rag_service = RAGService()
    
    # Test direct search for the security document
    test_queries = [
        "security_Account",
        "security permissions Account",
        "Account field-level security",
        "Account System Administrator permissions"
    ]
    
    print("Testing Direct Search for Account Security Document")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        try:
            # Search for documents
            documents = rag_service.search_context(query, top_k=10)
            
            print(f"Found {len(documents)} documents:")
            for i, doc in enumerate(documents):
                doc_id = doc.metadata.get('id', 'unknown')
                doc_type = doc.metadata.get('type', 'unknown')
                object_name = doc.metadata.get('object_name', 'unknown')
                print(f"  {i+1}. ID: {doc_id}, Type: {doc_type}, Object: {object_name}")
                
                # Check if this is the Account security document
                if doc_id == 'security_Account':
                    print(f"     ✅ FOUND ACCOUNT SECURITY DOCUMENT!")
                    # Show a snippet of the content
                    content = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                    print(f"     Content preview: {content}")
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_direct_search()
