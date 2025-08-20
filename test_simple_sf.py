#!/usr/bin/env python3
"""
Simple test to verify SF CLI connection
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pipeline.build_schema_library_end_to_end import resolve_sf, run_sf

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_sf():
    """Test simple SF CLI commands."""
    
    # Set up Salesforce CLI path
    sf_bin = resolve_sf()
    if not sf_bin:
        logger.error("Salesforce CLI not found!")
        return False
    
    # Set the SF_BIN globally
    import pipeline.build_schema_library_end_to_end as build_module
    build_module.SF_BIN = sf_bin
    
    org_alias = "DEVNEW"
    
    logger.info("Testing simple SF CLI commands...")
    
    try:
        # Test 1: Simple org info command
        logger.info("Test 1: Getting org info...")
        result = run_sf(["org", "display", "--json"], org_alias)
        logger.info("✅ Org info command successful")
        
        # Test 2: Simple data query
        logger.info("Test 2: Simple data query...")
        result = run_sf(["data", "query", "--query", "SELECT COUNT() FROM User", "--json"], org_alias)
        logger.info("✅ Data query command successful")
        
        logger.info("🎉 All simple SF CLI tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_sf()
    sys.exit(0 if success else 1)
