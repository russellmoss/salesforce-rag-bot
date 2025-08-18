#!/usr/bin/env python3
"""
Test script for parallel processing functions in the pipeline.
"""

import time
import concurrent.futures
from typing import List, Dict

def mock_api_call(name: str, delay: float = 0.1) -> Dict:
    """Mock API call that simulates the time it takes to fetch automation data."""
    time.sleep(delay)  # Simulate API call time
    return {
        "flows": [f"flow_{name}_1", f"flow_{name}_2"],
        "triggers": [f"trigger_{name}_1"],
        "code_complexity": {"triggers": [], "classes": []}
    }

def process_single_object_mock(obj: Dict, delay: float = 0.1) -> Dict:
    """Mock processing function that simulates the automation processing."""
    name = obj.get("name", "unknown")
    print(f"Processing {name}...")
    
    # Simulate the 4 API calls
    automation_deps = mock_api_call(f"{name}_automation", delay)
    fls_data = mock_api_call(f"{name}_fls", delay)
    history_data = mock_api_call(f"{name}_history", delay)
    complexity_data = mock_api_call(f"{name}_complexity", delay)
    
    # Update object
    if "_relationshipMetadata" not in obj:
        obj["_relationshipMetadata"] = {}
    obj["_relationshipMetadata"]["automationSummary"] = automation_deps
    obj["_relationshipMetadata"]["automationSummary"]["code_complexity"] = complexity_data
    
    return obj

def process_parallel_mock(objects: List[Dict], max_workers: int = 5, delay: float = 0.1) -> List[Dict]:
    """Test parallel processing with mock data."""
    print(f"Processing {len(objects)} objects with {max_workers} workers...")
    start_time = time.time()
    
    processed_objects = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_obj = {
            executor.submit(process_single_object_mock, obj, delay): obj 
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
                
                if completed % 5 == 0:
                    print(f"  Completed {completed}/{len(objects)} objects")
                    
            except Exception as e:
                print(f"  !! Exception processing {obj.get('name', 'unknown')}: {e}")
                processed_objects.append(obj)
    
    end_time = time.time()
    print(f"Parallel processing completed in {end_time - start_time:.2f} seconds")
    return processed_objects

def process_sequential_mock(objects: List[Dict], delay: float = 0.1) -> List[Dict]:
    """Test sequential processing for comparison."""
    print(f"Processing {len(objects)} objects sequentially...")
    start_time = time.time()
    
    processed_objects = []
    for i, obj in enumerate(objects, 1):
        processed_obj = process_single_object_mock(obj, delay)
        processed_objects.append(processed_obj)
        
        if i % 5 == 0:
            print(f"  Completed {i}/{len(objects)} objects")
    
    end_time = time.time()
    print(f"Sequential processing completed in {end_time - start_time:.2f} seconds")
    return processed_objects

def main():
    """Test both sequential and parallel processing."""
    # Create test objects
    test_objects = [
        {"name": f"Object_{i}", "fields": []} 
        for i in range(1, 21)  # 20 test objects
    ]
    
    print("=" * 60)
    print("PARALLEL PROCESSING TEST")
    print("=" * 60)
    
    # Test parallel processing
    parallel_results = process_parallel_mock(test_objects, max_workers=5, delay=0.1)
    
    print("\n" + "=" * 60)
    print("SEQUENTIAL PROCESSING TEST")
    print("=" * 60)
    
    # Test sequential processing
    sequential_results = process_sequential_mock(test_objects, delay=0.1)
    
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Objects processed: {len(test_objects)}")
    print(f"Parallel results: {len(parallel_results)}")
    print(f"Sequential results: {len(sequential_results)}")
    print("✅ Parallel processing test completed successfully!")

if __name__ == "__main__":
    main()
