#!/usr/bin/env python3
"""
Test script to verify timeout improvements in the Salesforce schema pipeline.
"""

import subprocess
import time
import sys
from pathlib import Path

def test_timeout_settings():
    """Test that timeout settings are properly configured."""
    print("🔍 Testing Timeout Configuration...")
    
    # Check the pipeline script for timeout settings
    pipeline_file = Path("src/pipeline/build_schema_library_end_to_end.py")
    if not pipeline_file.exists():
        print("❌ Pipeline file not found")
        return False
    
    try:
        with open(pipeline_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fallback to different encoding if UTF-8 fails
        with open(pipeline_file, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Check for timeout=300 in run_sf function
    if 'timeout: int = 300' in content:
        print("✅ Individual command timeout: 300s (5 minutes)")
    else:
        print("❌ Individual command timeout not set to 300s")
        return False
    
    # Check for batch processing
    if 'BATCH_SIZE = 50' in content:
        print("✅ Batch processing: 50 objects per batch")
    else:
        print("❌ Batch processing not configured")
        return False
    
    # Check for enhanced error handling
    if 'subprocess.TimeoutExpired' in content:
        print("✅ Enhanced timeout error handling")
    else:
        print("❌ Enhanced timeout error handling not found")
        return False
    
    return True

def test_github_actions_timeout():
    """Test GitHub Actions timeout configuration."""
    print("\n🔍 Testing GitHub Actions Timeout...")
    
    workflow_file = Path(".github/workflows/run_pipeline.yml")
    if not workflow_file.exists():
        print("❌ GitHub Actions workflow file not found")
        return False
    
    try:
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fallback to different encoding if UTF-8 fails
        with open(workflow_file, 'r', encoding='latin-1') as f:
            content = f.read()
    
    if 'timeout-minutes: 480' in content:
        print("✅ GitHub Actions timeout: 480 minutes (8 hours)")
    else:
        print("❌ GitHub Actions timeout not set to 480 minutes")
        return False
    
    return True

def test_resume_capability():
    """Test that resume functionality is available."""
    print("\n🔍 Testing Resume Capability...")
    
    try:
        # Test help output to see if resume option is available
        result = subprocess.run([
            sys.executable, "src/pipeline/build_schema_library_end_to_end.py", "--help"
        ], capture_output=True, text=True, timeout=30)
        
        if '--resume' in result.stdout:
            print("✅ Resume capability available")
            return True
        else:
            print("❌ Resume capability not found in help")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Help command timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing resume capability: {e}")
        return False

def test_batch_processing():
    """Test that batch processing is implemented."""
    print("\n🔍 Testing Batch Processing Implementation...")
    
    pipeline_file = Path("src/pipeline/build_schema_library_end_to_end.py")
    if not pipeline_file.exists():
        print("❌ Pipeline file not found")
        return False
    
    try:
        with open(pipeline_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fallback to different encoding if UTF-8 fails
        with open(pipeline_file, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Check for batch processing logic
    batch_indicators = [
        'BATCH_SIZE = 50',
        'for batch_start in range(0, total, BATCH_SIZE)',
        'Pausing 30 seconds between batches',
        'Processing batch'
    ]
    
    for indicator in batch_indicators:
        if indicator in content:
            print(f"✅ Found: {indicator}")
        else:
            print(f"❌ Missing: {indicator}")
            return False
    
    return True

def main():
    """Run all timeout tests."""
    print("🚀 Salesforce Schema Pipeline - Timeout Fixes Test")
    print("=" * 60)
    
    tests = [
        ("Individual Command Timeout", test_timeout_settings),
        ("GitHub Actions Timeout", test_github_actions_timeout),
        ("Resume Capability", test_resume_capability),
        ("Batch Processing", test_batch_processing),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All timeout fixes are properly implemented!")
        print("\n🚀 Ready for production deployment with:")
        print("   • 5-minute individual command timeouts")
        print("   • 8-hour GitHub Actions timeout")
        print("   • Batch processing with 30s pauses")
        print("   • Enhanced error handling and retries")
        print("   • Resume capability for interrupted runs")
    else:
        print("⚠️  Some timeout fixes need attention before production deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
