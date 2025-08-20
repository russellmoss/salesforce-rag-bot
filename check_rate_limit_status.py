#!/usr/bin/env python3
"""
Check if Salesforce rate limits have reset
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pipeline.build_schema_library_end_to_end import resolve_sf, run_sf

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_rate_limit_status():
    """Check if rate limits have reset."""
    
    # Set up Salesforce CLI path
    sf_bin = resolve_sf()
    if not sf_bin:
        logger.error("Salesforce CLI not found!")
        return False
    
    # Set the SF_BIN globally
    import pipeline.build_schema_library_end_to_end as build_module
    build_module.SF_BIN = sf_bin
    
    org_alias = "DEVNEW"
    
    logger.info("Checking rate limit status...")
    
    # Test 1: Simple data query (this will tell us if rate limits have reset)
    logger.info("Testing simple data query...")
    try:
        data_query = run_sf(["data", "query", "--query", "SELECT COUNT() FROM User", "--json"], org_alias)
        logger.info("SUCCESS: Rate limits have reset! You can now run the full pipeline.")
        logger.info("The query returned data successfully.")
        return True
    except Exception as e:
        error_str = str(e)
        if "REQUEST_LIMIT_EXCEEDED" in error_str:
            logger.warning("RATE LIMITED: Rate limits are still active.")
            logger.info("Wait another 15-30 minutes and try again.")
            logger.info("You can run this script again to check: python check_rate_limit_status.py")
            return False
        else:
            logger.error(f"UNEXPECTED ERROR: {e}")
            return False

if __name__ == "__main__":
    success = check_rate_limit_status()
    if success:
        logger.info("Ready to run the full pipeline!")
        logger.info("Command: python src/pipeline/build_schema_library_end_to_end.py --org-alias DEVNEW --output ./output --max-workers 1 --cache-dir cache --cache-max-age 24 --with-security --emit-jsonl --resume")
    sys.exit(0 if success else 1)
