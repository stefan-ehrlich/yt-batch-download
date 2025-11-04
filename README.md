# 🎬 Batch YouTube Video Downloader

A simple Python utility to **batch download YouTube videos** from a CSV file using [yt-dlp](https://github.com/yt-dlp/yt-dlp).  
Each row in the CSV defines a **custom filename** and the **YouTube URL** to download.

---

## 🚀 Features

- Batch downloads from a single CSV file  
- Uses **custom video names** from the CSV  
- Compatible with `ffmpeg` for best-quality merges  

---

## 🧩 Requirements

- **Python 3.8+**
- **yt-dlp** (install with `pip install yt-dlp`)
- *(optional)* **ffmpeg** for merging audio and video streams

### Windows (recommended):
```bash
winget install --id Gyan.FFmpeg -e
