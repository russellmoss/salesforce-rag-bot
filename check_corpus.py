#!/usr/bin/env python3
import json

count = 0
account_found = False
account_security_found = False

with open('output/corpus.jsonl', 'r') as f:
    for line in f:
        if line.strip():
            count += 1
            try:
                doc = json.loads(line)
                doc_id = doc.get('id', 'unknown')
                print(f'Line {count}: {doc_id}')
                
                if 'Account' in doc_id:
                    if 'security_Account' in doc_id:
                        account_security_found = True
                        print(f'  *** FOUND ACCOUNT SECURITY DOCUMENT ***')
                        print(f'  Content preview: {doc.get("text", "")[:200]}...')
                    else:
                        account_found = True
            except:
                print(f'Line {count}: ERROR parsing JSON')

print(f'\nTotal lines: {count}')
print(f'Account object found: {account_found}')
print(f'Account security found: {account_security_found}')
