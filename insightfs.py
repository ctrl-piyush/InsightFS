#!/usr/bin/env python

import os
import sys
import errno
import logging
from fuse import FUSE, FuseOSError, Operations
from ai_engine import analysis_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [InsightFS] - %(message)s')

class InsightFS(Operations):
    """
    A FUSE-based filesystem that proxies operations to an underlying
    directory and triggers AI analysis on file changes.
    """
    def __init__(self, root, db_path):
        self.root = root
        self.db_path = db_path
        # Initialize the analysis manager which also sets up the DB
        try:
            self.analyzer = analysis_manager.AnalysisManager(self.db_path)
            logging.info(f"Filesystem initialized. Root: {self.root}, DB: {self.db_path}")
        except Exception as e:
            logging.error(f"Failed to initialize AnalysisManager: {e}")
            sys.exit(1)

    def _full_path(self, partial):
        """Calculate the full path in the underlying storage."""
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # --- Filesystem Operations ---

    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        try:
            st = os.lstat(full_path)
            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                         'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        except FileNotFoundError:
            raise FuseOSError(errno.ENOENT)

    def readdir(self, path, fh):
        full_path = self._full_path(path)
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def read(self, path, size, offset, fh):
        full_path = self._full_path(path)
        logging.info(f"READ: {path}")
        # --- AI Feature: Access Frequency Tracking ---
        try:
            self.analyzer.log_access(full_path)
        except Exception as e:
            logging.warning(f"Failed to log access for {path}: {e}")
        # --- End AI Feature ---
        
        with os.fdopen(fh, 'rb', closefd=False) as f:
            f.seek(offset)
            return f.read(size)

    def write(self, path, data, offset, fh):
        full_path = self._full_path(path)
        logging.info(f"WRITE: {path}")
        
        with os.fdopen(fh, 'wb+', closefd=False) as f:
            f.seek(offset)
            bytes_written = f.write(data)

        # --- AI Feature: Trigger Analysis ---
        # This should be asynchronous in a real system!
        try:
            logging.info(f"Triggering analysis for {path}...")
            self.analyzer.analyze_file(full_path)
            logging.info(f"Analysis complete for {path}.")
        except Exception as e:
            logging.error(f"Failed to analyze {path}: {e}")
        # --- End AI Feature ---
            
        return bytes_written

    def create(self, path, mode):
        full_path = self._full_path(path)
        logging.info(f"CREATE: {path}")
        fd = os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)
        
        # --- AI Feature: Trigger Analysis ---
        try:
            self.analyzer.analyze_file(full_path, is_new=True)
        except Exception as e:
            logging.error(f"Failed to analyze new file {path}: {e}")
        # --- End AI Feature ---
            
        return fd

    def mkdir(self, path, mode):
        full_path = self._full_path(path)
        logging.info(f"MKDIR: {path}")
        os.mkdir(full_path, mode)

    def unlink(self, path):
        full_path = self._full_path(path)
        logging.info(f"UNLINK: {path}")
        
        # --- AI Feature: Remove from Index ---
        try:
            self.analyzer.remove_file(full_path)
        except Exception as e:
            logging.error(f"Failed to remove file from index {path}: {e}")
        # --- End AI Feature ---
            
        os.unlink(full_path)

    def rmdir(self, path):
        full_path = self._full_path(path)
        logging.info(f"RMDIR: {path}")
        os.rmdir(full_path)

    def rename(self, old, new):
        old_full = self._full_path(old)
        new_full = self._full_path(new)
        logging.info(f"RENAME: {old} -> {new}")
        
        # --- AI Feature: Update Index ---
        try:
            self.analyzer.rename_file(old_full, new_full)
        except Exception as e:
            logging.error(f"Failed to update index for rename {old} -> {new}: {e}")
        # --- End AI Feature ---
            
        os.rename(old_full, new_full)
        
    def open(self, path, flags):
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def release(self, path, fh):
        return os.close(fh)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return os.fsync(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: {} <storage_backend> <mount_point> <metadata_db>'.format(sys.argv[0]))
        sys.exit(1)

    storage_backend = sys.argv[1]
    mount_point = sys.argv[2]
    metadata_db = sys.argv[3]

    # Ensure paths are absolute
    storage_backend = os.path.abspath(storage_backend)
    mount_point = os.path.abspath(mount_point)
    metadata_db = os.path.abspath(metadata_db)

    logging.info(f"Mounting InsightFS...")
    logging.info(f"  Storage Backend: {storage_backend}")
    logging.info(f"  Mount Point: {mount_point}")
    logging.info(f"  Metadata DB: {metadata_db}")

    # Ensure directories exist
    os.makedirs(storage_backend, exist_ok=True)
    os.makedirs(mount_point, exist_ok=True)
    os.makedirs(os.path.dirname(metadata_db), exist_ok=True)
    
    # Pass 'foreground=True' for easier debugging
    FUSE(InsightFS(storage_backend, metadata_db), mount_point, foreground=True)
