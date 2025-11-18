import sys
import os
import sqlite3
import platform
import subprocess
import time
from flask import Flask, render_template, jsonify, request

# --- PROJECT SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ai_engine.analysis_manager import AnalysisManager

app = Flask(__name__)

# --- CONFIGURATION ---
DB_PATH = os.path.join(project_root, 'metadata', 'file_index.db')
MOUNT_POINT = os.path.join(project_root, 'my_fs')
STORAGE_BACKEND = os.path.join(project_root, 'storage_backend')

analyzer = AnalysisManager(DB_PATH)

def get_db_connection():
    if not os.path.exists(DB_PATH): return None
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) 
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError: return None

@app.route('/')
def index(): return render_template('index.html')

# --- API: STATISTICS ---
@app.route('/api/stats')
def api_stats():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database not found. Please run Terminal 1 first."}), 500

    try:
        cur = conn.cursor()

        # 1. Fetch ALL files
        cur.execute("SELECT filepath, filename, file_size, file_type FROM file_index")
        rows = cur.fetchall()

        # Initialize Counters for Size AND Count
        categories = ["Images", "Text", "PDFs", "Video", "Audio", "Archives", "Other"]
        stats_size = {k: 0 for k in categories}
        stats_count = {k: 0 for k in categories}
        
        file_count = 0
        total_size = 0
        all_files = []

        for row in rows:
            file_count += 1
            fsize = row['file_size'] or 0
            total_size += fsize
            
            fname = row['filename']
            if not fname: fname = os.path.basename(row['filepath'])
            ext = os.path.splitext(fname)[1].lower()
            mime = (row['file_type'] or '').lower()

            # --- CATEGORIZATION ---
            if mime.startswith('image/') or ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp']:
                category = 'Images'
            elif mime.startswith('video/') or ext in ['.mp4', '.mkv', '.mov', '.avi', '.wmv', '.flv', '.webm']:
                category = 'Video'
            elif mime.startswith('audio/') or ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']:
                category = 'Audio'
            elif 'pdf' in mime or ext == '.pdf':
                category = 'PDFs'
            elif mime.startswith('text/') or ext in ['.txt', '.md', '.csv', '.py', '.js', '.html', '.css', '.json', '.xml', '.log']:
                category = 'Text'
            elif 'zip' in mime or 'compressed' in mime or ext in ['.zip', '.tar', '.gz', '.rar', '.7z']:
                category = 'Archives'
            else:
                category = 'Other'
            
            # Update Stats
            stats_size[category] += fsize
            stats_count[category] += 1

            all_files.append({
                "name": fname,
                "filepath": row['filepath'],
                "size": fsize,
                "type": row['file_type']
            })

        # Create List for Chart (Include category if COUNT > 0, regardless of size)
        type_stats = []
        for cat in categories:
            if stats_count[cat] > 0:
                type_stats.append({
                    "category": cat, 
                    "total_size": stats_size[cat],
                    "count": stats_count[cat] # Sending count to frontend
                })

        # 2. Duplicates
        cur.execute("SELECT sha256_hash, COUNT(*) as count, SUM(file_size) as total_size FROM file_index WHERE sha256_hash IS NOT NULL GROUP BY sha256_hash HAVING count > 1")
        duplicates = [dict(row) for row in cur.fetchall()]
        duplicate_summary = { "count": len(duplicates), "wasted_space": sum([ (d['count']-1)*(d['total_size']/d['count']) for d in duplicates ]) }

        # 3. Sensitive & Hot Files
        cur.execute("SELECT filepath, file_type FROM file_index WHERE is_sensitive = 1")
        sensitive_files = [dict(row) for row in cur.fetchall()]

        cur.execute("SELECT filepath, access_count FROM file_index WHERE access_count > 0 ORDER BY access_count DESC LIMIT 5")
        hot_files = [dict(row) for row in cur.fetchall()]

        conn.close()
        
        return jsonify({
            "general_stats": { "file_count": file_count, "total_size": total_size },
            "type_stats": type_stats, 
            "duplicate_summary": duplicate_summary, 
            "sensitive_files": sensitive_files, 
            "hot_files": hot_files, 
            "all_files": all_files
        })
    except Exception as e:
        if conn: conn.close()
        return jsonify({"error": str(e)}), 500

# --- API: AI SEARCH ---
@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query: return jsonify([])
    conn = get_db_connection()
    if not conn: return jsonify([])
    try:
        cur = conn.cursor()
        cur.execute("SELECT filepath, filename, content_summary FROM file_index")
        rows = cur.fetchall()
        conn.close()
        if not rows: return jsonify([])

        documents = [f"{r['filename']} {r['filename']} {r['content_summary'] or ''}" for r in rows]
        filepaths = [r['filepath'] for r in rows]

        vectorizer = TfidfVectorizer(stop_words='english')
        try:
            tfidf_matrix = vectorizer.fit_transform(documents)
            query_vec = vectorizer.transform([query])
            cosine_sims = cosine_similarity(query_vec, tfidf_matrix).flatten()
            results = []
            top_indices = cosine_sims.argsort()[-10:][::-1]
            for i in top_indices:
                score = cosine_sims[i]
                if score > 0.01:
                    results.append({"filepath": filepaths[i], "name": os.path.basename(filepaths[i]), "score": round(score, 2)})
            return jsonify(results)
        except ValueError: return jsonify([])
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- API: ACTIONS ---
@app.route('/api/create', methods=['POST'])
def create_file():
    filename = request.json.get('filename')
    content = request.json.get('content', '')
    if not filename: return jsonify({"error": "Filename required"}), 400
    
    safe_name = os.path.basename(filename)
    mount_path = os.path.join(MOUNT_POINT, safe_name)
    storage_path = os.path.join(STORAGE_BACKEND, safe_name)

    try:
        if os.path.exists(MOUNT_POINT):
            with open(mount_path, 'w') as f: f.write(content)
        else:
            with open(storage_path, 'w') as f: f.write(content)

        analyzer.analyze_file(storage_path, is_new=True)
        return jsonify({"status": "success"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def delete_file():
    filepath = request.json.get('filepath')
    if not filepath: return jsonify({"error": "Path required"}), 400
    filename = os.path.basename(filepath)
    mount_path = os.path.join(MOUNT_POINT, filename)
    storage_path = os.path.join(STORAGE_BACKEND, filename)

    try:
        if os.path.exists(mount_path): os.remove(mount_path)
        elif os.path.exists(storage_path): os.remove(storage_path)
        
        analyzer.remove_file(mount_path)
        analyzer.remove_file(storage_path)
        return jsonify({"status": "success"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/open', methods=['POST'])
def open_file():
    filepath = request.json.get('filepath')
    if not os.path.exists(filepath):
        alt_path = os.path.join(STORAGE_BACKEND, os.path.basename(filepath))
        if os.path.exists(alt_path): filepath = alt_path
        else: return jsonify({"error": "File not found"}), 404

    try:
        analyzer.log_access(filepath)
        if platform.system() == 'Windows': os.startfile(filepath)
        elif platform.system() == 'Darwin': subprocess.call(('open', filepath))
        else: 
            try: subprocess.call(('xdg-open', filepath))
            except: 
                try:
                    win_path = subprocess.check_output(['wslpath', '-w', filepath]).decode().strip()
                    subprocess.call(['explorer.exe', win_path])
                except Exception as e: return jsonify({"error": "WSL Error: " + str(e)}), 500
        return jsonify({"status": "success"})
    except Exception as e: return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')