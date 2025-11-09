# InsightFS - A Context-Aware AI File Manager

InsightFS is a prototype file system built using FUSE (Filesystem in Userspace) that integrates an AI layer to provide intelligent features not found in traditional file systems.

This project is based on the "InsightFS" synopsis and extends it with a functional prototype, a web dashboard, and NLP-based search.



## Features

* **FUSE-based Filesystem:** Mounts a user-space filesystem that proxies to a real directory (`storage_backend`).
* **Automatic File Classification:** Uses `python-magic` to identify the MIME type of every file on write.
* **Duplicate Detection:** Calculates the SHA-256 hash of all files to identify and report duplicates.
* **Smart Permission/Sensitivity Check:** Scans text-based files for keywords like "password" or "confidential" to flag them as sensitive.
* **Access Frequency Tracking:** Logs every `read` operation to identify "hot" (frequently accessed) files, a stand-in for predictive caching logic.
* **Web Dashboard:** A Flask + Chart.js dashboard to visualize:
    * Storage breakdown by file type.
    * Wasted space from duplicate files.
    * A list of all sensitive files.
    * A list of the "hottest" files.
* **Natural Language Search:** A CLI tool (`ai_engine.search`) that uses TF-IDF to find files based on a natural language query.

## Project Structure

```
insightfs/
├── ai_engine/          # All AI/analysis logic
├── dashboard/          # Flask web dashboard
├── metadata/           # SQLite database for AI metadata
├── storage_backend/    # The "real" disk storage
├── my_fs/              # The mount point
├── insightfs.py        # Core FUSE logic
├── mount.sh            # Mount script
├── unmount.sh          # Unmount script
├── requirements.txt    # Dependencies
├── README.md           # This file
└── presentation.md     # Presentation slides
```

## How to Run

### 1. Prerequisites

You must be on a Linux or macOS system with FUSE installed.

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y fuse libfuse-dev pkg-config
```

**On macOS (with Homebrew):**
```bash
brew install macfuse
```

### 2. Setup

1.  Clone this repository.
2.  Create and activate a Python virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Running the System

You will need two terminals.

**In Terminal 1: Mount the Filesystem**

This script will run in the foreground and log all filesystem activity.

```bash
# Make scripts executable
chmod +x mount.sh unmount.sh

# Run the mount script
./mount.sh
```
You will see logs as the filesystem starts.

**In Terminal 2: Use the Filesystem & Dashboard**

1.  **Interact with the FS:**
    Your filesystem is now live! Any file you create in `./my_fs` will be analyzed.
    ```bash
    # 'ls' will work as normal
    ls -l my_fs/
    
    # Create a file. This will trigger the AI analysis.
    echo "This is a normal file." > my_fs/hello.txt
    
    # Create a sensitive file
    echo "my password is 1234" > my_fs/secret_doc.txt
    
    # Create a duplicate
    cp my_fs/hello.txt my_fs/hello_copy.txt
    
    # Read a file to trigger the access counter
    cat my_fs/hello.txt
    cat my_fs/hello.txt
    ```

2.  **Run the Dashboard:**
    ```bash
    # Activate the virtual environment
    source venv/bin/activate
    
    # Run the Flask app
    python dashboard/app.py
    ```
    Now, open **`http://127.0.0.1:5000`** in your browser to see the dashboard. It will update in real-time as you add/change files (after a page refresh).

3.  **Use the Smart Search:**
    ```bash
    # Activate the virtual environment
    source venv/bin/activate
    
    # Search for files
    python -m ai_engine.search metadata/file_index.db "secret document"
    # Expected output: [Score: 0.76] /path/to/insightfs/storage_backend/secret_doc.txt
    
    python -m ai_engine.search metadata/file_index.db "hello file"
    # Expected output: [Score: 0.71] /path/to/insightfs/storage_backend/hello.txt
    # Expected output: [Score: 0.71] /path/to/insightfs/storage_backend/hello_copy.txt
    ```

### 4. Stopping the System

1.  Stop the dashboard server (Ctrl+C in Terminal 2).
2.  Stop the filesystem (Ctrl+C in Terminal 1).
3.  If the filesystem didn't unmount cleanly, run the unmount script:
    ```bash
    ./unmount.sh
    ```
