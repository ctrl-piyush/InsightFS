from flask import Flask, render_template, jsonify
import sqlite3
import os

# Find the DB path. Assume it's in metadata/file_index.db relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'metadata', 'file_index.db')

app = Flask(__name__)

def get_db_connection():
    """Connects to the SQLite database."""
    try:
        # Connect in read-only mode, fail if DB doesn't exist
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) 
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError as e:
        print(f"Error connecting to database at {DB_PATH}: {e}")
        return None

@app.route('/')
def index():
    """Renders the main dashboard page."""
    return render_template('index.html')

@app.route('/api/stats')
def api_stats():
    """Provides file stats for the dashboard visuals."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database not found. Is InsightFS running and has it indexed any files?"}), 500

    try:
        cur = conn.cursor()

        # --- General Stats (New) ---
        cur.execute("SELECT COUNT(*) as file_count, SUM(file_size) as total_size FROM file_index")
        general_stats_row = cur.fetchone()
        general_stats = {
            "file_count": general_stats_row["file_count"] or 0,
            "total_size": general_stats_row["total_size"] or 0
        }

        # --- File Type Distribution ---
        cur.execute("""
            SELECT 
                CASE 
                    WHEN file_type LIKE 'image/%' THEN 'Images'
                    WHEN file_type LIKE 'text/%' THEN 'Text'
                    WHEN file_type LIKE 'application/pdf' THEN 'PDFs'
                    WHEN file_type LIKE 'video/%' THEN 'Video'
                    WHEN file_type LIKE 'audio/%' THEN 'Audio'
                    ELSE 'Other' 
                END as category, 
                COUNT(*) as count,
                SUM(file_size) as total_size
            FROM file_index 
            GROUP BY category
        """)
        type_stats = [dict(row) for row in cur.fetchall()]

        # --- Duplicate Files ---
        cur.execute("""
            SELECT sha256_hash, COUNT(*) as count, SUM(file_size) as total_size
            FROM file_index
            WHERE sha256_hash IS NOT NULL
            GROUP BY sha256_hash
            HAVING count > 1
        """)
        duplicates = [dict(row) for row in cur.fetchall()]
        
        duplicate_summary = {
            "count": len(duplicates),
            # Calculate wasted space: (count - 1) * size_of_one_file
            "wasted_space": sum([ (d['count'] - 1) * (d['total_size'] / d['count']) for d in duplicates if d['count'] > 0 ])
        }

        # --- Sensitive Files ---
        cur.execute("SELECT filepath, file_type FROM file_index WHERE is_sensitive = 1")
        sensitive_files = [dict(row) for row in cur.fetchall()]

        # --- Hot Files (Top 5 most accessed) ---
        cur.execute("""
            SELECT filepath, access_count 
            FROM file_index 
            WHERE access_count > 0
            ORDER BY access_count DESC 
            LIMIT 5
        """)
        hot_files = [dict(row) for row in cur.fetchall()]
        
        conn.close()

        return jsonify({
            "general_stats": general_stats,
            "type_stats": type_stats,
            "duplicate_summary": duplicate_summary,
            "sensitive_files": sensitive_files,
            "hot_files": hot_files
        })
    
    except sqlite3.OperationalError as e:
        conn.close()
        return jsonify({"error": f"Database query failed: {e}. Has the index been built?"}), 500


if __name__ == '__main__':
    print(f"Dashboard starting... Access at http://127.0.0.1:5000")
    print(f"Reading database from: {DB_PATH}")
    app.run(debug=True, host='0.0.0.0')