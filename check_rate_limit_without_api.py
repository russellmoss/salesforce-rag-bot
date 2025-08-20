#!/usr/bin/env python3
"""
Check rate limit status without making API calls
"""

import sys
import os
import time
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_rate_limit_without_api():
    """Check rate limit status based on time elapsed (no API calls)."""
    
    # Record when you first hit rate limits (update this timestamp)
    # Format: YYYY-MM-DD HH:MM:SS
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
            logger.warning("This appears to be a DAILY API limit, not hourly!")
            logger.warning("Daily limits typically reset at midnight (00:00) in your org's timezone.")
            logger.info("")
            logger.info("POSSIBLE SOLUTIONS:")
            logger.info("1. Wait until midnight (00:00) in your org's timezone")
            logger.info("2. Use a different Salesforce org with higher limits")
            logger.info("3. Use production org (if available) with higher limits")
            logger.info("4. Check if you can increase API limits in org settings")
            logger.info("")
            logger.info("To check your org's timezone:")
            logger.info("sf org display -o DEVNEW --json")
            return "DAILY_LIMIT"
        else:
            # Different day - limits should have reset
            logger.info("Different day detected - limits should have reset.")
            logger.info("You can try running the pipeline.")
            return True
            
    except Exception as e:
        logger.error(f"Error parsing time: {e}")
        return False

def show_daily_limit_solutions():
    """Show solutions for daily API limits."""
    logger.info("=" * 60)
    logger.info("DAILY API LIMIT SOLUTIONS")
    logger.info("=" * 60)
    logger.info("1. WAIT UNTIL MIDNIGHT: Daily limits reset at 00:00 org time")
    logger.info("2. USE DIFFERENT ORG: Try another Salesforce org")
    logger.info("3. CHECK ORG SETTINGS: Look for API limit configurations")
    logger.info("4. USE PRODUCTION: Production orgs have higher limits")
    logger.info("5. REDUCE API CALLS: Use --max-workers 1 and caching")
    logger.info("")
    logger.info("IMMEDIATE OPTIONS:")
    logger.info("- Wait until tomorrow (midnight)")
    logger.info("- Create a new developer org")
    logger.info("- Use existing cached data if available")
    logger.info("=" * 60)

if __name__ == "__main__":
    status = check_rate_limit_without_api()
    
    if status == True:
        logger.info("Ready to run the pipeline!")
        logger.info("Command: python src/pipeline/build_schema_library_end_to_end.py --org-alias DEVNEW --output ./output --max-workers 1 --cache-dir cache --cache-max-age 24 --with-security --emit-jsonl --resume")
    elif status == "DAILY_LIMIT":
        show_daily_limit_solutions()
    else:
        logger.info("Wait longer or try a different approach.")
    
    sys.exit(0 if status == True else 1)
