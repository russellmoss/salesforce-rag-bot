#!/usr/bin/env python3
"""
Clean up schema.json by removing the incorrect Contact object from the root level
and adding it to the objects array properly.
"""
import json
import os

def cleanup_and_fix_contact():
    """Remove incorrect Contact object and add it to objects array"""
    schema_path = "output/schema.json"
    print("🧹 Cleaning up schema.json...")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Check if Contact exists at root level
        contact_at_root = None
        if "Contact" in schema:
            contact_at_root = schema["Contact"]
            del schema["Contact"]
            print(f"❌ Removed incorrect Contact object from root level")
        
        # Check if Contact exists in objects array
        objects = schema.get('objects', [])
        contact_in_objects = any(obj.get('name') == 'Contact' for obj in objects)
        
        if not contact_in_objects and contact_at_root:
            # Add Contact to objects array
            objects.append(contact_at_root)
            # Sort objects by name
            objects.sort(key=lambda x: x.get("name", ""))
            schema["objects"] = objects
            print(f"✅ Added Contact object to objects array")
        elif contact_in_objects:
            print(f"✅ Contact object already exists in objects array")
        else:
            print(f"❌ No Contact object found to add")
        
        # Save updated schema
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
        
        print(f"✅ Schema cleaned and saved to {schema_path}")
        
        # Verify Contact is now in objects array
        contact_found = False
        for obj in objects:
            if obj.get('name') == 'Contact':
                contact_found = True
                print(f"✅ Found Contact object in objects array")
                print(f"   Label: {obj.get('label', 'Unknown')}")
                print(f"   Fields: {len(obj.get('fields', []))}")
                break
        
        if not contact_found:
            print(f"❌ Warning: Contact object not found in objects array!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning schema: {e}")
        return False

if __name__ == "__main__":
    cleanup_and_fix_contact()

