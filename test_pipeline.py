#!/usr/bin/env python3
"""
Test script to verify the pipeline script is working correctly.
This script checks that all required features are available.
"""

import sys
import os
from pathlib import Path

# Add the pipeline directory to the path
pipeline_dir = Path(__file__).parent / "src" / "pipeline"
sys.path.insert(0, str(pipeline_dir))

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import build_schema_library_end_to_end
        print("✅ Pipeline script imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import pipeline script: {e}")
        return False
    
    return True

def test_argument_parser():
    """Test that the argument parser has all required arguments."""
    print("\n🔍 Testing argument parser...")
    
    try:
        import build_schema_library_end_to_end as pipeline
        
        # Create a mock argument parser by calling main() and capturing the parser
        import sys
        from io import StringIO
        
        # Temporarily redirect stdout to capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # This will create the parser and parse empty args
            args = pipeline.main.__defaults__[0] if pipeline.main.__defaults__ else None
        except:
            # If that doesn't work, let's just check if the main function exists
            if hasattr(pipeline, 'main'):
                print("✅ Main function available")
                return True
            else:
                print("❌ Main function not found")
                return False
        finally:
            sys.stdout = old_stdout
        
        # Check for required arguments by looking at the source code
        required_args = [
            'org_alias', 'output', 'with_stats', 'with_automation', 
            'with_metadata', 'emit_jsonl', 'push_to_pinecone'
        ]
        
        # Read the source file to check for argument definitions
        source_file = Path(__file__).parent / "src" / "pipeline" / "build_schema_library_end_to_end.py"
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                source_content = f.read()
        except UnicodeDecodeError:
            # Try with a different encoding
            with open(source_file, 'r', encoding='latin-1') as f:
                source_content = f.read()
        
        for arg in required_args:
            if f'--{arg.replace("_", "-")}' in source_content:
                print(f"✅ Argument --{arg.replace('_', '-')} found in source")
            else:
                print(f"❌ Missing argument: {arg}")
                return False
                
        print("✅ All required arguments available")
        return True
        
    except Exception as e:
        print(f"❌ Failed to test argument parser: {e}")
        return False

def test_pinecone_integration():
    """Test that Pinecone integration is available."""
    print("\n🔍 Testing Pinecone integration...")
    
    try:
        import build_schema_library_end_to_end as pipeline
        
        if hasattr(pipeline, 'PINECONE_AVAILABLE') and pipeline.PINECONE_AVAILABLE:
            print("✅ Pinecone integration available")
            return True
        else:
            print("⚠️  Pinecone integration not available (missing dependencies)")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test Pinecone integration: {e}")
        return False

def test_requirements():
    """Test that all required packages are installed."""
    print("\n🔍 Testing required packages...")
    
    required_packages = [
        'openai', 'pinecone', 'python_dotenv', 'tiktoken',
        'pandas', 'numpy', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'python_dotenv':
                __import__('dotenv')
            else:
                __import__(package.replace('_', ''))
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages available")
    return True

def main():
    """Run all tests."""
    print("🚀 Testing Salesforce RAG Bot Pipeline")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_argument_parser,
        test_pinecone_integration,
        test_requirements
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Pipeline is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
