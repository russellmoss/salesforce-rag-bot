#!/usr/bin/env python3
"""
Test script for SmartCache system.
"""

import time
import json
import tempfile
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the SmartCache
from src.pipeline.smart_cache import SmartCache, create_cache_for_pipeline

def test_basic_caching():
    """Test basic cache operations."""
    print("🧪 Testing Basic Caching...")
    
    # Create temporary cache directory
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = SmartCache(Path(temp_dir), max_age_hours=1)
        
        # Test data
        test_data = {
            "flows": ["Flow1", "Flow2"],
            "triggers": ["Trigger1"],
            "code_complexity": {"triggers": [], "classes": []}
        }
        
        # Test cache write
        cache.cache_data("Account", "automation", test_data)
        print("✅ Cache write successful")
        
        # Test cache read
        cached_data = cache.get_cached_data("Account", "automation")
        if cached_data and cached_data.get('data') == test_data:
            print("✅ Cache read successful")
        else:
            print("❌ Cache read failed")
            return False
        
        # Test cache miss for different object
        cached_data = cache.get_cached_data("Contact", "automation")
        if cached_data is None:
            print("✅ Cache miss working correctly")
        else:
            print("❌ Cache miss failed")
            return False
        
        return True

def test_cache_invalidation():
    """Test cache invalidation based on age."""
    print("\n🧪 Testing Cache Invalidation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create cache with very short max age (1 second)
        cache = SmartCache(Path(temp_dir), max_age_hours=1/3600)  # 1 second
        
        test_data = {"test": "data"}
        cache.cache_data("TestObject", "test", test_data)
        
        # Should be cached immediately
        cached_data = cache.get_cached_data("TestObject", "test")
        if cached_data:
            print("✅ Fresh cache read successful")
        else:
            print("❌ Fresh cache read failed")
            return False
        
        # Wait for cache to expire
        time.sleep(2)
        
        # Should not be cached anymore
        cached_data = cache.get_cached_data("TestObject", "test")
        if cached_data is None:
            print("✅ Cache invalidation working")
        else:
            print("❌ Cache invalidation failed")
            return False
        
        return True

def test_compression():
    """Test compression functionality."""
    print("\n🧪 Testing Compression...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with compression enabled
        cache_compressed = SmartCache(Path(temp_dir) / "compressed", enable_compression=True)
        
        # Create large test data
        large_data = {
            "large_field": "x" * 10000,  # 10KB of data
            "array": list(range(1000)),
            "nested": {"deep": {"structure": {"with": "lots", "of": "data"}}}
        }
        
        cache_compressed.cache_data("LargeObject", "large_data", large_data)
        
        # Check if compressed file exists
        compressed_files = list((Path(temp_dir) / "compressed").rglob("*.gz"))
        if compressed_files:
            print("✅ Compression working - .gz files created")
        else:
            print("❌ Compression failed - no .gz files")
            return False
        
        # Test reading compressed data
        cached_data = cache_compressed.get_cached_data("LargeObject", "large_data")
        if cached_data and cached_data.get('data') == large_data:
            print("✅ Compressed data read successful")
        else:
            print("❌ Compressed data read failed")
            return False
        
        return True

def test_cache_stats():
    """Test cache statistics."""
    print("\n🧪 Testing Cache Statistics...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = SmartCache(Path(temp_dir))
        
        # Generate some cache activity
        for i in range(5):
            cache.cache_data(f"Object{i}", "test", {"data": i})
        
        # Generate some hits and misses
        for i in range(3):
            cache.get_cached_data(f"Object{i}", "test")  # Should hit
            cache.get_cached_data(f"Object{i}", "nonexistent")  # Should miss
        
        stats = cache.get_cache_stats()
        
        print(f"Cache Stats: {stats}")
        
        # Verify stats
        if stats['writes'] == 5 and stats['hits'] == 3 and stats['misses'] == 3:
            print("✅ Cache statistics working correctly")
            return True
        else:
            print("❌ Cache statistics incorrect")
            return False

def test_cache_clearing():
    """Test cache clearing functionality."""
    print("\n🧪 Testing Cache Clearing...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = SmartCache(Path(temp_dir))
        
        # Create some test data
        for i in range(3):
            cache.cache_data(f"Object{i}", "test", {"data": i})
            cache.cache_data(f"Object{i}", "automation", {"flows": []})
        
        # Check initial file count
        initial_files = len(list(Path(temp_dir).rglob("*.json*")))
        print(f"Initial cache files: {initial_files}")
        
        # Clear specific data type
        cleared = cache.clear_cache(data_type="test")
        print(f"Cleared {cleared} 'test' files")
        
        # Check remaining files
        remaining_files = len(list(Path(temp_dir).rglob("*.json*")))
        print(f"Remaining cache files: {remaining_files}")
        
        if cleared == 3 and remaining_files == 3:  # 3 automation files should remain
            print("✅ Cache clearing working correctly")
            return True
        else:
            print("❌ Cache clearing failed")
            return False

def test_convenience_functions():
    """Test convenience functions."""
    print("\n🧪 Testing Convenience Functions...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = create_cache_for_pipeline(temp_dir, max_age_hours=24)
        
        # Test automation data caching
        automation_data = {"flows": ["Flow1"], "triggers": ["Trigger1"]}
        
        from src.pipeline.smart_cache import (
            cache_automation_data, 
            get_cached_automation_data,
            cache_stats_data,
            get_cached_stats_data
        )
        
        # Test automation convenience functions
        cache_automation_data(cache, "Account", automation_data)
        cached_automation = get_cached_automation_data(cache, "Account")
        
        if cached_automation and cached_automation.get('data') == automation_data:
            print("✅ Automation convenience functions working")
        else:
            print("❌ Automation convenience functions failed")
            return False
        
        # Test stats convenience functions
        stats_data = {"record_count": 1000, "field_count": 50}
        cache_stats_data(cache, "Account", stats_data, sample_size=100)
        cached_stats = get_cached_stats_data(cache, "Account", sample_size=100)
        
        if cached_stats and cached_stats.get('data') == stats_data:
            print("✅ Stats convenience functions working")
        else:
            print("❌ Stats convenience functions failed")
            return False
        
        return True

def test_performance():
    """Test cache performance with realistic data."""
    print("\n🧪 Testing Performance...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = SmartCache(Path(temp_dir))
        
        # Simulate realistic automation data
        realistic_data = {
            "flows": [f"Flow_{i}" for i in range(10)],
            "triggers": [f"Trigger_{i}" for i in range(5)],
            "code_complexity": {
                "triggers": [
                    {"name": f"Trigger_{i}", "total_lines": 100 + i, "comment_lines": 20 + i}
                    for i in range(5)
                ],
                "classes": [
                    {"name": f"Class_{i}", "total_lines": 200 + i, "comment_lines": 40 + i}
                    for i in range(3)
                ]
            }
        }
        
        # Test write performance
        start_time = time.time()
        for i in range(100):
            cache.cache_data(f"Object_{i}", "automation", realistic_data)
        write_time = time.time() - start_time
        
        # Test read performance
        start_time = time.time()
        for i in range(100):
            cache.get_cached_data(f"Object_{i}", "automation")
        read_time = time.time() - start_time
        
        print(f"Write 100 objects: {write_time:.3f}s ({100/write_time:.1f} objects/sec)")
        print(f"Read 100 objects: {read_time:.3f}s ({100/read_time:.1f} objects/sec)")
        
        # Performance should be reasonable
        if write_time < 5.0 and read_time < 2.0:
            print("✅ Performance acceptable")
            return True
        else:
            print("❌ Performance too slow")
            return False

def main():
    """Run all tests."""
    print("🚀 SMART CACHE TESTING SUITE")
    print("=" * 50)
    
    tests = [
        ("Basic Caching", test_basic_caching),
        ("Cache Invalidation", test_cache_invalidation),
        ("Compression", test_compression),
        ("Cache Statistics", test_cache_stats),
        ("Cache Clearing", test_cache_clearing),
        ("Convenience Functions", test_convenience_functions),
        ("Performance", test_performance),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! SmartCache is ready for production!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
