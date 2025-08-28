#!/usr/bin/env python3
"""
Test script to directly search for Contact object in the vector store
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from chatbot.rag_service import RAGService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_contact_search():
    """Test direct search for Contact object"""
    print("🔍 Testing direct Contact object search...")
    
    try:
        # Initialize RAG service
        rag_service = RAGService()
        
        # Test 1: Direct search for Contact object
        print("\n=== Test 1: Direct search for 'salesforce_object_Contact' ===")
        try:
            results = rag_service.vector_store.similarity_search("salesforce_object_Contact", k=10)
            print(f"Found {len(results)} results")
            for i, doc in enumerate(results[:5]):
                doc_id = doc.metadata.get('id', 'unknown')
                object_name = doc.metadata.get('object_name', 'unknown')
                print(f"  {i+1}. ID={doc_id}, Object={object_name}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Search for "Contact"
        print("\n=== Test 2: Search for 'Contact' ===")
        try:
            results = rag_service.vector_store.similarity_search("Contact", k=10)
            print(f"Found {len(results)} results")
            for i, doc in enumerate(results[:5]):
                doc_id = doc.metadata.get('id', 'unknown')
                object_name = doc.metadata.get('object_name', 'unknown')
                print(f"  {i+1}. ID={doc_id}, Object={object_name}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 3: Search for "contact" (lowercase)
        print("\n=== Test 3: Search for 'contact' (lowercase) ===")
        try:
            results = rag_service.vector_store.similarity_search("contact", k=10)
            print(f"Found {len(results)} results")
            for i, doc in enumerate(results[:5]):
                doc_id = doc.metadata.get('id', 'unknown')
                object_name = doc.metadata.get('object_name', 'unknown')
                print(f"  {i+1}. ID={doc_id}, Object={object_name}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 4: Search for "Contact object fields"
        print("\n=== Test 4: Search for 'Contact object fields' ===")
        try:
            results = rag_service.vector_store.similarity_search("Contact object fields", k=10)
            print(f"Found {len(results)} results")
            for i, doc in enumerate(results[:5]):
                doc_id = doc.metadata.get('id', 'unknown')
                object_name = doc.metadata.get('object_name', 'unknown')
                print(f"  {i+1}. ID={doc_id}, Object={object_name}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 5: Check total documents
        print("\n=== Test 5: Check total documents ===")
        try:
            # Get more documents to search through
            results = rag_service.vector_store.similarity_search("", k=1000)
            print(f"Total documents in vector store: {len(results)}")
            
            # Look for Contact in all results
            contact_found = False
            contact_docs = []
            main_contact_found = False
            for doc in results:
                doc_id = doc.metadata.get('id', 'unknown')
                if 'contact' in doc_id.lower():
                    contact_docs.append(doc_id)
                    contact_found = True
                    if doc_id == 'salesforce_object_Contact':
                        main_contact_found = True
                        print(f"✅ Found main Contact object: {doc_id}")
            
            if not contact_found:
                print("❌ Contact document NOT found in vector store!")
            else:
                print(f"✅ Found {len(contact_docs)} Contact documents:")
                for doc_id in contact_docs[:10]:  # Show first 10
                    print(f"  - {doc_id}")
                
                if not main_contact_found:
                    print("❌ Main Contact object (salesforce_object_Contact) NOT found!")
                else:
                    print("✅ Main Contact object found!")
                
        except Exception as e:
            print(f"Error: {e}")
            
    except Exception as e:
        print(f"❌ Error initializing RAG service: {e}")

if __name__ == "__main__":
    test_contact_search()
