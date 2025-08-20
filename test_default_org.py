#!/usr/bin/env python3
"""
Test setting default org and running query
"""

import sys
import os
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_default_org():
    """Test setting default org and running query."""
    
    org_alias = "DEVNEW"
    
    # Test 1: Set default org first, then run query
    logger.info("Test 1: Set default org first, then run query...")
    
    # Set default org globally
    set_org_cmd = ["sf.cmd", "config", "set", "target-org", org_alias, "--global"]
    logger.info(f"Setting default org: {' '.join(set_org_cmd)}")
    
    try:
        set_result = subprocess.run(set_org_cmd, capture_output=True, text=True, timeout=30)
        logger.info(f"Set org return code: {set_result.returncode}")
        if set_result.returncode == 0:
            logger.info("✅ Default org set successfully!")
        else:
            logger.error(f"❌ Failed to set default org: {set_result.stderr}")
            return
    except Exception as e:
        logger.error(f"Exception setting org: {e}")
        return
    
    # Now run query without org parameter
    query_cmd = ["sf.cmd", "data", "query", "--query", "SELECT COUNT() FROM User", "--json"]
    logger.info(f"Running query: {' '.join(query_cmd)}")
    
    try:
        query_result = subprocess.run(query_cmd, capture_output=True, text=True, timeout=30)
        logger.info(f"Query return code: {query_result.returncode}")
        if query_result.returncode == 0:
            logger.info("✅ Query successful!")
            logger.info(f"STDOUT: {query_result.stdout}")
        else:
            logger.error(f"❌ Query failed: {query_result.stderr}")
            logger.error(f"STDOUT: {query_result.stdout}")
    except Exception as e:
        logger.error(f"Exception running query: {e}")

if __name__ == "__main__":
    test_default_org()
