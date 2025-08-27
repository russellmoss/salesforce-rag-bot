#!/usr/bin/env python3
"""
Check if Contact security data exists in the output files.
"""

import json
import os
from pathlib import Path

def check_contact_security_data():
    """Check if Contact security data exists in the output files."""
    
    # Check output directory
    output_dir = Path("./output")
    if not output_dir.exists():
        print("❌ Output directory not found!")
        return
    
    # Check for security.json file
    security_file = output_dir / "security.json"
    if not security_file.exists():
        print("❌ Security data file not found!")
        return
    
    try:
        with open(security_file, 'r') as f:
            security_data = json.load(f)
        
        print("SECURITY DATA FOUND!")
        print("=" * 50)
        print(f"Total objects with security data: {len(security_data)}")
        
        # Check for Contact security data
        contact_data = security_data.get('Contact', None)
        if contact_data:
            print("\n✅ CONTACT SECURITY DATA FOUND!")
            print("=" * 30)
            print(f"Contact data keys: {list(contact_data.keys())}")
            
            # Check field permissions
            field_permissions = contact_data.get('field_permissions', [])
            print(f"\nfield_permissions: {len(field_permissions)} items")
            if field_permissions:
                sample = field_permissions[0]
                print(f"  Sample: {sample}")
            
            # Check object permissions
            object_permissions = contact_data.get('object_permissions', {})
            print(f"\nobject_permissions: {len(object_permissions)} items")
            if object_permissions:
                sample_key = list(object_permissions.keys())[0]
                sample_value = object_permissions[sample_key]
                print(f"  Sample key: {sample_key}")
                print(f"  Sample value: {sample_value}")
            
            # Check profiles
            profiles = contact_data.get('profiles', [])
            print(f"\nprofiles: {len(profiles)} items")
            
            # Check permission sets
            permission_sets = contact_data.get('permission_sets', [])
            print(f"\npermission_sets: {len(permission_sets)} items")
            
        else:
            print("\n❌ NO CONTACT SECURITY DATA FOUND!")
            print("=" * 35)
        
        # Show what objects do have security data
        object_names = list(security_data.keys())
        print(f"Objects with security data: {len(object_names)}")
        
        # Show first 10 objects
        print("First 10 objects with security data:")
        for i, obj_name in enumerate(object_names[:10]):
            obj_data = security_data[obj_name]
            field_perms = len(obj_data.get('field_permissions', []))
            print(f"  {i+1}. {obj_name}: {field_perms} field permissions")
        
        if len(object_names) > 10:
            print(f"  ... and {len(object_names) - 10} more objects")
        
        # Check for Contact in object names
        contact_related = [name for name in object_names if 'contact' in name.lower()]
        if contact_related:
            print(f"\n🔍 Contact-related objects found: {len(contact_related)}")
            for obj_name in contact_related:
                print(f"  - {obj_name}")
        
    except Exception as e:
        print(f"❌ Error reading security data: {e}")

if __name__ == "__main__":
    check_contact_security_data()
