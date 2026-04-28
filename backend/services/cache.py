"""
Cache layer using SQLite with WAL mode for concurrent access.
Stores company address data with 7-day TTL.
"""
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from config import settings


class Cache:
    """SQLite-based cache with WAL mode for concurrent FastAPI workers."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.cache_db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database with WAL mode and create schema."""
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable WAL mode for concurrent access
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Create cache table with expiration timestamp
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_cache (
                cache_key TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                zip_code TEXT,
                website TEXT,
                result_data TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        
        # Create index on expires_at for efficient cleanup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at 
            ON company_cache(expires_at)
        """)
        
        conn.commit()
        conn.close()
    
    def _generate_cache_key(self, company_name: str, zip_code: Optional[str] = None) -> str:
        """
        Generate cache key from company name and optional zip code.
        Format: md5(company_name.lower().strip():zip_code)
        """
        normalized_name = company_name.lower().strip()
        key_string = f"{normalized_name}:{zip_code or ''}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, company_name: str, zip_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached result for a company.
        Returns None if not found or expired.
        """
        cache_key = self._generate_cache_key(company_name, zip_code)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT result_data, status, created_at
            FROM company_cache
            WHERE cache_key = ? AND expires_at > ?
        """, (cache_key, datetime.now()))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            result_data, status, created_at = row
            return {
                "result": json.loads(result_data),
                "status": status,
                "cached": True,
                "cached_at": created_at
            }
        
        return None
    
    def set(
        self,
        company_name: str,
        result_data: Dict[str, Any],
        status: str,
        zip_code: Optional[str] = None,
        website: Optional[str] = None
    ):
        """
        Store result in cache with TTL.
        """
        cache_key = self._generate_cache_key(company_name, zip_code)
        created_at = datetime.now()
        expires_at = created_at + timedelta(days=settings.cache_ttl_days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO company_cache
            (cache_key, company_name, zip_code, website, result_data, status, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cache_key,
            company_name,
            zip_code,
            website,
            json.dumps(result_data),
            status,
            created_at,
            expires_at
        ))
        
        conn.commit()
        conn.close()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.
        Returns the number of entries deleted.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM company_cache
            WHERE expires_at <= ?
        """, (datetime.now(),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM company_cache WHERE expires_at > ?", (datetime.now(),))
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM company_cache WHERE expires_at <= ?", (datetime.now(),))
        expired_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "active_entries": active_count,
            "expired_entries": expired_count,
            "ttl_days": settings.cache_ttl_days
        }


# Global cache instance
cache = Cache()