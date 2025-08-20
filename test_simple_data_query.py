#!/usr/bin/env python3
"""
Test simple data query with org parameter
"""

import sys
import os
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_data_query():
    """Test simple data query with org parameter."""
    
    org_alias = "DEVNEW"
    
    # Test 1: Simple single-line query
    logger.info("Test 1: Simple single-line query...")
    cmd1 = ["sf.cmd", "data", "query", "--query", "SELECT COUNT() FROM User", "--json", "-o", org_alias]
    logger.info(f"Command 1: {' '.join(cmd1)}")
    
    try:
        result1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=30)
        logger.info(f"Return code: {result1.returncode}")
        if result1.returncode == 0:
            logger.info("✅ Simple query successful!")
        else:
            logger.error(f"❌ Simple query failed: {result1.stderr}")
    except Exception as e:
        logger.error(f"Exception: {e}")
    
    # Test 2: Query with org parameter at the end
    logger.info("\nTest 2: Query with org parameter at the end...")
    cmd2 = ["sf.cmd", "data", "query", "--query", "SELECT COUNT() FROM User", "--json", "-o", org_alias]
    logger.info(f"Command 2: {' '.join(cmd2)}")
    
    try:
        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
        logger.info(f"Return code: {result2.returncode}")
        if result2.returncode == 0:
            logger.info("✅ Query with org at end successful!")
        else:
            logger.error(f"❌ Query with org at end failed: {result2.stderr}")
    except Exception as e:
        logger.error(f"Exception: {e}")
    
    # Test 3: Query with org parameter at the beginning
    logger.info("\nTest 3: Query with org parameter at the beginning...")
    cmd3 = ["sf.cmd", "-o", org_alias, "data", "query", "--query", "SELECT COUNT() FROM User", "--json"]
    logger.info(f"Command 3: {' '.join(cmd3)}")
    
    try:
        result3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=30)
        logger.info(f"Return code: {result3.returncode}")
        if result3.returncode == 0:
            logger.info("✅ Query with org at beginning successful!")
        else:
            logger.error(f"❌ Query with org at beginning failed: {result3.stderr}")
    except Exception as e:
        logger.error(f"Exception: {e}")

if __name__ == "__main__":
    test_simple_data_query()
