import sqlite3
import os
import logging
from . import classification, duplicates, permissions

# Mimetypes to read for content summary
READABLE_MIMES = {
    "text/plain", "text/csv", "application/json", "application/xml",
    "application/x-sh", "application/x-python", "text/markdown",
    "text/html", "application/javascript"
}

class AnalysisManager:
    """Handles the database and orchestrates all AI analysis tasks."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        """Initializes the metadata database schema."""
        try:
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS file_index (
                        id INTEGER PRIMARY KEY,
                        filepath TEXT UNIQUE NOT NULL,
                        filename TEXT,
                        file_type TEXT,
                        file_size INTEGER,
                        sha256_hash TEXT,
                        is_sensitive BOOLEAN,
                        access_count INTEGER,
                        last_modified REAL,
                        content_summary TEXT
                    );
                """)
                self.conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_hash ON file_index (sha256_hash);
                """)
                self.conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_type ON file_index (file_type);
                """)
        except Exception as e:
            logging.error(f"Error creating database table: {e}")
            raise

    def _get_content_summary(self, filepath, file_type):
        """Reads the first 2048 bytes of a text file for indexing."""
        if file_type not in READABLE_MIMES:
            return ""
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(2048) # Read first 2KB
        except FileNotFoundError:
            return ""
        except Exception as e:
            logging.warning(f"Could not read content from {filepath}: {e}")
            return ""

    def analyze_file(self, filepath, is_new=False):
        """Runs all analysis tasks on a single file and updates the DB."""
        if not os.path.exists(filepath) or os.path.isdir(filepath):
            return

        try:
            file_stat = os.stat(filepath)
            filename = os.path.basename(filepath)
            file_size = file_stat.st_size
            last_modified = file_stat.st_mtime
            
            # 1. Classification
            file_type = classification.get_file_type(filepath)
            
            # 2. Hashing (for duplicates)
            file_hash = duplicates.hash_file(filepath)
            
            # 3. Sensitivity Check
            is_sensitive = permissions.check_sensitivity(filepath, file_type)
            
            # 4. Content Summary (FIXED)
            content_summary = self._get_content_summary(filepath, file_type)
            
            # 5. Database Update
            with self.conn:
                # Determine access_count value
                access_count_val = 0
                if not is_new:
                    # Try to preserve old access_count
                    cur = self.conn.cursor()
                    cur.execute("SELECT access_count FROM file_index WHERE filepath = ?", (filepath,))
                    row = cur.fetchone()
                    if row:
                        access_count_val = row[0]

                self.conn.execute("""
                    INSERT INTO file_index (
                        filepath, filename, file_type, file_size, sha256_hash, 
                        is_sensitive, access_count, last_modified, content_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(filepath) DO UPDATE SET
                        filename=excluded.filename,
                        file_type=excluded.file_type,
                        file_size=excluded.file_size,
                        sha256_hash=excluded.sha256_hash,
                        is_sensitive=excluded.is_sensitive,
                        last_modified=excluded.last_modified,
                        content_summary=excluded.content_summary,
                        access_count=file_index.access_count -- Keep old access_count on update
                """, (
                    filepath, filename, file_type, file_size, file_hash,
                    is_sensitive, access_count_val,
                    last_modified, content_summary
                ))
            logging.info(f"Successfully analyzed and indexed: {filepath}")

        except Exception as e:
            logging.error(f"Error during analysis of {filepath}: {e}")

    def remove_file(self, filepath):
        """Removes a file's metadata from the index."""
        with self.conn:
            self.conn.execute("DELETE FROM file_index WHERE filepath = ?", (filepath,))
        logging.info(f"Removed from index: {filepath}")

    def rename_file(self, old_filepath, new_filepath):
        """Updates a file's path in the index."""
        with self.conn:
            self.conn.execute(
                "UPDATE file_index SET filepath = ?, filename = ? WHERE filepath = ?",
                (new_filepath, os.path.basename(new_filepath), old_filepath)
            )
        logging.info(f"Renamed in index: {old_filepath} -> {new_filepath}")

    def log_access(self, filepath):
        """Increments the access count for a file."""
        with self.conn:
            self.conn.execute(
                "UPDATE file_index SET access_count = access_count + 1 WHERE filepath = ?",
                (filepath,)
            )