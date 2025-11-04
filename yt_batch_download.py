import argparse
import csv
import os
import re
import sys
from pathlib import Path

try:
    from yt_dlp import YoutubeDL
except ImportError:
    print("yt-dlp is not installed. Run: pip install yt-dlp", file=sys.stderr)
    sys.exit(1)

NAME_KEYS = ("name", "title", "video_name")
URL_KEYS  = ("link", "url", "video_url")

INVALID_CHARS = r'<>:"/\\|?*'  # Windows-reserved chars (good cross-platform baseline)

def sanitize_filename(name: str, max_len: int = 180) -> str:
    # Replace invalid characters with underscores and strip whitespace
    name = name.strip()
    name = re.sub(rf"[{re.escape(INVALID_CHARS)}]", "_", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name)
    # Remove trailing periods/spaces (Windows quirk)
    name = name.rstrip(" .")
    # Limit length
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    # Fallback if empty
    return name or "video"

def find_columns(fieldnames):
    lower = [f.lower() for f in fieldnames]
    name_col = next((f for f in fieldnames if f.lower() in NAME_KEYS), None)
    url_col  = next((f for f in fieldnames if f.lower() in URL_KEYS), None)
    return name_col, url_col

def read_rows(csv_path: Path):
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        sample = f.read(4096)
        f.seek(0)
        sniffer = csv.Sniffer()
        has_header = False
        try:
            has_header = sniffer.has_header(sample)
        except csv.Error:
            pass

        if has_header:
            reader = csv.DictReader(f)
            name_col, url_col = find_columns(reader.fieldnames or [])
            if not name_col or not url_col:
                raise ValueError(
                    f"CSV must include name/title/video_name and link/url/video_url. "
                    f"Found columns: {reader.fieldnames}"
                )
            for row in reader:
                name = (row.get(name_col) or "").strip()
                url  = (row.get(url_col) or "").strip()
                if name and url:
                    yield name, url
        else:
            # No header: expect exactly 2 columns per row: name, url
            reader = csv.reader(f)
            for idx, row in enumerate(reader, start=1):
                if len(row) < 2:
                    print(f"Skipping row {idx}: expected 2 columns, got {len(row)}", file=sys.stderr)
                    continue
                name, url = row[0].strip(), row[1].strip()
                if name and url:
                    yield name, url

def download_video(url: str, out_dir: Path, desired_name: str, fmt: str, overwrite: bool):
    safe_name = sanitize_filename(desired_name)
    # Let yt-dlp decide extension; we set the base and add .%(ext)s
    outtmpl = str(out_dir / (safe_name + ".%(ext)s"))

    # If a file with any extension already exists and overwrite=False, skip
    existing = list(out_dir.glob(safe_name + ".*"))
    if existing and not overwrite:
        print(f"[skip] {safe_name} (file exists)")
        return

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": fmt,
        "noprogress": False,
        "quiet": False,
        "no_warnings": True,
        "retries": 5,
        "continuedl": True,   # resume partial downloads
        # Merge to mp4 if possible when bestvideo+bestaudio
        "merge_output_format": "mp4",
    }

    # Create a fresh instance per video so each can have its own outtmpl
    with YoutubeDL(ydl_opts) as ydl:
        print(f"[download] {safe_name}  <-  {url}")
        ydl.download([url])

def main():
    parser = argparse.ArgumentParser(
        description="Batch download YouTube videos from a CSV with (name, link)."
    )
    parser.add_argument("csv", type=str, help="Path to CSV file.")
    parser.add_argument("-o", "--output-dir", type=str, default="downloads",
                        help="Directory to save videos (default: downloads)")
    parser.add_argument("-f", "--format", type=str, default="bestvideo+bestaudio/best",
                        help="yt-dlp format selector (default: bestvideo+bestaudio/best)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite if a file with the same base name already exists.")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    try:
        for name, url in read_rows(csv_path):
            try:
                download_video(url=url, out_dir=out_dir, desired_name=name, fmt=args.format, overwrite=args.overwrite)
                count += 1
            except Exception as e:
                print(f"[error] Failed to download '{name}' from {url}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[fatal] {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nDone. Processed {count} item(s). Files saved to: {out_dir.resolve()}")

if __name__ == "__main__":
    main()
