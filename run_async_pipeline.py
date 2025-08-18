#!/usr/bin/env python3
"""
Production-ready async pipeline runner.

This script runs the async-optimized pipeline with all necessary flags
for complete processing including Pinecone upload.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_async_pipeline():
    """Run the complete async pipeline with production settings."""
    
    # Check if schema file exists
    schema_file = Path("output/schema.json")
    if not schema_file.exists():
        print("❌ Schema file not found: output/schema.json")
        print("   Please run the initial pipeline first to generate the schema.")
        print("   Command: python src/pipeline/build_schema_library_end_to_end.py --org-alias DEVNEW --with-stats")
        return False
    
    print("🚀 RUNNING PRODUCTION ASYNC PIPELINE")
    print("="*60)
    
    # Production command with all optimizations
    cmd = [
        sys.executable,
        "src/pipeline/build_schema_library_end_to_end_async.py",
        "--org-alias", "DEVNEW",
        "--input", "output/schema.json",
        "--output", "output",
        "--max-concurrent", "20",
        "--with-stats",
        "--with-automation", 
        "--with-metadata",
        "--emit-markdown",
        "--emit-jsonl",
        "--push-to-pinecone",
        "--resume",
        "--stats-resume"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print(f"\nExpected performance: ~16 minutes for 1462 objects")
    print(f"Async processing with 20 concurrent operations")
    print(f"Adaptive rate limiting for optimal API usage")
    print("\nStarting pipeline...")
    
    try:
        # Run the async pipeline
        result = subprocess.run(cmd, check=True)
        print("\n✅ Async pipeline completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Async pipeline failed with exit code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        return False

def run_quick_test():
    """Run a quick test of the async pipeline."""
    print("🧪 RUNNING QUICK ASYNC TEST")
    print("="*60)
    
    cmd = [
        sys.executable,
        "src/pipeline/build_schema_library_end_to_end_async.py",
        "--test-only",
        "--org-alias", "DEVNEW",
        "--max-concurrent", "20"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print("\nRunning test with 3 objects...")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ Async test completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Async test failed with exit code: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production async pipeline runner")
    parser.add_argument("--test", action="store_true", help="Run quick test only")
    parser.add_argument("--org-alias", default="DEVNEW", help="Salesforce org alias")
    
    args = parser.parse_args()
    
    # Set org alias in environment
    os.environ["SF_ORG_ALIAS"] = args.org_alias
    
    if args.test:
        success = run_quick_test()
    else:
        success = run_async_pipeline()
    
    if success:
        print("\n🎉 All operations completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Pipeline failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
