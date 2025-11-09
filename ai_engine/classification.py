import magic
import logging

def get_file_type(filepath):
    """Uses python-magic to determine the MIME type of a file."""
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(filepath)
        return file_type
    except magic.MagicException as e:
        logging.warning(f"Could not determine file type for {filepath}: {e}")
        return "application/octet-stream" # Default unknown type
    except FileNotFoundError:
        logging.warning(f"File not found during classification: {filepath}")
        return "application/octet-stream"
