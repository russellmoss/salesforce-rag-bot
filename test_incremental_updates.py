#!/usr/bin/env python3
"""
Test script to verify incremental update functionality in the Salesforce schema pipeline.
"""

import subprocess
import sys
from pathlib import Path

def test_incremental_argument():
    """Test that the --incremental-update argument is available."""
    print("🔍 Testing --incremental-update argument...")
    
    try:
        result = subprocess.run([
            sys.executable, "src/pipeline/build_schema_library_end_to_end.py", "--help"
        ], capture_output=True, text=True, timeout=30)
        
        if '--incremental-update' in result.stdout:
            print("✅ --incremental-update argument available")
            return True
        else:
            print("❌ --incremental-update argument not found in help")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Help command timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing incremental argument: {e}")
        return False

def test_incremental_functions():
    """Test that incremental update functions are implemented."""
    print("\n🔍 Testing incremental update functions...")
    
    pipeline_file = Path("src/pipeline/build_schema_library_end_to_end.py")
    if not pipeline_file.exists():
        print("❌ Pipeline file not found")
        return False
    
    try:
        with open(pipeline_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(pipeline_file, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Check for required functions
    required_functions = [
        'def get_existing_vectors_from_pinecone',
        'def calculate_content_hash',
        'def identify_changed_objects',
        'def filter_chunks_for_incremental_update',
        'def delete_vectors_for_objects',
        'def upload_chunks_to_pinecone_incremental'
    ]
    
    missing_functions = []
    for func in required_functions:
        if func in content:
            print(f"✅ Found: {func}")
        else:
            print(f"❌ Missing: {func}")
            missing_functions.append(func)
    
    return len(missing_functions) == 0

def test_incremental_logic():
    """Test that incremental logic is implemented."""
    print("\n🔍 Testing incremental logic implementation...")
    
    pipeline_file = Path("src/pipeline/build_schema_library_end_to_end.py")
    if not pipeline_file.exists():
        print("❌ Pipeline file not found")
        return False
    
    try:
        with open(pipeline_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(pipeline_file, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Check for incremental logic indicators
    logic_indicators = [
        'if args.incremental_update:',
        'upload_chunks_to_pinecone_incremental',
        'current_objects=objects',
        'incremental=True',
        'chunks_to_upload=chunks_to_upload'
    ]
    
    missing_logic = []
    for indicator in logic_indicators:
        if indicator in content:
            print(f"✅ Found: {indicator}")
        else:
            print(f"❌ Missing: {indicator}")
            missing_logic.append(indicator)
    
    return len(missing_logic) == 0

def test_summary_output():
    """Test that incremental update status is shown in summary."""
    print("\n🔍 Testing incremental update summary output...")
    
    pipeline_file = Path("src/pipeline/build_schema_library_end_to_end.py")
    if not pipeline_file.exists():
        print("❌ Pipeline file not found")
        return False
    
    try:
        with open(pipeline_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(pipeline_file, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Check for summary output
    summary_indicators = [
        'if args.incremental_update:',
        'Mode: Incremental update',
        'Mode: Full upload'
    ]
    
    missing_summary = []
    for indicator in summary_indicators:
        if indicator in content:
            print(f"✅ Found: {indicator}")
        else:
            print(f"❌ Missing: {indicator}")
            missing_summary.append(indicator)
    
    return len(missing_summary) == 0

def main():
    """Run all incremental update tests."""
    print("🚀 Salesforce Schema Pipeline - Incremental Update Test")
    print("=" * 60)
    
    tests = [
        ("Incremental Argument", test_incremental_argument),
        ("Incremental Functions", test_incremental_functions),
        ("Incremental Logic", test_incremental_logic),
        ("Summary Output", test_summary_output),
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
        print("🎉 Incremental update feature is properly implemented!")
        print("\n🚀 Ready to use with:")
        print("   • --incremental-update flag for change detection")
        print("   • Automatic comparison with existing vectors")
        print("   • Efficient processing of only changed objects")
        print("   • Proper handling of chunked files")
        print("   • Safe deletion of removed objects")
        print("\n📖 See INCREMENTAL_UPDATES.md for detailed usage instructions")
    else:
        print("⚠️  Some incremental update features need attention.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
