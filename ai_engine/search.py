import sqlite3
import sys
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

class SmartSearch:
    """Performs natural language search over the file index."""
    def __init__(self, db_path):
        if not os.path.exists(db_path):
            print(f"Error: Database file not found at {db_path}")
            sys.exit(1)
            
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def _get_all_files(self):
        """Fetches all file data from the index."""
        try:
            with self.conn:
                cur = self.conn.cursor()
                cur.execute("SELECT filepath, filename, file_type, content_summary FROM file_index")
                return cur.fetchall()
        except Exception as e:
            logging.error(f"Error fetching files from DB: {e}")
            return []

    def search(self, query):
        """Searches the index for files matching the query."""
        all_files = self._get_all_files()
        if not all_files:
            print("No files in the index.")
            return

        # --- FIX ---
        # Create a "document" for each file by combining its name
        # and its content summary. This is much smarter.
        # We also "boost" the filename by adding it twice.
        documents = [
            f"{doc['filename']} {doc['filename']} {doc['content_summary']}" 
            for doc in all_files
        ]
        filepaths = [doc['filepath'] for doc in all_files]
        # -----------
        
        # Build TF-IDF matrix
        try:
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            query_vec = self.vectorizer.transform([query])
        except ValueError as e:
            print(f"No valid data to search. Index might be empty. Error: {e}")
            return

        # Calculate cosine similarity
        cosine_sims = cosine_similarity(query_vec, tfidf_matrix).flatten()

        # Get top 5 results with a score > 0
        top_indices = cosine_sims.argsort()[-5:][::-1] # Top 5 indices, descending
        
        print(f"--- Search Results for '{query}' ---")
        
        found_results = False
        for i in top_indices:
            score = cosine_sims[i]
            if score > 0.01: # Set a minimum threshold
                print(f"  {'+' * int(score * 5)} [{score:.2f}] {filepaths[i]}")
                found_results = True
        
        if not found_results:
            print("No relevant files found.")

def main():
    if len(sys.argv) != 3:
        print("Usage: python ai_engine/search.py <db_path> <query>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    query = sys.argv[2]
    
    searcher = SmartSearch(db_path)
    searcher.search(query)

if __name__ == "__main__":
    main()