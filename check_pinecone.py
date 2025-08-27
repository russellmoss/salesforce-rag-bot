#!/usr/bin/env python3
"""
Simple script to check what's actually in the Pinecone index
"""

import os
import sys
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# Load environment variables
load_dotenv()

def check_pinecone_index():
    """Check what documents are actually in the Pinecone index"""
    
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    
    # Get the index
    index_name = os.getenv('PINECONE_INDEX_NAME', 'salesforce-schema')
    index = pc.Index(index_name)
    
    # Get index stats
    stats = index.describe_index_stats()
    print(f"Index stats: {stats}")
    
    # Get some sample documents
    print("\nFetching sample documents...")
    
    # Use a simple query to get documents
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Create a test embedding
    test_text = "test"
    response = openai_client.embeddings.create(
        input=[test_text],
        model="text-embedding-3-small"
    )
    test_embedding = response.data[0].embedding
    
    # Query the index
    results = index.query(
        vector=test_embedding,
        top_k=10,
        include_metadata=True
    )
    
    print(f"\nDirect Pinecone Query results:")
    for i, match in enumerate(results.matches):
        print(f"{i+1}. ID: {match.id}")
        print(f"   Score: {match.score}")
        print(f"   Metadata: {match.metadata}")
        print()
    
    # Now test LangChain Pinecone
    print("\n" + "="*50)
    print("Testing LangChain Pinecone...")
    
    # Initialize OpenAI embeddings
    embedding_function = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Initialize vector store
    vector_store = PineconeVectorStore(
        index_name=index_name,
        embedding=embedding_function
    )
    
    # Test 1: Get all documents
    print("\n1. Getting all documents with LangChain...")
    all_results = vector_store.similarity_search("", k=10)
    print(f"Found {len(all_results)} documents")
    
    for i, doc in enumerate(all_results):
        print(f"\nLangChain Document {i+1}:")
        print(f"  ID: {doc.metadata.get('id', 'unknown')}")
        print(f"  Type: {doc.metadata.get('type', 'unknown')}")
        print(f"  Object: {doc.metadata.get('object_name', 'unknown')}")
        print(f"  Content (first 200 chars): {doc.page_content[:200]}")
    
    # Test 2: Search for security documents specifically
    print("\n2. Searching for security documents with LangChain...")
    security_results = vector_store.similarity_search("security permissions", k=5)
    print(f"Found {len(security_results)} security documents")
    
    for i, doc in enumerate(security_results):
        print(f"\nLangChain Security Document {i+1}:")
        print(f"  ID: {doc.metadata.get('id', 'unknown')}")
        print(f"  Type: {doc.metadata.get('type', 'unknown')}")
        print(f"  Object: {doc.metadata.get('object_name', 'unknown')}")
        print(f"  Content (first 200 chars): {doc.page_content[:200]}")
    
    # Test 3: Search specifically for Account security
    print("\n3. Searching specifically for Account security with LangChain...")
    account_queries = [
        "What security permissions do we have for the Account object?",
        "Account security permissions",
        "Account CRUD permissions",
        "Account object permissions",
        "security Account",
        "Account field permissions"
    ]
    
    for query in account_queries:
        print(f"\n--- Testing query: '{query}' ---")
        account_results = vector_store.similarity_search(query, k=5)
        print(f"Found {len(account_results)} results")
        
        account_found = False
        for i, doc in enumerate(account_results):
            doc_id = doc.metadata.get('id', 'unknown')
            print(f"  {i+1}. ID: {doc_id}")
            print(f"     Type: {doc.metadata.get('type', 'unknown')}")
            print(f"     Object: {doc.metadata.get('object_name', 'unknown')}")
            
            if 'Account' in doc_id:
                account_found = True
                print(f"     *** ACCOUNT FOUND! ***")
        
        if not account_found:
            print("     ❌ NO ACCOUNT DOCUMENT FOUND")

if __name__ == "__main__":
    check_pinecone_index()
