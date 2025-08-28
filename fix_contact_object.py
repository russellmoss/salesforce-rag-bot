#!/usr/bin/env python3
"""
Targeted script to fetch Contact object and add it to existing schema
"""

import json
import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_sf_command(args, org_alias="NEWORG"):
    """Run Salesforce CLI command"""
    try:
        # Get the script's directory and navigate to parent
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)  # Go to parent of salesforce-rag-bot
        
        print(f"🔍 Changing to directory: {parent_dir}")
        original_dir = os.getcwd()
        os.chdir(parent_dir)
        
        # Use a batch file approach to run the command
        batch_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_sf_command.bat")
        
        # Build the command string for the batch file
        cmd_string = f'"{batch_file}"'
        print(f"🔍 Running command: {cmd_string}")
        
        # Run the batch file
        result = subprocess.run(cmd_string, shell=True, capture_output=True, text=True, check=True)
        
        # Change back to original directory
        os.chdir(original_dir)
        
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Salesforce CLI error: {e}")
        print(f"Command: {cmd_string}")
        print(f"Error: {e.stderr}")
        # Change back to original directory even on error
        try:
            os.chdir(original_dir)
        except:
            pass
        return None
    except Exception as e:
        print(f"❌ Error running Salesforce CLI: {e}")
        # Change back to original directory even on error
        try:
            os.chdir(original_dir)
        except:
            pass
        return None

def fetch_contact_object():
    """Fetch Contact object metadata using Salesforce CLI"""
    print("🔍 Fetching Contact object metadata...")
    
    try:
        # Get Contact entity definition using Tooling API
        entity_result = run_sf_command([
            "data", "query", 
            "--query", "SELECT QualifiedApiName, Label FROM EntityDefinition WHERE QualifiedApiName = 'Contact'", 
            "--json",
            "--use-tooling-api"
        ])
        
        if not entity_result:
            return None
            
        entity_data = json.loads(entity_result)["result"]["records"][0]
        
        # Get Contact fields using Tooling API
        fields_result = run_sf_command([
            "data", "query", 
            "--query", "SELECT QualifiedApiName, Label, DataType, Description FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = 'Contact' ORDER BY QualifiedApiName", 
            "--json",
            "--use-tooling-api"
        ])
        
        if not fields_result:
            return None
            
        fields_data = json.loads(fields_result)["result"]["records"]
        
        # Format it like the existing schema
        contact_object = {
            "name": "Contact",
            "label": entity_data["Label"],
            "description": "",
            "fields": []
        }
        
        # Process fields
        for field in fields_data:
            field_info = {
                "name": field.get("QualifiedApiName", ""),
                "label": field.get("Label", ""),
                "type": field.get("DataType", ""),
                "description": field.get("Description", ""),
                "required": False,  # Default value since field not available
                "unique": False,    # Default value since field not available
                "external_id": False # Default value since field not available
            }
            contact_object["fields"].append(field_info)
        
        print(f"✅ Contact object fetched with {len(contact_object['fields'])} fields")
        return contact_object
        
    except Exception as e:
        print(f"❌ Error fetching Contact object: {e}")
        return None

def add_contact_to_schema(contact_object):
    """Add Contact object to existing schema.json"""
    schema_path = "output/schema.json"
    
    try:
        # Load existing schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Check if Contact already exists in objects array
        objects = schema.get("objects", [])
        contact_exists = any(obj.get("name") == "Contact" for obj in objects)
        
        if not contact_exists:
            # Add Contact object to objects array
            objects.append(contact_object)
            # Sort objects by name to maintain order
            objects.sort(key=lambda x: x.get("name", ""))
            schema["objects"] = objects
            
            # Save updated schema
            with open(schema_path, 'w') as f:
                json.dump(schema, f, indent=2)
            
            print(f"✅ Contact object added to {schema_path}")
        else:
            print(f"ℹ️ Contact object already exists in {schema_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        return False

def add_contact_to_sobject_list():
    """Add Contact to sobject-list.json"""
    sobject_path = "output/sobject-list.json"
    
    try:
        # Load existing sobject list
        with open(sobject_path, 'r') as f:
            sobject_data = json.load(f)
        
        # Add Contact if not already present
        if "Contact" not in sobject_data["result"]:
            sobject_data["result"].append("Contact")
            sobject_data["result"].sort()  # Keep alphabetical order
            
            # Save updated list
            with open(sobject_path, 'w') as f:
                json.dump(sobject_data, f, indent=2)
            
            print(f"✅ Contact added to {sobject_path}")
        else:
            print(f"ℹ️ Contact already in {sobject_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating sobject list: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Fixing Contact object in schema...")
    
    # Fetch Contact object
    contact_object = fetch_contact_object()
    if not contact_object:
        return False
    
    # Add to schema
    if not add_contact_to_schema(contact_object):
        return False
    
    # Add to sobject list
    if not add_contact_to_sobject_list():
        return False
    
    print("✅ Contact object successfully added to schema!")
    print("📝 Next step: Run corpus generation with new chunking logic")
    
    return True

if __name__ == "__main__":
    main()
