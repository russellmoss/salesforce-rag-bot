#!/usr/bin/env python3
"""
Production-ready cached pipeline runner.

This script runs the pipeline with SmartCache integration for maximum
performance and efficiency.
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse

def run_cached_pipeline():
    """Run the complete cached pipeline with production settings."""
    
    # Check if schema file exists
    schema_file = Path("output/schema.json")
    if not schema_file.exists():
        print("❌ Schema file not found: output/schema.json")
        print("   Please run the initial pipeline first to generate the schema.")
        print("   Command: python src/pipeline/build_schema_library_end_to_end.py --org-alias DEVNEW --with-stats")
        return False
    
    # Check if cache directory exists, create if not
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    print("🚀 RUNNING CACHED PIPELINE")
    print("=" * 60)
    print(f"Schema file: {schema_file}")
    print(f"Cache directory: {cache_dir}")
    print(f"Cache status: {'Exists' if cache_dir.exists() else 'Created'}")
    
    # Build the command with all optimizations
    cmd = [
        sys.executable,
        "src/pipeline/build_schema_library_end_to_end.py",
        "--fetch=none",
        "--input=output/schema.json",
        "--with-automation",
        "--with-stats", 
        "--with-metadata",
        "--emit-markdown",
        "--emit-jsonl",
        "--push-to-pinecone",
        "--resume",
        "--stats-resume",
        "--max-workers", "15",
        "--cache-dir", "cache",
        "--cache-max-age", "24",
        "--cache-stats"
    ]
    
    print("\n📋 Command:")
    print(" ".join(cmd))
    
    print("\n⏱️  Expected Performance:")
    print("• First run: ~2-4 hours (with caching)")
    print("• Subsequent runs: ~30-60 minutes (cache hits)")
    print("• Cache hit rate: 80-95% on subsequent runs")
    
    print("\n🎯 Benefits:")
    print("• 10-50x faster on subsequent runs")
    print("• Reduced API calls to Salesforce")
    print("• Automatic cache invalidation (24 hours)")
    print("• Compression reduces disk usage")
    print("• Cache statistics for monitoring")
    
    # Ask for confirmation
    response = input("\n❓ Proceed with cached pipeline? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Pipeline cancelled.")
        return False
    
    print("\n🚀 Starting cached pipeline...")
    print("=" * 60)
    
    try:
        # Run the pipeline
        result = subprocess.run(cmd, check=True)
        print("\n✅ Cached pipeline completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Pipeline failed with exit code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        return False

def show_cache_stats():
    """Show cache statistics."""
    cache_dir = Path("cache")
    if not cache_dir.exists():
        print("❌ Cache directory not found")
        return
    
    stats_file = cache_dir / "stats" / "cache_stats.json"
    if stats_file.exists():
        import json
        with open(stats_file, 'r') as f:
            stats = json.load(f)
        
        print("📊 CACHE STATISTICS")
        print("=" * 40)
        print(f"Timestamp: {stats['timestamp']}")
        print(f"Cache hits: {stats['stats']['hits']}")
        print(f"Cache misses: {stats['stats']['misses']}")
        print(f"Cache writes: {stats['stats']['writes']}")
        print(f"Hit rate: {stats['stats']['hit_rate_percent']}%")
        print(f"Cache size: {stats['stats']['cache_size_mb']} MB")
        print(f"Cache files: {stats['stats']['cache_files']}")
    else:
        print("❌ No cache statistics found")

def clear_cache():
    """Clear the cache."""
    cache_dir = Path("cache")
    if not cache_dir.exists():
        print("❌ Cache directory not found")
        return
    
    response = input("⚠️  Are you sure you want to clear the cache? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Cache clearing cancelled.")
        return
    
    import shutil
    shutil.rmtree(cache_dir)
    print("✅ Cache cleared successfully")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Cached pipeline runner")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--clear", action="store_true", help="Clear cache")
    parser.add_argument("--test", action="store_true", help="Run test mode")
    
    args = parser.parse_args()
    
    if args.stats:
        show_cache_stats()
    elif args.clear:
        clear_cache()
    elif args.test:
        print("🧪 TEST MODE")
        print("=" * 40)
        print("This would run the cached pipeline in test mode.")
        print("Use --stats to see cache statistics.")
        print("Use --clear to clear the cache.")
        print("Run without arguments to start the pipeline.")
    else:
        run_cached_pipeline()

if __name__ == "__main__":
    main()
