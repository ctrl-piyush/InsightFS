# InsightFS: Context-Aware Intelligent Filesystem

**InsightFS** is an advanced Operating System project that bridges the gap between raw storage and high-level intelligence. Built on **FUSE (Filesystem in Userspace)**, it intercepts standard file operations in real-time to perform AI analysis, data classification, and security scanning before data ever hits the disk.

![InsightFS Dashboard](https://via.placeholder.com/800x400?text=InsightFS+Dashboard+Preview)

## 🚀 Key Features

### 🧠 AI-Powered Analysis
* **Automatic Classification:** Uses `libmagic` to determine the true file type (MIME) regardless of extension.
* **Intelligent Search:** Implements **TF-IDF (Term Frequency-Inverse Document Frequency)** to rank search results by relevance rather than just filename matching.
* **Sensitive Data Detection:** Scans text content for keywords (e.g., "password", "API Key") and flags files to prevent data leaks.

### 🛡️ Storage Optimization
* **Deduplication:** Calculates SHA-256 hashes for every file. Identical content is flagged as a duplicate instantly, regardless of the filename.
* **Access Tracking:** Logs file access frequency to identify "Hot Files" vs. "Cold Storage" candidates.

### 📊 Real-Time Visualization
* **Web Dashboard:** A modern UI to monitor storage usage, visualize file distribution (Doughnut Charts), and manage files securely.

---

## 🏗️ System Architecture

InsightFS mimics a standard Operating System architecture by splitting responsibilities into **Kernel Space** (simulated via FUSE) and **User Space** (the Dashboard).

```mermaid
graph TD
    User[User / Dashboard] -->|Writes File| MountPoint[Mount Point (my_fs)]
    MountPoint -->|Intercepts System Call| FUSE[FUSE Driver (insightfs.py)]
    
    subgraph "InsightFS Kernel (Terminal 1)"
    FUSE -->|1. Analyze Content| AI[AI Engine]
    FUSE -->|2. Update Metadata| DB[(SQLite Database)]
    FUSE -->|3. Write to Disk| Storage[Storage Backend]
    end
    
    subgraph "User Space (Terminal 2)"
    Dashboard[Flask Web App] -->|Reads| DB
    Dashboard -->|Sends Commands| MountPoint
    end
The Kernel (Terminal 1): Runs insightfs.py. This daemon holds the mount point active, intercepting write, read, and unlink syscalls.

The Interface (Terminal 2): Runs dashboard/app.py. A Flask application that queries the metadata database and allows user interaction.

🛠️ Installation & Setup
Prerequisites
OS: Linux or WSL (Windows Subsystem for Linux) is required for FUSE support.

Python: 3.8 or higher.

System Libraries: libfuse must be installed.

Ubuntu/Debian: sudo apt-get install fuse libfuse-dev

1. Clone & Prepare
Bash

git clone [https://github.com/YOUR_USERNAME/InsightFS.git](https://github.com/YOUR_USERNAME/InsightFS.git)
cd InsightFS

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
2. Create Directory Structure
We need three key folders for the filesystem to work:

Bash

mkdir -p my_fs storage_backend metadata
my_fs: The virtual mount point (User entry).

storage_backend: The physical storage (Hidden).

metadata: Stores the AI index database.

🖥️ How to Run (The 2-Terminal Workflow)
Because this is a filesystem driver, it must run in a separate process from the UI.

Step 1: Start the Filesystem (Terminal 1)
This acts as the OS Kernel driver.

Bash

# Ensure venv is activated
source venv/bin/activate

# Run the FUSE script
python insightfs.py storage_backend my_fs metadata/file_index.db
⚠️ Note: This terminal may appear to "hang" or show a blinking cursor. This is normal; the process is running in the foreground.

Step 2: Start the Dashboard (Terminal 2)
Open a new terminal window/tab.

Bash

# Navigate to project and activate venv
cd path/to/insightfs
source venv/bin/activate

# Run the Web UI
python dashboard/app.py
Step 3: Access the System
Open your browser and navigate to: 👉 http://localhost:5000

You can now:

Create Files: Click "New File" to write data to the virtual filesystem.

Search: Type keywords like "budget" to test the AI ranking.

Verify: Check the my_fs/ folder in your file explorer to see the files created.

🔧 Troubleshooting
Error: "Transport endpoint is not connected" This happens if the FUSE script (Terminal 1) crashed or was closed improperly.

Fix: Unmount the directory manually:

Bash

fusermount -u my_fs
Then restart Step 1.

Error: "Database not found"

Fix: Ensure Terminal 1 (insightfs.py) is running before you start Terminal 2. The filesystem creates the database.

📂 Project Structure
Plaintext

InsightFS/
├── ai_engine/              # Core AI Logic
│   ├── analysis_manager.py # Orchestrates classification & DB updates
│   ├── classification.py   # Magic-byte file typing
│   ├── duplicates.py       # SHA-256 hashing
│   └── permissions.py      # Sensitive data scanning
├── dashboard/              # Web Interface
│   ├── app.py              # Flask backend & API
│   └── templates/          # HTML Frontend
├── insightfs.py            # Main FUSE Driver (The "Kernel")
├── requirements.txt        # Python dependencies
└── README.md               # Documentation
📜 License
This project is open-source and available under the MIT License.
