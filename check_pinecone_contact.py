#!/usr/bin/env python3
"""
Check what Contact-related documents are actually in Pinecone
"""
import sys
import os
sys.path.append('src')

from chatbot.rag_service import RAGService

def check_contact_in_pinecone():
    """Check what Contact documents are in Pinecone"""
    print("🔍 Checking Contact documents in Pinecone...")
    
    try:
        rag_service = RAGService()
        
        # Search for all documents
        print("\n=== Searching for all documents ===")
        results = rag_service.vector_store.similarity_search("", k=1000)
        print(f"Total documents in vector store: {len(results)}")
        
        # Look for Contact-related documents
        contact_docs = []
        for doc in results:
            doc_id = doc.metadata.get('id', 'unknown')
            if 'contact' in doc_id.lower():
                contact_docs.append(doc_id)
        
        print(f"\n=== Contact-related documents found: {len(contact_docs)} ===")
        for doc_id in contact_docs:
            print(f"  - {doc_id}")
        
        # Check specifically for salesforce_object_Contact
        main_contact_found = any('salesforce_object_Contact' == doc_id for doc_id in contact_docs)
        if main_contact_found:
            print("\n✅ Main Contact object (salesforce_object_Contact) found!")
        else:
            print("\n❌ Main Contact object (salesforce_object_Contact) NOT found!")
        
        # Check document types
        print(f"\n=== Document type breakdown ===")
        type_counts = {}
        for doc in results:
            doc_type = doc.metadata.get('type', 'unknown')
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        for doc_type, count in type_counts.items():
            print(f"  - {doc_type}: {count}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_contact_in_pinecone()

