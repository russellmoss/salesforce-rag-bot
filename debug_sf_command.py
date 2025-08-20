#!/usr/bin/env python3
"""
Debug script to see what SF command is being executed
"""

import sys
import os
import subprocess
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pipeline.build_schema_library_end_to_end import resolve_sf

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_sf_command():
    """Debug the SF command execution."""
    
    # Set up Salesforce CLI path
    sf_bin = resolve_sf()
    logger.info(f"SF_BIN resolved to: {sf_bin}")
    
    # Set the SF_BIN globally
    import pipeline.build_schema_library_end_to_end as build_module
    build_module.SF_BIN = sf_bin
    
    org_alias = "DEVNEW"
    
    # Test the exact command that's failing
    test_query = """
    SELECT SobjectType, PermissionsCreate, PermissionsRead, PermissionsEdit, PermissionsDelete
    FROM ObjectPermissions
    WHERE Parent.Profile.Name = 'B2B Reordering Portal Buyer Profile'
    LIMIT 100
    """
    
    # Build the command exactly as it would be built in run_sf
    args = ["data", "query", "--query", test_query, "--json"]
    cmd = [sf_bin] + args
    if org_alias:
        cmd.extend(["-o", org_alias])
    
    logger.info(f"Full command: {' '.join(cmd)}")
    
    # Try to run it manually
    try:
        logger.info("Executing command...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        logger.info(f"Return code: {result.returncode}")
        logger.info(f"STDOUT: {result.stdout}")
        logger.info(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            logger.info("✅ Command executed successfully!")
        else:
            logger.error("❌ Command failed!")
            
    except Exception as e:
        logger.error(f"Exception occurred: {e}")

if __name__ == "__main__":
    debug_sf_command()
