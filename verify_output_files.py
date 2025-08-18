#!/usr/bin/env python
"""
Verify that all output files were created correctly.
Checks markdown files, JSONL files, and data quality.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_output_directory(output_dir: str = "output"):
    """Verify the output directory structure and files."""
    logger.info(f"Verifying output directory: {output_dir}")
    
    output_path = Path(output_dir)
    if not output_path.exists():
        logger.error(f"Output directory '{output_dir}' does not exist!")
        return False
    
    # Check for required files
    required_files = [
        "schema.json",
        "corpus.jsonl"
    ]
    
    required_dirs = [
        "md"
    ]
    
    logger.info("Checking required files...")
    for file_name in required_files:
        file_path = output_path / file_name
        if file_path.exists():
            logger.info(f"  ✅ {file_name} exists")
        else:
            logger.error(f"  ❌ {file_name} missing!")
            return False
    
    logger.info("Checking required directories...")
    for dir_name in required_dirs:
        dir_path = output_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            logger.info(f"  ✅ {dir_name}/ directory exists")
        else:
            logger.error(f"  ❌ {dir_name}/ directory missing!")
            return False
    
    return True

def verify_schema_json(output_dir: str = "output"):
    """Verify the schema.json file."""
    logger.info("Verifying schema.json...")
    
    schema_file = Path(output_dir) / "schema.json"
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        objects = schema_data.get('objects', {})
        
        # Handle different formats
        if isinstance(objects, dict):
            object_count = len(objects)
            object_names = list(objects.keys())
        elif isinstance(objects, list):
            object_count = len(objects)
            object_names = [obj.get('name', '') for obj in objects if obj.get('name')]
        else:
            logger.error(f"Unexpected objects format: {type(objects)}")
            return False
        
        logger.info(f"  ✅ Schema contains {object_count} objects")
        
        # Check for key objects
        key_objects = ['Account', 'Contact', 'Lead', 'Opportunity', 'User']
        found_key_objects = [obj for obj in key_objects if obj in object_names]
        logger.info(f"  ✅ Found {len(found_key_objects)}/{len(key_objects)} key objects: {found_key_objects}")
        
        # Sample object structure
        if object_names:
            sample_object = object_names[0]
            logger.info(f"  📝 Sample object: {sample_object}")
            
            if isinstance(objects, dict):
                sample_data = objects[sample_object]
            else:
                sample_data = next((obj for obj in objects if obj.get('name') == sample_object), {})
            
            if 'fields' in sample_data:
                fields = sample_data['fields']
                if isinstance(fields, dict):
                    field_count = len(fields)
                elif isinstance(fields, list):
                    field_count = len(fields)
                else:
                    field_count = 0
                logger.info(f"    - Fields: {field_count}")
            
            if 'description' in sample_data:
                logger.info(f"    - Has description: {bool(sample_data['description'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying schema.json: {e}")
        return False

def verify_markdown_files(output_dir: str = "output"):
    """Verify the markdown files."""
    logger.info("Verifying markdown files...")
    
    md_dir = Path(output_dir) / "md"
    
    if not md_dir.exists():
        logger.error("Markdown directory does not exist!")
        return False
    
    # Count markdown files
    md_files = list(md_dir.glob("*.md"))
    logger.info(f"  ✅ Found {len(md_files)} markdown files")
    
    # Check for key objects
    key_objects = ['Account', 'Contact', 'Lead', 'Opportunity', 'User']
    found_key_files = []
    
    for key_obj in key_objects:
        key_file = md_dir / f"{key_obj}.md"
        if key_file.exists():
            found_key_files.append(key_obj)
            logger.info(f"  ✅ {key_obj}.md exists")
        else:
            logger.warning(f"  ⚠️  {key_obj}.md missing")
    
    logger.info(f"  📊 Found {len(found_key_files)}/{len(key_objects)} key object files")
    
    # Verify content quality of a sample file
    if md_files:
        sample_file = md_files[0]
        logger.info(f"  📝 Checking content quality of {sample_file.name}...")
        
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for required sections
            required_sections = ['# ', '## Fields']
            found_sections = [section for section in required_sections if section in content]
            
            logger.info(f"    - Content length: {len(content)} characters")
            logger.info(f"    - Found {len(found_sections)}/{len(required_sections)} required sections")
            
            # Check for field information
            if '## Fields' in content:
                field_lines = [line for line in content.split('\n') if line.startswith('### ')]
                logger.info(f"    - Contains {len(field_lines)} field definitions")
            
        except Exception as e:
            logger.error(f"Error reading sample markdown file: {e}")
            return False
    
    return True

def verify_jsonl_file(output_dir: str = "output"):
    """Verify the JSONL file."""
    logger.info("Verifying corpus.jsonl...")
    
    jsonl_file = Path(output_dir) / "corpus.jsonl"
    
    if not jsonl_file.exists():
        logger.error("corpus.jsonl file does not exist!")
        return False
    
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        logger.info(f"  ✅ JSONL file contains {len(lines)} lines")
        
        # Parse and verify a few entries
        valid_entries = 0
        sample_entries = []
        
        for i, line in enumerate(lines[:10]):  # Check first 10 entries
            try:
                entry = json.loads(line.strip())
                
                # Check required fields
                required_fields = ['id', 'text', 'metadata']
                if all(field in entry for field in required_fields):
                    valid_entries += 1
                    
                    if len(sample_entries) < 3:  # Keep first 3 as samples
                        sample_entries.append({
                            'id': entry['id'],
                            'object_name': entry['metadata'].get('object_name', 'Unknown'),
                            'fields_count': entry['metadata'].get('fields_count', 0),
                            'text_length': len(entry['text'])
                        })
                
            except json.JSONDecodeError:
                logger.warning(f"  ⚠️  Invalid JSON on line {i+1}")
        
        logger.info(f"  ✅ {valid_entries}/10 sample entries are valid")
        
        # Show sample entries
        for i, entry in enumerate(sample_entries, 1):
            logger.info(f"  📝 Sample {i}: {entry['object_name']} (ID: {entry['id']}, Fields: {entry['fields_count']}, Text: {entry['text_length']} chars)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying JSONL file: {e}")
        return False

def verify_data_consistency(output_dir: str = "output"):
    """Verify data consistency across all files."""
    logger.info("Verifying data consistency...")
    
    # Load schema data
    schema_file = Path(output_dir) / "schema.json"
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        objects = schema_data.get('objects', {})
        if isinstance(objects, dict):
            schema_objects = set(objects.keys())
        elif isinstance(objects, list):
            schema_objects = set(obj.get('name', '') for obj in objects if obj.get('name'))
        else:
            logger.error("Cannot determine schema objects")
            return False
        
        logger.info(f"  📊 Schema contains {len(schema_objects)} objects")
        
        # Check markdown files
        md_dir = Path(output_dir) / "md"
        md_files = set(f.stem for f in md_dir.glob("*.md"))
        logger.info(f"  📊 Markdown directory contains {len(md_files)} files")
        
        # Check JSONL entries
        jsonl_file = Path(output_dir) / "corpus.jsonl"
        jsonl_objects = set()
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    object_name = entry['metadata'].get('object_name', '')
                    if object_name:
                        jsonl_objects.add(object_name)
                except:
                    continue
        
        logger.info(f"  📊 JSONL contains {len(jsonl_objects)} objects")
        
        # Check consistency
        schema_md_diff = schema_objects - md_files
        schema_jsonl_diff = schema_objects - jsonl_objects
        
        if schema_md_diff:
            logger.warning(f"  ⚠️  {len(schema_md_diff)} objects in schema but not in markdown: {list(schema_md_diff)[:5]}")
        else:
            logger.info("  ✅ Schema and markdown files are consistent")
        
        if schema_jsonl_diff:
            logger.warning(f"  ⚠️  {len(schema_jsonl_diff)} objects in schema but not in JSONL: {list(schema_jsonl_diff)[:5]}")
        else:
            logger.info("  ✅ Schema and JSONL are consistent")
        
        return len(schema_md_diff) == 0 and len(schema_jsonl_diff) == 0
        
    except Exception as e:
        logger.error(f"Error verifying data consistency: {e}")
        return False

def main():
    """Run all verification checks."""
    logger.info("Starting comprehensive output file verification...")
    logger.info("=" * 60)
    
    checks = [
        ("Output Directory", verify_output_directory),
        ("Schema JSON", verify_schema_json),
        ("Markdown Files", verify_markdown_files),
        ("JSONL File", verify_jsonl_file),
        ("Data Consistency", verify_data_consistency)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        logger.info(f"\n{'='*20} {check_name} {'='*20}")
        try:
            success = check_func()
            results[check_name] = "✅ PASSED" if success else "❌ FAILED"
        except Exception as e:
            logger.error(f"Check '{check_name}' failed with exception: {e}")
            results[check_name] = "❌ FAILED"
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results.items():
        logger.info(f"{check_name}: {result}")
        if "PASSED" in result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("🎉 ALL CHECKS PASSED! Your output files are perfect!")
    else:
        logger.warning(f"⚠️  {total - passed} check(s) failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    main()
