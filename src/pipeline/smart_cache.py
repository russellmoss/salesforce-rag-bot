#!/usr/bin/env python3
"""
Smart caching system for Salesforce schema pipeline.

This module provides intelligent caching for API calls, with automatic
invalidation, compression, and performance monitoring.
"""

import json
import gzip
import hashlib
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import pickle
import shutil

logger = logging.getLogger(__name__)

class SmartCache:
    """
    Intelligent caching system with automatic invalidation and compression.
    
    Features:
    - Automatic cache invalidation based on age
    - Compression for large data
    - Cache hit/miss statistics
    - Selective cache clearing
    - Performance monitoring
    """
    
    def __init__(self, cache_dir: Path, max_age_hours: int = 24, enable_compression: bool = True):
        self.cache_dir = Path(cache_dir)
        self.max_age_seconds = max_age_hours * 3600
        self.enable_compression = enable_compression
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'compressed_writes': 0,
            'errors': 0
        }
        
        # Create cache directory structure
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / 'compressed').mkdir(exist_ok=True)
        (self.cache_dir / 'stats').mkdir(exist_ok=True)
        
        logger.info(f"SmartCache initialized at {self.cache_dir}")
        logger.info(f"Max cache age: {max_age_hours} hours")
        logger.info(f"Compression: {'enabled' if enable_compression else 'disabled'}")
    
    def _get_cache_key(self, object_name: str, data_type: str, **kwargs) -> str:
        """Generate a unique cache key based on parameters."""
        # Create a hash of all parameters to ensure uniqueness
        key_data = f"{object_name}_{data_type}"
        if kwargs:
            # Sort kwargs for consistent hashing
            sorted_kwargs = sorted(kwargs.items())
            key_data += "_" + "_".join(f"{k}_{v}" for k, v in sorted_kwargs)
        
        # Use SHA256 for collision resistance
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def _get_cache_path(self, cache_key: str, data_type: str) -> Path:
        """Get the cache file path."""
        if self.enable_compression:
            return self.cache_dir / 'compressed' / f"{cache_key}_{data_type}.json.gz"
        else:
            return self.cache_dir / f"{cache_key}_{data_type}.json"
    
    def _is_cache_fresh(self, cache_path: Path) -> bool:
        """Check if cache file is fresh (within max_age_seconds)."""
        if not cache_path.exists():
            return False
        
        try:
            file_age = time.time() - cache_path.stat().st_mtime
            return file_age < self.max_age_seconds
        except OSError:
            return False
    
    def get_cached_data(self, object_name: str, data_type: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get cached data if it exists and is fresh.
        
        Args:
            object_name: Name of the Salesforce object
            data_type: Type of data (e.g., 'automation', 'stats', 'metadata')
            **kwargs: Additional parameters for cache key generation
            
        Returns:
            Cached data dict if fresh, None otherwise
        """
        try:
            cache_key = self._get_cache_key(object_name, data_type, **kwargs)
            cache_path = self._get_cache_path(cache_key, data_type)
            
            if not self._is_cache_fresh(cache_path):
                self.stats['misses'] += 1
                return None
            
            # Load cached data
            if self.enable_compression and cache_path.suffix == '.gz':
                with gzip.open(cache_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            self.stats['hits'] += 1
            logger.debug(f"Cache HIT: {object_name}_{data_type}")
            return data
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.warning(f"Cache read error for {object_name}_{data_type}: {e}")
            return None
    
    def cache_data(self, object_name: str, data_type: str, data: Dict[str, Any], **kwargs):
        """
        Cache data with metadata.
        
        Args:
            object_name: Name of the Salesforce object
            data_type: Type of data being cached
            data: Data to cache
            **kwargs: Additional parameters for cache key generation
        """
        try:
            cache_key = self._get_cache_key(object_name, data_type, **kwargs)
            cache_path = self._get_cache_path(cache_key, data_type)
            
            # Add metadata to cached data
            cached_data = {
                'data': data,
                'metadata': {
                    'cached_at': datetime.now().isoformat(),
                    'object_name': object_name,
                    'data_type': data_type,
                    'cache_key': cache_key,
                    'parameters': kwargs
                }
            }
            
            # Write to cache
            if self.enable_compression and cache_path.suffix == '.gz':
                with gzip.open(cache_path, 'wt', encoding='utf-8') as f:
                    json.dump(cached_data, f, indent=2)
                self.stats['compressed_writes'] += 1
            else:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cached_data, f, indent=2)
            
            self.stats['writes'] += 1
            logger.debug(f"Cache WRITE: {object_name}_{data_type}")
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache write error for {object_name}_{data_type}: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate cache size
        cache_size = 0
        cache_files = 0
        for cache_file in self.cache_dir.rglob('*.json*'):
            try:
                cache_size += cache_file.stat().st_size
                cache_files += 1
            except OSError:
                pass
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'writes': self.stats['writes'],
            'compressed_writes': self.stats['compressed_writes'],
            'errors': self.stats['errors'],
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size_mb': round(cache_size / (1024 * 1024), 2),
            'cache_files': cache_files,
            'cache_dir': str(self.cache_dir)
        }
    
    def clear_cache(self, data_type: Optional[str] = None, older_than_hours: Optional[int] = None):
        """
        Clear cache entries.
        
        Args:
            data_type: If specified, only clear this data type
            older_than_hours: If specified, only clear entries older than this
        """
        cleared_count = 0
        current_time = time.time()
        
        for cache_file in self.cache_dir.rglob('*.json*'):
            try:
                # Check if we should clear this file
                should_clear = True
                
                if data_type and data_type not in cache_file.name:
                    should_clear = False
                
                if older_than_hours:
                    file_age = current_time - cache_file.stat().st_mtime
                    if file_age < (older_than_hours * 3600):
                        should_clear = False
                
                if should_clear:
                    cache_file.unlink()
                    cleared_count += 1
                    
            except OSError as e:
                logger.warning(f"Error clearing cache file {cache_file}: {e}")
        
        logger.info(f"Cleared {cleared_count} cache files")
        return cleared_count
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        cache_files = []
        total_size = 0
        
        for cache_file in self.cache_dir.rglob('*.json*'):
            try:
                stat = cache_file.stat()
                cache_files.append({
                    'name': cache_file.name,
                    'size_bytes': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'age_hours': (time.time() - stat.st_mtime) / 3600
                })
                total_size += stat.st_size
            except OSError:
                pass
        
        return {
            'total_files': len(cache_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'files': sorted(cache_files, key=lambda x: x['age_hours'], reverse=True)[:10]  # Top 10 oldest
        }
    
    def save_stats(self):
        """Save cache statistics to file."""
        stats_file = self.cache_dir / 'stats' / 'cache_stats.json'
        stats_data = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.get_cache_stats(),
            'info': self.get_cache_info()
        }
        
        with open(stats_file, 'w') as f:
            json.dump(stats_data, f, indent=2)
    
    def __str__(self) -> str:
        stats = self.get_cache_stats()
        return f"SmartCache(hits={stats['hits']}, misses={stats['misses']}, hit_rate={stats['hit_rate_percent']}%)"


# Convenience functions for common cache operations
def create_cache_for_pipeline(cache_dir: str = "cache", max_age_hours: int = 24) -> SmartCache:
    """Create a SmartCache instance optimized for the pipeline."""
    return SmartCache(
        cache_dir=Path(cache_dir),
        max_age_hours=max_age_hours,
        enable_compression=True
    )

def get_cached_automation_data(cache: SmartCache, object_name: str) -> Optional[Dict[str, Any]]:
    """Get cached automation data for an object."""
    return cache.get_cached_data(object_name, 'automation')

def cache_automation_data(cache: SmartCache, object_name: str, automation_data: Dict[str, Any]):
    """Cache automation data for an object."""
    cache.cache_data(object_name, 'automation', automation_data)

def get_cached_stats_data(cache: SmartCache, object_name: str, sample_size: int = 100) -> Optional[Dict[str, Any]]:
    """Get cached stats data for an object."""
    return cache.get_cached_data(object_name, 'stats', sample_size=sample_size)

def cache_stats_data(cache: SmartCache, object_name: str, stats_data: Dict[str, Any], sample_size: int = 100):
    """Cache stats data for an object."""
    cache.cache_data(object_name, 'stats', stats_data, sample_size=sample_size)
