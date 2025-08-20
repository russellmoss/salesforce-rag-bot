# Simple Metadata API Setup (Using Existing Salesforce CLI)

## Quick Setup for Developer Accounts

Since you already have Salesforce CLI working with your DEVNEW org, we can use a much simpler approach!

## Step 1: Verify Current Setup

Your current setup is already working:
```bash
# This works - you already have access!
sf org list
sf data query -q "SELECT Id, Name FROM Profile LIMIT 1" -o DEVNEW --json
```

## Step 2: Test Metadata API Access

Let's test if you can access metadata directly:

```bash
# Test listing profiles metadata
sf org list metadata --metadata-type Profile -o DEVNEW

# Test listing permission sets metadata  
sf org list metadata --metadata-type PermissionSet -o DEVNEW

# Test retrieving a specific profile
sf org retrieve metadata --metadata-type Profile --metadata-names "System Administrator" -o DEVNEW
```

## Step 3: Enhanced Pipeline with Metadata API

I'll create an enhanced version of the pipeline that uses the Metadata API through Salesforce CLI. This approach:

✅ **No additional setup required** - uses your existing CLI authentication  
✅ **More comprehensive data** - gets full profile and permission set metadata  
✅ **Better field permissions** - retrieves detailed field-level security  
✅ **Detailed CRUD permissions** - gets actual permission configurations  

## Step 4: Create Enhanced Metadata Functions

Let me create the enhanced functions that will use the Metadata API:

```python
def get_profiles_metadata_via_cli(org: str) -> List[dict]:
    """Get profiles metadata using Salesforce CLI Metadata API."""
    try:
        # List all profiles
        result = run_sf(["org", "list", "metadata", "--metadata-type", "Profile", "--json"], org)
        profiles_list = json.loads(result)
        
        profiles_metadata = []
        for profile in profiles_list.get('result', []):
            try:
                # Retrieve profile metadata
                profile_name = profile['fullName']
                profile_result = run_sf([
                    "org", "retrieve", "metadata", 
                    "--metadata-type", "Profile", 
                    "--metadata-names", profile_name, 
                    "--json"
                ], org)
                
                profile_data = json.loads(profile_result)
                if profile_data.get('result', {}).get('inboundFiles'):
                    profiles_metadata.append({
                        'name': profile_name,
                        'metadata': profile_data['result']['inboundFiles'][0]
                    })
                    
            except Exception as e:
                logger.warning(f"Could not retrieve metadata for profile {profile_name}: {e}")
                continue
        
        return profiles_metadata
        
    except Exception as e:
        logger.error(f"Error getting profiles metadata: {e}")
        return []

def get_permission_sets_metadata_via_cli(org: str) -> List[dict]:
    """Get permission sets metadata using Salesforce CLI Metadata API."""
    try:
        # List all permission sets
        result = run_sf(["org", "list", "metadata", "--metadata-type", "PermissionSet", "--json"], org)
        permission_sets_list = json.loads(result)
        
        permission_sets_metadata = []
        for ps in permission_sets_list.get('result', []):
            try:
                # Retrieve permission set metadata
                ps_name = ps['fullName']
                ps_result = run_sf([
                    "org", "retrieve", "metadata", 
                    "--metadata-type", "PermissionSet", 
                    "--metadata-names", ps_name, 
                    "--json"
                ], org)
                
                ps_data = json.loads(ps_result)
                if ps_data.get('result', {}).get('inboundFiles'):
                    permission_sets_metadata.append({
                        'name': ps_name,
                        'metadata': ps_data['result']['inboundFiles'][0]
                    })
                    
            except Exception as e:
                logger.warning(f"Could not retrieve metadata for permission set {ps_name}: {e}")
                continue
        
        return permission_sets_metadata
        
    except Exception as e:
        logger.error(f"Error getting permission sets metadata: {e}")
        return []
```

## Step 5: Test the Enhanced Approach

Let's test this approach:

```bash
# Test the metadata API access
python -c "
import subprocess
import json

# Test listing profiles
result = subprocess.run(['sf', 'org', 'list', 'metadata', '--metadata-type', 'Profile', '--json', '-o', 'DEVNEW'], 
                       capture_output=True, text=True)
print('Profiles metadata available:', len(json.loads(result.stdout).get('result', [])))

# Test listing permission sets  
result = subprocess.run(['sf', 'org', 'list', 'metadata', '--metadata-type', 'PermissionSet', '--json', '-o', 'DEVNEW'], 
                       capture_output=True, text=True)
print('Permission sets metadata available:', len(json.loads(result.stdout).get('result', [])))
"
```

## Benefits of This Approach

1. **No Additional Authentication** - Uses your existing CLI setup
2. **Comprehensive Data** - Gets full XML metadata files with all permissions
3. **Field-Level Security** - Detailed field permissions for each profile/permission set
4. **Object Permissions** - Complete CRUD permissions for all objects
5. **Custom Permissions** - Access to custom permissions and settings

## Next Steps

Once we confirm this works, I'll enhance the pipeline to:

1. **Retrieve full metadata** for all profiles and permission sets
2. **Parse XML metadata** to extract detailed permissions
3. **Map field-level security** for all objects and fields
4. **Extract CRUD permissions** with full detail
5. **Integrate with existing pipeline** for comprehensive security data

This approach should give us much more detailed security information than the current API limitations allow!
