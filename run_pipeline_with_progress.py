#!/usr/bin/env python3
"""
Wrapper script to run the Salesforce schema pipeline with enhanced progress monitoring.
"""

import subprocess
import sys
import time
import os
from datetime import datetime

def run_pipeline_with_progress():
    """Run the pipeline with enhanced progress monitoring"""
    
    print("🚀 Starting Salesforce Schema Pipeline with Enhanced Progress Monitoring")
    print("=" * 80)
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Pipeline command with all features enabled
    cmd = [
        sys.executable, "-u",  # Force unbuffered output
        "src/pipeline/build_schema_library_end_to_end.py",
        "--org-alias", "DEVNEW",
        "--output", "./output",
        "--with-stats",
        "--with-automation", 
        "--with-metadata",
        "--emit-jsonl",
        "--push-to-pinecone",
        "--clean-output",
        "--throttle-ms", "100",  # Faster processing
        "--retries", "3"
    ]
    
    print("📋 Pipeline Configuration:")
    print(f"  • Org Alias: DEVNEW")
    print(f"  • Output Directory: ./output")
    print(f"  • Features: Stats, Automation, Metadata, JSONL, Pinecone")
    print(f"  • Throttle: 100ms between API calls")
    print(f"  • Retries: 3 per object")
    print("=" * 80)
    
    try:
        # Run the pipeline with real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor progress in real-time
        start_time = time.time()
        last_progress_time = start_time
        
        for line in iter(process.stdout.readline, ''):
            if line:
                # Print the line immediately
                print(line.rstrip())
                
                # Show time elapsed every 5 minutes
                current_time = time.time()
                if current_time - last_progress_time > 300:  # 5 minutes
                    elapsed = current_time - start_time
                    minutes = int(elapsed // 60)
                    seconds = int(elapsed % 60)
                    print(f"⏱️  Time elapsed: {minutes}m {seconds}s")
                    last_progress_time = current_time
                
                # Flush output immediately
                sys.stdout.flush()
        
        # Wait for process to complete
        return_code = process.wait()
        
        # Show final summary
        end_time = time.time()
        total_time = end_time - start_time
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        
        print("=" * 80)
        print(f"✅ Pipeline completed!")
        print(f"⏰ End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total Time: {minutes}m {seconds}s")
        print(f"🔢 Return Code: {return_code}")
        print("=" * 80)
        
        if return_code == 0:
            print("🎉 Success! Your Salesforce schema has been processed and uploaded to Pinecone.")
            print("📁 Check the ./output directory for generated files.")
            print("🤖 You can now run the Streamlit chatbot to test the RAG system!")
        else:
            print("❌ Pipeline failed. Check the output above for errors.")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Pipeline interrupted by user.")
        return 1
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_pipeline_with_progress())
