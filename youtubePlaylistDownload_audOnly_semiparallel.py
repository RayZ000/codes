# semiparallel cuz all downloads are done first before any conversion

import os
import sys
import threading
import queue
import time
import yt_dlp
import subprocess
import concurrent.futures
import re

# Concurrency limits
DOWNLOAD_CONCURRENCY = 10
CONVERSION_CONCURRENCY = 3

def canonical_input(prompt):
    """
    Force the terminal into a sane (canonical) state before prompting.
    This is a simple workaround to avoid raw-mode issues.
    """
    os.system("stty sane")
    return input(prompt)

def get_playlist_title(playlist_url):
    """
    Retrieve the playlist title using yt-dlp.
    Uses --skip-download, --no-warnings, and --print playlist_title.
    Returns a sanitized title string safe for a folder name.
    """
    try:
        cmd = [
            "yt-dlp",
            playlist_url,
            "-I", "1:1",
            "--skip-download",
            "--no-warnings",
            "--print", "playlist_title"
        ]
        output = subprocess.check_output(cmd, universal_newlines=True)
        title = output.strip()
        # Sanitize: allow alphanumerics, spaces, underscore, dash.
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
        return safe_title if safe_title else "playlist_unknown"
    except Exception as e:
        print(f"[Title] Error retrieving playlist title for {playlist_url}: {e}")
        return "playlist_unknown"

def get_playlist_video_urls(playlist_url):
    """
    Extract a list of video URLs from the given playlist URL using yt-dlp.
    """
    video_urls = []
    ydl_opts = {
        'skip_download': True,
        'ignoreerrors': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            if info and 'entries' in info:
                for entry in info['entries']:
                    if entry and entry.get("webpage_url"):
                        video_urls.append(entry["webpage_url"])
    except Exception as e:
        print(f"[Playlist] Error extracting video URLs from {playlist_url}: {e}")
    return video_urls

def download_video(video_url, output_folder):
    """
    Download a single video (merged into MP4) using yt-dlp.
    Returns the filename of the downloaded video (or None on failure).
    """
    outtmpl = os.path.join(output_folder, "%(title)s [%(id)s].%(ext)s")
    ydl_opts = {
        'format': 'best',  # downloads the best merged format
        'outtmpl': outtmpl,
        'ignoreerrors': True,
        'merge_output_format': 'mp4',
        'keepvideo': True,  # we need the merged MP4 for conversion
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            if info is None:
                print(f"[Download] No info for video: {video_url}")
                return None
            video_file = ydl.prepare_filename(info)
            print(f"[Download] Downloaded video: {video_file}")
            return video_file
    except Exception as e:
        print(f"[Download] Error downloading video {video_url}: {e}")
        return None

def convert_to_mp3(video_file):
    """
    Convert a downloaded merged video (MP4) to MP3 using FFmpeg.
    On success, delete the original video file.
    Returns the path to the MP3 file.
    """
    base, _ = os.path.splitext(video_file)
    mp3_file = base + ".mp3"
    print(f"[Conversion] Converting {video_file} to MP3...")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", video_file,
            "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k",
            mp3_file
        ], check=True)
        print(f"[Conversion] Conversion complete: {mp3_file}")
        os.remove(video_file)
        print(f"[Conversion] Deleted original video file: {video_file}")
    except subprocess.CalledProcessError as e:
        print(f"[Conversion] Error converting {video_file}: {e}")
    return mp3_file

def conversion_worker(download_queue):
    """
    Worker function that continuously takes a downloaded video filename
    from download_queue, converts it to MP3, and then moves on.
    When a sentinel (None) is encountered, the worker exits.
    """
    while True:
        video_file = download_queue.get()
        if video_file is None:
            download_queue.task_done()
            break
        convert_to_mp3(video_file)
        download_queue.task_done()

def main():
    # Collect playlist URLs one by one.
    playlist_urls = []
    while True:
        url = canonical_input("Enter a playlist URL (or type 'done' to finish): ").strip()
        if url.lower() in ("done", ""):
            break
        playlist_urls.append(url)
    if not playlist_urls:
        print("No playlist URLs provided. Exiting.")
        return

    download_folder = canonical_input("Enter the folder to store downloads: ").strip()
    os.makedirs(download_folder, exist_ok=True)
    print(f"[Main] Using main download folder: {download_folder}")

    # List to store folder paths (each folder is named after a playlist).
    playlist_folders = []
    # Build a global list of download tasks: each is (video_url, target_folder)
    tasks = []
    for p_url in playlist_urls:
        title = get_playlist_title(p_url)
        playlist_folder = os.path.join(download_folder, title)
        # If folder already exists, append a counter.
        base_folder = playlist_folder
        counter = 1
        while os.path.exists(playlist_folder):
            playlist_folder = f"{base_folder}_{counter}"
            counter += 1
        os.makedirs(playlist_folder, exist_ok=True)
        playlist_folders.append(playlist_folder)
        video_urls = get_playlist_video_urls(p_url)
        print(f"[Playlist] Found {len(video_urls)} videos in playlist '{title}'.")
        for video_url in video_urls:
            tasks.append((video_url, playlist_folder))

    # Create a queue for conversion tasks.
    downloaded_queue = queue.Queue()

    # Start the download tasks in a ThreadPoolExecutor.
    download_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=DOWNLOAD_CONCURRENCY) as download_executor:
        futures = {
            download_executor.submit(download_video, video_url, folder): (video_url, folder)
            for video_url, folder in tasks
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                # As soon as a download finishes, add its filename to the conversion queue.
                downloaded_queue.put(result)

    # Start conversion worker threads.
    conversion_threads = []
    for _ in range(CONVERSION_CONCURRENCY):
        t = threading.Thread(target=conversion_worker, args=(downloaded_queue,))
        t.start()
        conversion_threads.append(t)

    # Signal conversion workers that no more downloads will be added.
    for _ in range(CONVERSION_CONCURRENCY):
        downloaded_queue.put(None)

    # Wait for all conversion tasks to finish.
    downloaded_queue.join()
    for t in conversion_threads:
        t.join()

    print("Finish: All download and conversion tasks are complete.")
    # (Later, after this point you could start running Whisper on the MP3 files one by one.)

if __name__ == "__main__":
    main()