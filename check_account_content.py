#!/usr/bin/env python3
import json

with open('output/corpus.jsonl', 'r') as f:
    for line in f:
        if line.strip():
            doc = json.loads(line)
            if 'security_Account' in doc.get('id', ''):
                print("ACCOUNT SECURITY DOCUMENT FOUND!")
                print("=" * 50)
                print(f"ID: {doc.get('id')}")
                print(f"Type: {doc.get('metadata', {}).get('type')}")
                print(f"Object: {doc.get('metadata', {}).get('object_name')}")
                print("\nCONTENT:")
                print(doc.get('text', ''))
                print("=" * 50)
                break
