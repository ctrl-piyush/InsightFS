import hashlib
import logging

def hash_file(filepath):
    """Calculates the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            # Read in 64k chunks
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256.update(byte_block)
        return sha256.hexdigest()
    except FileNotFoundError:
        logging.warning(f"File not found during hashing: {filepath}")
        return None
    except Exception as e:
        logging.error(f"Error hashing {filepath}: {e}")
        return None
