#!/usr/bin/env python3
"""
Test script to verify security improvements in the pipeline.
"""

import json
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src" / "pipeline"))

from build_schema_library_end_to_end import (
    get_all_field_level_security_batched,
    get_all_object_permissions_batched,
    resolve_sf,
    run_sf
)

def test_security_functions():
    """Test the improved security functions."""
    
    # Get org alias from environment or use default
    org_alias = os.getenv("SF_ORG_ALIAS", "DEVNEW")
    
    print(f"Testing security functions for org: {org_alias}")
    
    # Initialize SF_BIN
    try:
        sf_bin = resolve_sf()
        print(f"Using Salesforce CLI: {sf_bin}")
        
        # Set the global SF_BIN variable
        import build_schema_library_end_to_end
        build_schema_library_end_to_end.SF_BIN = sf_bin
        
    except Exception as e:
        print(f"Error resolving Salesforce CLI: {e}")
        return
    
    # Test with a few common objects
    test_objects = ["Account", "Contact", "Opportunity", "User"]
    
    print("\n" + "="*60)
    print("TESTING FIELD LEVEL SECURITY")
    print("="*60)
    
    try:
        fls_data = get_all_field_level_security_batched(org_alias, test_objects)
        
        print(f"Field permissions found for {len(fls_data)} objects:")
        for obj_name, obj_data in fls_data.items():
            field_perms = obj_data.get("field_permissions", [])
            print(f"  {obj_name}: {len(field_perms)} field permissions")
            
            # Show sample field permissions
            if field_perms:
                print(f"    Sample permissions:")
                for perm in field_perms[:3]:  # Show first 3
                    print(f"      {perm['field']}: Read={perm['read']}, Edit={perm['edit']} (Source: {perm.get('source', 'unknown')})")
                if len(field_perms) > 3:
                    print(f"      ... and {len(field_perms) - 3} more")
            print()
            
    except Exception as e:
        print(f"Error testing field level security: {e}")
    
    print("\n" + "="*60)
    print("TESTING OBJECT PERMISSIONS")
    print("="*60)
    
    try:
        obj_perms_data = get_all_object_permissions_batched(org_alias, test_objects)
        
        print(f"Object permissions found for {len(obj_perms_data)} objects:")
        for obj_name, obj_data in obj_perms_data.items():
            profiles = obj_data.get("profiles", {})
            permission_sets = obj_data.get("permission_sets", {})
            
            print(f"  {obj_name}:")
            print(f"    Profiles: {len(profiles)}")
            print(f"    Permission Sets: {len(permission_sets)}")
            
            # Show sample profile permissions
            if profiles:
                print(f"    Sample profile permissions:")
                sample_profile = list(profiles.items())[0]
                profile_name, profile_perms = sample_profile
                print(f"      {profile_name}:")
                print(f"        Create: {profile_perms.get('create', False)}")
                print(f"        Read: {profile_perms.get('read', False)}")
                print(f"        Edit: {profile_perms.get('edit', False)}")
                print(f"        Delete: {profile_perms.get('delete', False)}")
                print(f"        Source: {profile_perms.get('source', 'unknown')}")
            print()
            
    except Exception as e:
        print(f"Error testing object permissions: {e}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    # Check if we got any field permissions
    total_field_perms = sum(len(obj_data.get("field_permissions", [])) for obj_data in fls_data.values())
    print(f"Total field permissions found: {total_field_perms}")
    
    # Check if we got detailed CRUD permissions
    total_profiles_with_crud = 0
    total_permission_sets_with_crud = 0
    
    for obj_data in obj_perms_data.values():
        for profile_perms in obj_data.get("profiles", {}).values():
            if any([profile_perms.get('create'), profile_perms.get('read'), 
                   profile_perms.get('edit'), profile_perms.get('delete')]):
                total_profiles_with_crud += 1
                
        for ps_perms in obj_data.get("permission_sets", {}).values():
            if any([ps_perms.get('create'), ps_perms.get('read'), 
                   ps_perms.get('edit'), ps_perms.get('delete')]):
                total_permission_sets_with_crud += 1
    
    print(f"Profiles with detailed CRUD permissions: {total_profiles_with_crud}")
    print(f"Permission sets with detailed CRUD permissions: {total_permission_sets_with_crud}")
    
    if total_field_perms > 0:
        print("✅ Field permissions: SUCCESS")
    else:
        print("❌ Field permissions: FAILED")
        
    if total_profiles_with_crud > 0 or total_permission_sets_with_crud > 0:
        print("✅ CRUD permissions: SUCCESS")
    else:
        print("❌ CRUD permissions: FAILED")

if __name__ == "__main__":
    test_security_functions()
