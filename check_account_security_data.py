#!/usr/bin/env python3
import json

with open('output/security.json', 'r') as f:
    security_data = json.load(f)
    
if 'Account' in security_data:
    account_data = security_data['Account']
    print("ACCOUNT SECURITY DATA FOUND!")
    print("=" * 50)
    print(f"Account data keys: {list(account_data.keys())}")
    
    for key, value in account_data.items():
        if isinstance(value, list):
            print(f"\n{key}: {len(value)} items")
            if value and len(value) > 0:
                print(f"  Sample: {value[0]}")
        elif isinstance(value, dict):
            print(f"\n{key}: {len(value)} items")
            if value:
                sample_key = list(value.keys())[0]
                print(f"  Sample key: {sample_key}")
                print(f"  Sample value: {value[sample_key]}")
        else:
            print(f"\n{key}: {value}")
else:
    print("❌ Account not found in security.json")
