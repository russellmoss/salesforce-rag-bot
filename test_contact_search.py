#!/usr/bin/env python3
"""
Test script to debug Contact object search in Pinecone
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from chatbot.rag_service import RAGService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_contact_search():
    """Test Contact object search directly"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize RAG service
    rag_service = RAGService()
    
    print("🔍 Testing Contact object search...")
    
    # Test 1: Direct search for Contact object
    print("\n=== Test 1: Direct Contact search ===")
    try:
        results = rag_service.vector_store.similarity_search("Contact object fields", k=10)
        print(f"Found {len(results)} results")
        
        for i, doc in enumerate(results):
            doc_id = doc.metadata.get('id', 'unknown')
            object_name = doc.metadata.get('object_name', 'unknown')
            doc_type = doc.metadata.get('type', 'unknown')
            print(f"  {i+1}. ID={doc_id}, Object={object_name}, Type={doc_type}")
            
            # Check if this is the Contact object
            if object_name.lower() == 'contact' or 'contact' in doc_id.lower():
                print(f"     ✅ FOUND CONTACT OBJECT!")
                print(f"     Content preview: {doc.page_content[:200]}...")
    except Exception as e:
        print(f"❌ Error in direct search: {e}")
    
    # Test 2: Search for exact Contact ID
    print("\n=== Test 2: Search for exact Contact ID ===")
    try:
        results = rag_service.vector_store.similarity_search("salesforce_object_Contact", k=5)
        print(f"Found {len(results)} results for exact ID")
        
        for i, doc in enumerate(results):
            doc_id = doc.metadata.get('id', 'unknown')
            object_name = doc.metadata.get('object_name', 'unknown')
            print(f"  {i+1}. ID={doc_id}, Object={object_name}")
    except Exception as e:
        print(f"❌ Error in exact ID search: {e}")
    
    # Test 3: Search for "contact" in general
    print("\n=== Test 3: General 'contact' search ===")
    try:
        results = rag_service.vector_store.similarity_search("contact", k=10)
        print(f"Found {len(results)} results for 'contact'")
        
        for i, doc in enumerate(results):
            doc_id = doc.metadata.get('id', 'unknown')
            object_name = doc.metadata.get('object_name', 'unknown')
            doc_type = doc.metadata.get('type', 'unknown')
            print(f"  {i+1}. ID={doc_id}, Object={object_name}, Type={doc_type}")
            
            # Check if this is the Contact object
            if object_name.lower() == 'contact':
                print(f"     ✅ FOUND CONTACT OBJECT!")
    except Exception as e:
        print(f"❌ Error in general search: {e}")
    
    # Test 4: Check total documents in index
    print("\n=== Test 4: Check total documents ===")
    try:
        # Get a sample of documents to see what's in the index
        sample_results = rag_service.vector_store.similarity_search("", k=5)
        print(f"Sample documents in index:")
        
        for i, doc in enumerate(sample_results):
            doc_id = doc.metadata.get('id', 'unknown')
            object_name = doc.metadata.get('object_name', 'unknown')
            doc_type = doc.metadata.get('type', 'unknown')
            print(f"  {i+1}. ID={doc_id}, Object={object_name}, Type={doc_type}")
    except Exception as e:
        print(f"❌ Error getting sample: {e}")

if __name__ == "__main__":
    test_contact_search()
