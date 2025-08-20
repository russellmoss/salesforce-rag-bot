#!/usr/bin/env python3
"""
Test script for CLI-based metadata functions
"""

import sys
import os
import json
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pipeline.build_schema_library_end_to_end import (
    get_profiles_metadata_via_cli,
    get_permission_sets_metadata_via_cli,
    get_detailed_field_permissions_via_cli,
    resolve_sf
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_cli_metadata_functions():
    """Test the CLI-based metadata functions."""
    
    # Set up Salesforce CLI path
    sf_bin = resolve_sf()
    if not sf_bin:
        logger.error("Salesforce CLI not found!")
        return False
    
    # Set the SF_BIN globally
    import pipeline.build_schema_library_end_to_end as build_module
    build_module.SF_BIN = sf_bin
    
    org_alias = "DEVNEW"
    
    logger.info("Testing CLI-based metadata functions...")
    
    try:
        # Test 1: Get profiles metadata
        logger.info("Test 1: Getting profiles metadata...")
        profiles_metadata = get_profiles_metadata_via_cli(org_alias)
        logger.info(f"✅ Retrieved {len(profiles_metadata)} profiles")
        
        # Show sample profile data
        if profiles_metadata:
            sample_profile = profiles_metadata[0]
            logger.info(f"Sample profile: {sample_profile['name']}")
            logger.info(f"  - Source: {sample_profile.get('source', 'unknown')}")
            logger.info(f"  - Has metadata content: {'metadata_content' in sample_profile}")
        
        # Test 2: Get permission sets metadata
        logger.info("\nTest 2: Getting permission sets metadata...")
        permission_sets_metadata = get_permission_sets_metadata_via_cli(org_alias)
        logger.info(f"✅ Retrieved {len(permission_sets_metadata)} permission sets")
        
        # Show sample permission set data
        if permission_sets_metadata:
            sample_ps = permission_sets_metadata[0]
            logger.info(f"Sample permission set: {sample_ps['name']}")
            logger.info(f"  - Source: {sample_ps.get('source', 'unknown')}")
            logger.info(f"  - Has metadata content: {'metadata_content' in sample_ps}")
        
        # Test 3: Get detailed field permissions for a few objects
        logger.info("\nTest 3: Getting detailed field permissions...")
        test_objects = ["Account", "Contact", "Opportunity"]
        field_permissions = get_detailed_field_permissions_via_cli(org_alias, test_objects)
        
        total_field_perms = sum(len(obj_data.get("field_permissions", [])) for obj_data in field_permissions.values())
        logger.info(f"✅ Retrieved {total_field_perms} field permissions across {len(field_permissions)} objects")
        
        # Show sample field permissions
        for obj_name, obj_data in field_permissions.items():
            field_perms = obj_data.get("field_permissions", [])
            logger.info(f"  - {obj_name}: {len(field_perms)} field permissions")
            if field_perms:
                sample_perm = field_perms[0]
                logger.info(f"    Sample: {sample_perm['field']} - Read: {sample_perm['read']}, Edit: {sample_perm['edit']}")
        
        logger.info("\n🎉 All CLI metadata tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_cli_metadata_functions()
    sys.exit(0 if success else 1)
