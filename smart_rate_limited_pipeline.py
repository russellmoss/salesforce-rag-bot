#!/usr/bin/env python3
"""
Smart Rate-Limited Pipeline - Avoids API calls when rate limited
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pipeline.build_schema_library_end_to_end import resolve_sf, run_sf

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_rate_limit_status_without_api():
    """Check if we're rate limited without making any API calls."""
    
    # Record when you first hit rate limits (update this timestamp)
    RATE_LIMIT_HIT_TIME = "2025-08-20 15:04:00"  # Update this when you hit rate limits
    
    try:
        hit_time = datetime.strptime(RATE_LIMIT_HIT_TIME, "%Y-%m-%d %H:%M:%S")
        current_time = datetime.now()
        elapsed = current_time - hit_time
        
        logger.info(f"Rate limit hit at: {hit_time}")
        logger.info(f"Current time: {current_time}")
        logger.info(f"Time elapsed: {elapsed}")
        
        # Check if this might be a daily limit
        is_same_day = hit_time.date() == current_time.date()
        
        if is_same_day:
            logger.warning("DAILY API LIMIT ACTIVE - No API calls will be made!")
            logger.warning("Daily limits typically reset at midnight (00:00) in your org's timezone.")
            return "DAILY_LIMIT"
        else:
            # Different day - limits should have reset
            logger.info("Different day detected - limits should have reset.")
            return "OK"
            
    except Exception as e:
        logger.error(f"Error parsing time: {e}")
        return "UNKNOWN"

def check_existing_data():
    """Check what data we already have available."""
    output_dir = Path("./output")
    
    existing_data = {
        "schema": False,
        "security": False,
        "automation": False,
        "stats": False,
        "corpus": False
    }
    
    if output_dir.exists():
        if (output_dir / "schema.json").exists():
            existing_data["schema"] = True
            logger.info("Found existing schema.json")
        
        if (output_dir / "security.json").exists():
            existing_data["security"] = True
            logger.info("Found existing security.json")
        
        if (output_dir / "automation.json").exists():
            existing_data["automation"] = True
            logger.info("Found existing automation.json")
        
        if (output_dir / "stats.json").exists():
            existing_data["stats"] = True
            logger.info("Found existing stats.json")
        
        if (output_dir / "corpus.jsonl").exists():
            existing_data["corpus"] = True
            logger.info("Found existing corpus.jsonl")
    
    return existing_data

def analyze_existing_security_data():
    """Analyze existing security data to see what's available."""
    security_file = Path("./output/security.json")
    
    if not security_file.exists():
        logger.info("No existing security.json found")
        return None
    
    try:
        with open(security_file, 'r') as f:
            data = json.load(f)
        
        total_objects = len(data)
        objects_with_permissions = 0
        profiles_found = set()
        permission_sets_found = set()
        
        for obj_name, obj_data in data.items():
            if 'object_permissions' in obj_data:
                objects_with_permissions += 1
                for perm_type, perm_data in obj_data['object_permissions'].items():
                    if perm_type == 'profiles':
                        profiles_found.update(perm_data.keys())
                    elif perm_type == 'permission_sets':
                        permission_sets_found.update(perm_data.keys())
        
        logger.info(f"Existing security data analysis:")
        logger.info(f"- Total objects: {total_objects}")
        logger.info(f"- Objects with permissions: {objects_with_permissions}")
        logger.info(f"- Profiles found: {len(profiles_found)}")
        logger.info(f"- Permission sets found: {len(permission_sets_found)}")
        
        if profiles_found:
            logger.info(f"- Sample profiles: {list(profiles_found)[:5]}")
        
        return {
            "total_objects": total_objects,
            "objects_with_permissions": objects_with_permissions,
            "profiles_count": len(profiles_found),
            "permission_sets_count": len(permission_sets_found)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing security data: {e}")
        return None

def show_recommendations(rate_limit_status, existing_data, security_analysis):
    """Show recommendations based on current status."""
    
    logger.info("=" * 60)
    logger.info("SMART PIPELINE RECOMMENDATIONS")
    logger.info("=" * 60)
    
    if rate_limit_status == "DAILY_LIMIT":
        logger.warning("🚫 DAILY API LIMIT ACTIVE")
        logger.info("")
        logger.info("RECOMMENDED ACTIONS:")
        logger.info("1. Use existing data (if available)")
        logger.info("2. Wait until midnight for limits to reset")
        logger.info("3. Create a new developer org")
        logger.info("4. Use a production org with higher limits")
        logger.info("")
        
        if any(existing_data.values()):
            logger.info("✅ EXISTING DATA AVAILABLE:")
            for data_type, available in existing_data.items():
                if available:
                    logger.info(f"   - {data_type}.json")
            
            logger.info("")
            logger.info("You can use existing data for your RAG bot!")
            logger.info("Run: python src/pipeline/build_schema_library_end_to_end.py --resume --emit-jsonl")
        
        else:
            logger.warning("❌ No existing data found")
            logger.info("You'll need to wait for rate limits to reset or use a different org")
    
    elif rate_limit_status == "OK":
        logger.info("✅ API LIMITS OK - You can run the pipeline")
        logger.info("")
        logger.info("RECOMMENDED COMMAND:")
        logger.info("python src/pipeline/build_schema_library_end_to_end.py \\")
        logger.info("  --org-alias DEVNEW \\")
        logger.info("  --output ./output \\")
        logger.info("  --max-workers 1 \\")
        logger.info("  --cache-dir cache \\")
        logger.info("  --cache-max-age 24 \\")
        logger.info("  --with-security \\")
        logger.info("  --emit-jsonl")
    
    if security_analysis:
        logger.info("")
        logger.info("SECURITY DATA ANALYSIS:")
        logger.info(f"- Objects with permissions: {security_analysis['objects_with_permissions']}/{security_analysis['total_objects']}")
        logger.info(f"- Profiles captured: {security_analysis['profiles_count']}")
        logger.info(f"- Permission sets captured: {security_analysis['permission_sets_count']}")
        
        if security_analysis['profiles_count'] > 0:
            logger.info("✅ You have security data for your RAG bot!")
        else:
            logger.warning("⚠️  Limited security data available")
    
    logger.info("=" * 60)

def main():
    """Main function that checks rate limits and provides recommendations."""
    
    logger.info("🔍 Smart Rate-Limited Pipeline Check")
    logger.info("Checking rate limit status and existing data...")
    
    # Step 1: Check rate limit status (no API calls)
    rate_limit_status = check_rate_limit_status_without_api()
    
    # Step 2: Check existing data
    existing_data = check_existing_data()
    
    # Step 3: Analyze existing security data
    security_analysis = analyze_existing_security_data()
    
    # Step 4: Show recommendations
    show_recommendations(rate_limit_status, existing_data, security_analysis)
    
    # Step 5: Provide next steps
    if rate_limit_status == "DAILY_LIMIT":
        logger.info("")
        logger.info("NEXT STEPS:")
        if any(existing_data.values()):
            logger.info("1. Use existing data: --resume flag")
            logger.info("2. Wait for midnight reset")
            logger.info("3. Create new developer org")
        else:
            logger.info("1. Wait for midnight reset")
            logger.info("2. Create new developer org")
            logger.info("3. Use production org")
    else:
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("1. Run the pipeline with rate limiting")
        logger.info("2. Use --max-workers 1 to reduce API calls")

if __name__ == "__main__":
    main()
