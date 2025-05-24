"""
Memory module for Instability v2

This module provides simple memory management functions for the chatbot,
handling cache storage and retrieval. It's designed to be minimal and
function-based rather than using complex OOP architecture.
"""

import os
import json
import time
from typing import Dict, Any, Optional, List

# Default cache file path
DEFAULT_CACHE_FILE = os.path.expanduser("~/.instability_v2_cache.json")


def load_cache(cache_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the cache from a JSON file

    Args:
        cache_file: Path to the cache file (optional, uses default if not specified)

    Returns:
        Dictionary containing cached data
    """
    file_path = cache_file or DEFAULT_CACHE_FILE

    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                cache = json.load(f)

                # Validate cache structure
                if not isinstance(cache, dict):
                    print(f"Warning: Cache file has invalid format. Creating new cache.")
                    return {
                        "_created": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "_last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
                    }

                return cache
        else:
            # Create a new cache with creation timestamp
            return {
                "_created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "_last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    except Exception as e:
        print(f"Error loading cache: {e}")
        # Return an empty cache with timestamps if there's an error
        return {
            "_created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "_last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "_error": str(e)
        }


def save_cache(cache: Dict[str, Any], cache_file: Optional[str] = None) -> bool:
    """
    Save the cache to a JSON file

    Args:
        cache: Dictionary containing the cache data
        cache_file: Path to the cache file (optional, uses default if not specified)

    Returns:
        True if successful, False otherwise
    """
    file_path = cache_file or DEFAULT_CACHE_FILE

    try:
        # Update the last updated timestamp
        cache["_last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        # Write to the file
        with open(file_path, 'w') as f:
            json.dump(cache, f, indent=2)

        return True
    except Exception as e:
        print(f"Error saving cache: {e}")
        return False


def update_cache(key: str, value: Any, cache: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a specific key in the cache

    Args:
        key: The key to update
        value: The value to set
        cache: The cache dictionary to update

    Returns:
        The updated cache dictionary
    """
    # Update the value
    cache[key] = value

    # Update the last modified timestamp for this key
    cache[f"_{key}_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")

    return cache


def get_cached_value(key: str, cache: Dict[str, Any], default: Any = None) -> Any:
    """
    Get a value from the cache

    Args:
        key: The key to retrieve
        cache: The cache dictionary
        default: Default value to return if key not found

    Returns:
        The cached value or the default
    """
    return cache.get(key, default)


def clear_cache(preserve_keys: Optional[List[str]] = None, cache_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Clear the cache, optionally preserving specific keys

    Args:
        preserve_keys: List of keys to preserve (optional)
        cache_file: Path to the cache file (optional)

    Returns:
        New empty cache dictionary
    """
    # Create a new empty cache
    new_cache = {
        "_created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "_last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "_cleared": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # If keys should be preserved, load the current cache and copy those keys
    if preserve_keys:
        try:
            current_cache = load_cache(cache_file)
            for key in preserve_keys:
                if key in current_cache:
                    new_cache[key] = current_cache[key]
        except Exception as e:
            print(f"Error preserving keys while clearing cache: {e}")

    # Save the new cache
    save_cache(new_cache, cache_file)

    return new_cache


def get_cache_info(cache: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get information about the cache

    Args:
        cache: The cache dictionary

    Returns:
        Dictionary with cache information
    """
    # Count regular keys (not starting with underscore)
    regular_keys = [k for k in cache.keys() if not k.startswith('_')]

    info = {
        "total_entries": len(regular_keys),
        "created": cache.get("_created", "unknown"),
        "last_updated": cache.get("_last_updated", "unknown"),
        "size_bytes": len(json.dumps(cache)),
        "keys": regular_keys
    }

    return info