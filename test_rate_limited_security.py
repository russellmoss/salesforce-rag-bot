#!/usr/bin/env python3
"""
Test rate-limited security collection
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pipeline.build_schema_library_end_to_end import resolve_sf, get_profiles_metadata_via_cli

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rate_limited_security():
    """Test the rate-limited security collection."""
    
    # Set up Salesforce CLI path
    sf_bin = resolve_sf()
    if not sf_bin:
        logger.error("Salesforce CLI not found!")
        return False
    
    # Set the SF_BIN globally
    import pipeline.build_schema_library_end_to_end as build_module
    build_module.SF_BIN = sf_bin
    
    org_alias = "DEVNEW"
    
    logger.info("Testing rate-limited security collection...")
    logger.info("This will test with proper rate limiting (500ms delays between API calls)")
    
    try:
        # Test profiles collection with rate limiting
        logger.info("Testing profiles metadata collection...")
        profiles_metadata = get_profiles_metadata_via_cli(org_alias)
        
        logger.info(f"Successfully collected metadata for {len(profiles_metadata)} profiles")
        
        # Show sample data
        if profiles_metadata:
            sample_profile = profiles_metadata[0]
            logger.info(f"Sample profile: {sample_profile.get('name', 'Unknown')}")
            logger.info(f"Has object permissions: {'object_permissions' in sample_profile}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing rate-limited security collection: {e}")
        return False

if __name__ == "__main__":
    success = test_rate_limited_security()
    if success:
        logger.info("Rate-limited security collection test completed successfully!")
        logger.info("You can now run the full pipeline with proper rate limiting.")
    sys.exit(0 if success else 1)
