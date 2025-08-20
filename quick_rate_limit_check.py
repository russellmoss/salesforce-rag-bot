#!/usr/bin/env python3
"""
Quick check for Salesforce rate limit status (no retry logic)
"""

import sys
import os
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def quick_rate_limit_check():
    """Quick check if rate limits have reset (no retry logic)."""
    
    org_alias = "DEVNEW"
    
    logger.info("Quick rate limit check...")
    
    # Simple command without retry logic
    cmd = ["sf.cmd", "data", "query", "--query", "SELECT COUNT() FROM User", "--json", "-o", org_alias]
    
    try:
        logger.info("Testing simple data query...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("SUCCESS: Rate limits have reset! You can now run the full pipeline.")
            logger.info("Ready to run the full pipeline!")
            return True
        else:
            # Check if it's a rate limit error
            if "REQUEST_LIMIT_EXCEEDED" in result.stdout or "REQUEST_LIMIT_EXCEEDED" in result.stderr:
                logger.warning("RATE LIMITED: Rate limits are still active.")
                logger.info("Wait another 15-30 minutes and try again.")
                return False
            else:
                logger.error(f"UNEXPECTED ERROR: {result.stdout}")
                return False
                
    except subprocess.TimeoutExpired:
        logger.error("Command timed out")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = quick_rate_limit_check()
    if success:
        logger.info("Command: python src/pipeline/build_schema_library_end_to_end.py --org-alias DEVNEW --output ./output --max-workers 1 --cache-dir cache --cache-max-age 24 --with-security --emit-jsonl --resume")
    sys.exit(0 if success else 1)
