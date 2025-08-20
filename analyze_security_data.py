#!/usr/bin/env python3
"""
Analyze existing security data to see what's already collected
"""

import json
import sys

def analyze_security_data():
    """Analyze the security.json file to see what data is available."""
    
    try:
        with open('output/security.json', 'r') as f:
            data = json.load(f)
        
        print(f"Total objects with security data: {len(data)}")
        
        profiles = set()
        permission_sets = set()
        objects_with_permissions = 0
        
        for obj_name, obj_data in data.items():
            if 'object_permissions' in obj_data:
                objects_with_permissions += 1
                for perm_type, perm_data in obj_data['object_permissions'].items():
                    if perm_type == 'profiles':
                        profiles.update(perm_data.keys())
                    elif perm_type == 'permission_sets':
                        permission_sets.update(perm_data.keys())
        
        print(f"Objects with permissions data: {objects_with_permissions}")
        print(f"Profiles found: {len(profiles)}")
        print(f"Permission sets found: {len(permission_sets)}")
        
        if profiles:
            print(f"Sample profiles: {list(profiles)[:5]}")
        
        if permission_sets:
            print(f"Sample permission sets: {list(permission_sets)[:5]}")
        
        # Check for field permissions
        objects_with_field_permissions = 0
        for obj_name, obj_data in data.items():
            if 'field_permissions' in obj_data and obj_data['field_permissions']:
                objects_with_field_permissions += 1
        
        print(f"Objects with field permissions: {objects_with_field_permissions}")
        
        # Check corpus.jsonl
        try:
            with open('output/corpus.jsonl', 'r') as f:
                corpus_lines = f.readlines()
            print(f"Corpus entries: {len(corpus_lines)}")
        except FileNotFoundError:
            print("Corpus file not found")
        
        return True
        
    except Exception as e:
        print(f"Error analyzing security data: {e}")
        return False

if __name__ == "__main__":
    success = analyze_security_data()
    sys.exit(0 if success else 1)
