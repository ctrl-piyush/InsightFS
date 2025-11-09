---
# InsightFS
## A Context-Aware AI File Manager

**Team:**
* Piyush (Team Lead)
* Lakshay Verma
* Rudra Pratap Singh

---

## The Problem

Traditional file systems (ext4, NTFS) are "dumb." They store data but don't understand it.

With terabytes of data, users face major challenges:
* **Finding Files:** "Where is that report I wrote last month?"
* **Duplicate Data:** Multiple copies of the same 5GB video file wasting space.
* **Security:** "Did I accidentally save a file with my API keys in it?"
* **Optimization:** Slow access to frequently used files.

---

## The Solution: InsightFS

**InsightFS** is a smart file system layer that integrates AI to understand your data *as you write it*.

It bridges the gap between low-level OS storage and high-level intelligent automation.



---

## System Architecture

Our system is built in three main layers:

1.  **FUSE-based Layer (The Core)**
    * A filesystem in userspace (FUSE) written in Python.
    * It intercepts all file operations (`read`, `write`, `create`).
    * It proxies these operations to the underlying disk storage.

2.  **AI Layer (The "Insight")**
    * Triggered by the FUSE layer on file changes.
    * Runs analysis tasks asynchronously.
    * Stores all findings in a central metadata database.

3.  **User Interface (The "View")**
    * **CLI:** The filesystem itself! (`ls`, `cat`, `cp` in the mount point).
    * **Smart Search:** A CLI tool for natural language search.
    * **Web Dashboard:** A visual way to see the AI's insights.

---

## Live Demo: Features

1.  **Real-time File Classification**
2.  **Duplicate Detection**
3.  **Sensitive File Warning**
4.  **Access Frequency ("Hot File") Tracking**
5.  **Smart Search (CLI)**
6.  **Web Dashboard**

---

## Feature 1: The Dashboard

A real-time web dashboard shows us the state of our filesystem.

* **Storage Visualization:** A pie chart of what's *really* on your disk (images, text, video).
* **Duplicate Monitor:** Tracks wasted space from duplicate files.
* **Security Monitor:** Lists all files flagged as "sensitive."
* **Hot Files:** Shows the most frequently read files.



---

## Feature 2: Smart Search (CLI)

We use Natural Language Processing (TF-IDF) to find files. You can search by *concept*, not just filename.

**Query:**
`python -m ai_engine.search metadata/file_index.db "my secret password doc"`

**Result:**
```
--- Search Results for 'my secret password doc' ---
[Score: 0.82] /path/to/storage_backend/secret_doc.txt
[Score: 0.51] /path/to/storage_backend/api_keys.txt
```

---

## Future Work

* **Asynchronous Analysis:** Move the AI tasks to a background worker queue for much faster filesystem performance.
* **True Predictive Caching:** Use an ML model (e.g., LRU + usage patterns) to pre-load frequently accessed files into a memory cache.
* **Content-based Search:** Index the *full text* of documents (PDFs, .txt, .md) for deeper search.
* **Smart Permission *Recommendations*:** Actively suggest `chmod` changes for sensitive files that are world-readable.

---

## Thank You

### Questions?
