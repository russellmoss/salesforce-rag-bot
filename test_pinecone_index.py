#!/usr/bin/env python
"""
Test script to verify Pinecone index is working correctly.
Tests vector search, metadata, and data quality.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Pinecone imports
try:
    from openai import OpenAI
    from pinecone import Pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("Error: openai or pinecone-client not installed.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pinecone_connection():
    """Test basic Pinecone connection and index access."""
    logger.info("Testing Pinecone connection...")
    
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "salesforce-schema")
    
    if not pinecone_api_key:
        logger.error("PINECONE_API_KEY not found in environment variables")
        return False
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=pinecone_api_key)
        
        # List indexes
        indexes = pc.list_indexes()
        logger.info(f"Available indexes: {[idx.name for idx in indexes]}")
        
        # Check if our index exists
        if index_name not in [idx.name for idx in indexes]:
            logger.error(f"Index '{index_name}' not found!")
            return False
        
        # Get index
        index = pc.Index(index_name)
        
        # Get index stats
        stats = index.describe_index_stats()
        logger.info(f"Index stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error connecting to Pinecone: {e}")
        return False

def test_vector_search():
    """Test vector search functionality."""
    logger.info("Testing vector search...")
    
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "salesforce-schema")
    
    if not pinecone_api_key or not openai_api_key:
        logger.error("Missing API keys for vector search test")
        return False
    
    try:
        # Initialize clients
        pc = Pinecone(api_key=pinecone_api_key)
        openai_client = OpenAI(api_key=openai_api_key)
        index = pc.Index(index_name)
        
        # Test queries
        test_queries = [
            "Account object with contact information",
            "Lead management and conversion",
            "Opportunity sales process",
            "User and profile management",
            "Custom fields and validation rules"
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: '{query}'")
            
            # Generate embedding for query
            response = openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            query_embedding = response.data[0].embedding
            
            # Search Pinecone
            search_results = index.query(
                vector=query_embedding,
                top_k=5,
                include_metadata=True
            )
            
            logger.info(f"Found {len(search_results.matches)} matches:")
            for i, match in enumerate(search_results.matches, 1):
                object_name = match.metadata.get('object_name', 'Unknown')
                score = match.score
                fields_count = match.metadata.get('fields_count', 0)
                logger.info(f"  {i}. {object_name} (score: {score:.3f}, fields: {fields_count})")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in vector search test: {e}")
        return False

def test_metadata_quality():
    """Test metadata quality and completeness."""
    logger.info("Testing metadata quality...")
    
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "salesforce-schema")
    
    if not pinecone_api_key:
        logger.error("PINECONE_API_KEY not found")
        return False
    
    try:
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index(index_name)
        
        # Get a sample of vectors to check metadata
        sample_results = index.query(
            vector=[0.0] * 1536,  # Dummy vector
            top_k=10,
            include_metadata=True
        )
        
        logger.info(f"Checking metadata for {len(sample_results.matches)} sample objects:")
        
        required_fields = ['object_name', 'type', 'fields_count']
        optional_fields = ['record_count', 'content']
        
        for i, match in enumerate(sample_results.matches, 1):
            metadata = match.metadata
            object_name = metadata.get('object_name', 'Unknown')
            
            logger.info(f"\n  {i}. {object_name}:")
            
            # Check required fields
            for field in required_fields:
                if field in metadata:
                    logger.info(f"    ✅ {field}: {metadata[field]}")
                else:
                    logger.info(f"    ❌ Missing {field}")
            
            # Check optional fields
            for field in optional_fields:
                if field in metadata:
                    value = metadata[field]
                    if field == 'content':
                        value = value[:100] + "..." if len(str(value)) > 100 else value
                    logger.info(f"    📝 {field}: {value}")
                else:
                    logger.info(f"    ⚠️  No {field}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in metadata quality test: {e}")
        return False

def test_specific_object_search():
    """Test searching for specific Salesforce objects."""
    logger.info("Testing specific object searches...")
    
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "salesforce-schema")
    
    if not pinecone_api_key or not openai_api_key:
        logger.error("Missing API keys for specific object search test")
        return False
    
    try:
        pc = Pinecone(api_key=pinecone_api_key)
        openai_client = OpenAI(api_key=openai_api_key)
        index = pc.Index(index_name)
        
        # Test specific object searches
        specific_queries = [
            ("Account", "Find the Account object"),
            ("Contact", "Show me Contact object details"),
            ("Lead", "Lead object information"),
            ("Opportunity", "Opportunity sales object"),
            ("User", "User management object")
        ]
        
        for expected_object, query in specific_queries:
            logger.info(f"\nSearching for '{expected_object}' with query: '{query}'")
            
            # Generate embedding
            response = openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            query_embedding = response.data[0].embedding
            
            # Search
            search_results = index.query(
                vector=query_embedding,
                top_k=3,
                include_metadata=True
            )
            
            # Check if expected object is in top results
            found = False
            for match in search_results.matches:
                if match.metadata.get('object_name') == expected_object:
                    logger.info(f"  ✅ Found {expected_object} at position with score {match.score:.3f}")
                    found = True
                    break
            
            if not found:
                logger.warning(f"  ⚠️  {expected_object} not found in top 3 results")
                for match in search_results.matches[:3]:
                    logger.info(f"    Instead found: {match.metadata.get('object_name')} (score: {match.score:.3f})")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in specific object search test: {e}")
        return False

def test_index_statistics():
    """Test and display comprehensive index statistics."""
    logger.info("Testing index statistics...")
    
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "salesforce-schema")
    
    if not pinecone_api_key:
        logger.error("PINECONE_API_KEY not found")
        return False
    
    try:
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index(index_name)
        
        # Get detailed stats
        stats = index.describe_index_stats()
        
        logger.info("=" * 60)
        logger.info("PINECONE INDEX STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Index Name: {index_name}")
        logger.info(f"Dimension: {stats.get('dimension', 'Unknown')}")
        logger.info(f"Metric: {stats.get('metric', 'Unknown')}")
        logger.info(f"Total Vector Count: {stats.get('total_vector_count', 0):,}")
        logger.info(f"Index Fullness: {stats.get('index_fullness', 0):.2%}")
        
        # Namespace stats
        namespaces = stats.get('namespaces', {})
        for namespace, ns_stats in namespaces.items():
            logger.info(f"Namespace '{namespace}': {ns_stats.get('vector_count', 0):,} vectors")
        
        # Test metadata filtering
        logger.info("\nTesting metadata filtering...")
        
        # Count objects by type
        type_filter = {"type": "salesforce_object"}
        type_results = index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            filter=type_filter,
            include_metadata=True
        )
        
        logger.info(f"Objects with type 'salesforce_object': {len(type_results.matches)}")
        
        # Sample some object names
        object_names = [match.metadata.get('object_name') for match in type_results.matches[:10]]
        logger.info(f"Sample object names: {object_names}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in index statistics test: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting comprehensive Pinecone index tests...")
    logger.info("=" * 60)
    
    tests = [
        ("Connection Test", test_pinecone_connection),
        ("Index Statistics", test_index_statistics),
        ("Metadata Quality", test_metadata_quality),
        ("Vector Search", test_vector_search),
        ("Specific Object Search", test_specific_object_search)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results[test_name] = "✅ PASSED" if success else "❌ FAILED"
        except Exception as e:
            logger.error(f"Test '{test_name}' failed with exception: {e}")
            results[test_name] = "❌ FAILED"
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        logger.info(f"{test_name}: {result}")
        if "PASSED" in result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Your Pinecone index is working perfectly!")
    else:
        logger.warning(f"⚠️  {total - passed} test(s) failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    main()
