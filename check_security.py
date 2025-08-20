#!/usr/bin/env python3
import json

# Load security data
with open('output/security.json', 'r') as f:
    data = json.load(f)

# Check Contact security data
contact_data = data.get('Contact', {})
profiles = contact_data.get('profiles', [])
permission_sets = contact_data.get('permission_sets', [])
object_permissions = contact_data.get('object_permissions', {})
field_permissions = contact_data.get('field_permissions', [])

print("🔍 Contact Security Data Analysis")
print("=" * 50)
print(f"📊 Profiles with Contact access: {len(profiles)}")
print(f"📊 Permission sets with Contact access: {len(permission_sets)}")
print(f"📊 Object permissions: {len(object_permissions)}")
print(f"📊 Field permissions: {len(field_permissions)}")

print("\n👥 Sample Profiles with Contact Access:")
for profile in profiles[:10]:
    print(f"  - {profile['Name']} ({profile['UserType']})")

print("\n🔧 Sample Permission Sets with Contact Access:")
for ps in permission_sets[:10]:
    print(f"  - {ps.get('Label', 'Unknown')}")

print("\n🔐 Object Permissions:")
if object_permissions:
    for perm_type, value in object_permissions.items():
        print(f"  - {perm_type}: {value}")
else:
    print("  - No object permissions found (ObjectPermissions table may not be accessible)")

print("\n📝 Field Permissions:")
if field_permissions:
    for fp in field_permissions[:5]:
        print(f"  - {fp}")
else:
    print("  - No field permissions found")
