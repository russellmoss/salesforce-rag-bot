#!/usr/bin/env python3
"""
Test script to compare async processing vs parallel processing performance.
"""

import time
import asyncio
import concurrent.futures
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock API call simulation
async def mock_api_call_async(name: str, delay: float = 0.1) -> Dict:
    """Mock async API call that simulates the time it takes to fetch automation data."""
    await asyncio.sleep(delay)  # Simulate async API call time
    return {
        "flows": [f"flow_{name}_1", f"flow_{name}_2"],
        "triggers": [f"trigger_{name}_1"],
        "code_complexity": {"triggers": [], "classes": []}
    }

def mock_api_call_sync(name: str, delay: float = 0.1) -> Dict:
    """Mock synchronous API call."""
    time.sleep(delay)  # Simulate sync API call time
    return {
        "flows": [f"flow_{name}_1", f"flow_{name}_2"],
        "triggers": [f"trigger_{name}_1"],
        "code_complexity": {"triggers": [], "classes": []}
    }

# Async processing functions
async def process_single_object_async(obj: Dict, delay: float = 0.1) -> Dict:
    """Async processing function that simulates the automation processing."""
    name = obj.get("name", "unknown")
    logger.debug(f"Processing {name} (async)...")
    
    # Simulate the 4 API calls
    automation_deps = await mock_api_call_async(f"{name}_automation", delay)
    fls_data = await mock_api_call_async(f"{name}_fls", delay)
    history_data = await mock_api_call_async(f"{name}_history", delay)
    complexity_data = await mock_api_call_async(f"{name}_complexity", delay)
    
    # Update object
    if "_relationshipMetadata" not in obj:
        obj["_relationshipMetadata"] = {}
    obj["_relationshipMetadata"]["automationSummary"] = automation_deps
    obj["_relationshipMetadata"]["automationSummary"]["code_complexity"] = complexity_data
    
    return obj

async def process_async(objects: List[Dict], max_concurrent: int = 20, delay: float = 0.1) -> List[Dict]:
    """Test async processing with semaphore limiting."""
    logger.info(f"Processing {len(objects)} objects with async (max {max_concurrent} concurrent)...")
    start_time = time.time()
    
    # Create semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(obj):
        async with semaphore:
            return await process_single_object_async(obj, delay)
    
    # Process all objects concurrently
    tasks = [process_with_semaphore(obj) for obj in objects]
    
    # Track progress
    completed = 0
    total_objects = len(objects)
    processed_objects = []
    
    # Process tasks as they complete
    for coro in asyncio.as_completed(tasks):
        try:
            processed_obj = await coro
            processed_objects.append(processed_obj)
            completed += 1
            
            if completed % 10 == 0:
                logger.info(f"  Completed {completed}/{total_objects} objects (async)")
                
        except Exception as e:
            logger.error(f"  !! Exception processing object: {e}")
            processed_objects.append(obj)
    
    end_time = time.time()
    logger.info(f"Async processing completed in {end_time - start_time:.2f} seconds")
    return processed_objects

# Parallel processing functions (for comparison)
def process_single_object_sync(obj: Dict, delay: float = 0.1) -> Dict:
    """Synchronous processing function."""
    name = obj.get("name", "unknown")
    logger.debug(f"Processing {name} (sync)...")
    
    # Simulate the 4 API calls
    automation_deps = mock_api_call_sync(f"{name}_automation", delay)
    fls_data = mock_api_call_sync(f"{name}_fls", delay)
    history_data = mock_api_call_sync(f"{name}_history", delay)
    complexity_data = mock_api_call_sync(f"{name}_complexity", delay)
    
    # Update object
    if "_relationshipMetadata" not in obj:
        obj["_relationshipMetadata"] = {}
    obj["_relationshipMetadata"]["automationSummary"] = automation_deps
    obj["_relationshipMetadata"]["automationSummary"]["code_complexity"] = complexity_data
    
    return obj

def process_parallel(objects: List[Dict], max_workers: int = 10, delay: float = 0.1) -> List[Dict]:
    """Test parallel processing with ThreadPoolExecutor."""
    logger.info(f"Processing {len(objects)} objects with parallel (max {max_workers} workers)...")
    start_time = time.time()
    
    processed_objects = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_obj = {
            executor.submit(process_single_object_sync, obj, delay): obj 
            for obj in objects
        }
        
        # Process completed tasks
        completed = 0
        for future in concurrent.futures.as_completed(future_to_obj):
            obj = future_to_obj[future]
            try:
                processed_obj = future.result()
                processed_objects.append(processed_obj)
                completed += 1
                
                if completed % 10 == 0:
                    logger.info(f"  Completed {completed}/{len(objects)} objects (parallel)")
                    
            except Exception as e:
                logger.error(f"  !! Exception processing {obj.get('name', 'unknown')}: {e}")
                processed_objects.append(obj)
    
    end_time = time.time()
    logger.info(f"Parallel processing completed in {end_time - start_time:.2f} seconds")
    return processed_objects

def process_sequential(objects: List[Dict], delay: float = 0.1) -> List[Dict]:
    """Test sequential processing for baseline comparison."""
    logger.info(f"Processing {len(objects)} objects sequentially...")
    start_time = time.time()
    
    processed_objects = []
    for i, obj in enumerate(objects, 1):
        processed_obj = process_single_object_sync(obj, delay)
        processed_objects.append(processed_obj)
        
        if i % 10 == 0:
            logger.info(f"  Completed {i}/{len(objects)} objects (sequential)")
    
    end_time = time.time()
    logger.info(f"Sequential processing completed in {end_time - start_time:.2f} seconds")
    return processed_objects

async def main():
    """Test all processing methods and compare performance."""
    # Create test objects
    test_objects = [
        {"name": f"Object_{i}", "fields": []} 
        for i in range(1, 51)  # 50 test objects
    ]
    
    logger.info("=" * 80)
    logger.info("ASYNC vs PARALLEL vs SEQUENTIAL PROCESSING COMPARISON")
    logger.info("=" * 80)
    
    # Test 1: Async Processing
    logger.info("\n" + "=" * 40)
    logger.info("TEST 1: ASYNC PROCESSING")
    logger.info("=" * 40)
    async_results = await process_async(test_objects, max_concurrent=20, delay=0.1)
    
    # Test 2: Parallel Processing
    logger.info("\n" + "=" * 40)
    logger.info("TEST 2: PARALLEL PROCESSING")
    logger.info("=" * 40)
    parallel_results = process_parallel(test_objects, max_workers=10, delay=0.1)
    
    # Test 3: Sequential Processing
    logger.info("\n" + "=" * 40)
    logger.info("TEST 3: SEQUENTIAL PROCESSING")
    logger.info("=" * 40)
    sequential_results = process_sequential(test_objects, delay=0.1)
    
    # Performance Summary
    logger.info("\n" + "=" * 80)
    logger.info("PERFORMANCE SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Objects processed: {len(test_objects)}")
    logger.info(f"Async results: {len(async_results)}")
    logger.info(f"Parallel results: {len(parallel_results)}")
    logger.info(f"Sequential results: {len(sequential_results)}")
    
    # Calculate expected times for real scenario
    logger.info("\n" + "=" * 80)
    logger.info("REAL-WORLD PROJECTIONS")
    logger.info("=" * 80)
    
    # For 1462 objects (your actual scenario)
    real_objects = 1462
    api_calls_per_object = 4
    total_api_calls = real_objects * api_calls_per_object
    
    logger.info(f"Real scenario: {real_objects} objects × {api_calls_per_object} API calls = {total_api_calls} total calls")
    
    # Sequential: 1462 objects × 4 calls × 150ms = ~15 minutes just for delays
    sequential_time_minutes = (real_objects * api_calls_per_object * 0.15) / 60
    logger.info(f"Sequential processing: ~{sequential_time_minutes:.1f} minutes (just for delays)")
    
    # Parallel: 10 workers × 300ms rate limit = 50 calls/second
    parallel_time_minutes = total_api_calls / (10 * 2) / 60  # 10 workers, 2 calls per second
    logger.info(f"Parallel processing: ~{parallel_time_minutes:.1f} minutes")
    
    # Async: 20 concurrent × 300ms rate limit = 100 calls/second
    async_time_minutes = total_api_calls / (20 * 2) / 60  # 20 concurrent, 2 calls per second
    logger.info(f"Async processing: ~{async_time_minutes:.1f} minutes")
    
    # Improvement calculations
    parallel_improvement = sequential_time_minutes / parallel_time_minutes
    async_improvement = sequential_time_minutes / async_time_minutes
    
    logger.info(f"\nPerformance improvements:")
    logger.info(f"Parallel vs Sequential: {parallel_improvement:.1f}x faster")
    logger.info(f"Async vs Sequential: {async_improvement:.1f}x faster")
    logger.info(f"Async vs Parallel: {async_improvement/parallel_improvement:.1f}x faster")
    
    logger.info("\n✅ Async processing test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
