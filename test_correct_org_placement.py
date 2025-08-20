#!/usr/bin/env python3
"""
Test correct org parameter placement
"""

import sys
import os
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_org_placement():
    """Test different org parameter placements."""
    
    org_alias = "DEVNEW"
    
    # Test 1: Org parameter after data subcommand
    logger.info("Test 1: Org parameter after 'data' subcommand...")
    cmd1 = ["sf.cmd", "data", "-o", org_alias, "query", "--query", "SELECT COUNT() FROM User", "--json"]
    logger.info(f"Command 1: {' '.join(cmd1)}")
    
    try:
        result1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=30)
        logger.info(f"Return code: {result1.returncode}")
        if result1.returncode == 0:
            logger.info("✅ Test 1 successful!")
            logger.info(f"STDOUT: {result1.stdout}")
        else:
            logger.error(f"❌ Test 1 failed: {result1.stderr}")
    except Exception as e:
        logger.error(f"Exception: {e}")
    
    # Test 2: Org parameter after query subcommand
    logger.info("\nTest 2: Org parameter after 'query' subcommand...")
    cmd2 = ["sf.cmd", "data", "query", "-o", org_alias, "--query", "SELECT COUNT() FROM User", "--json"]
    logger.info(f"Command 2: {' '.join(cmd2)}")
    
    try:
        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
        logger.info(f"Return code: {result2.returncode}")
        if result2.returncode == 0:
            logger.info("✅ Test 2 successful!")
            logger.info(f"STDOUT: {result2.stdout}")
        else:
            logger.error(f"❌ Test 2 failed: {result2.stderr}")
    except Exception as e:
        logger.error(f"Exception: {e}")
    
    # Test 3: Org parameter at the very end
    logger.info("\nTest 3: Org parameter at the very end...")
    cmd3 = ["sf.cmd", "data", "query", "--query", "SELECT COUNT() FROM User", "--json", "-o", org_alias]
    logger.info(f"Command 3: {' '.join(cmd3)}")
    
    try:
        result3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=30)
        logger.info(f"Return code: {result3.returncode}")
        if result3.returncode == 0:
            logger.info("✅ Test 3 successful!")
            logger.info(f"STDOUT: {result3.stdout}")
        else:
            logger.error(f"❌ Test 3 failed: {result3.stderr}")
    except Exception as e:
        logger.error(f"Exception: {e}")

if __name__ == "__main__":
    test_org_placement()
