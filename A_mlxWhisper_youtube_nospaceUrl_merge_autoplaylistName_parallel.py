import os
import sys
import threading
import queue
import time
import yt_dlp
import subprocess
import concurrent.futures
import re
import mlx_whisper

# Concurrency limits for different groups
DOWNLOAD_CONCURRENCY = 10
CONVERSION_CONCURRENCY = 8
METADATA_CONCURRENCY = 50

# Whisper model identifier
MODEL_ID = "mlx-community/whisper-large-v3-turbo"

def canonical_input(prompt):
    """
    Force the terminal into a sane state before prompting.
    """
    os.system("stty sane")
    return input(prompt)

def get_playlist_title(playlist_url):
    """
    Retrieve the playlist title using yt-dlp with --skip-download, --no-warnings,
    and --print playlist_title. Returns a sanitized title safe for a folder name.
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
    Extract a list of video URLs from the given playlist using yt-dlp.
    """
    video_urls = []
    ydl_opts = {'skip_download': True, 'ignoreerrors': True}
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

def process_playlist_metadata(playlist_url):
    """
    Retrieve metadata for a given playlist: its title and list of video URLs.
    """
    title = get_playlist_title(playlist_url)
    video_urls = get_playlist_video_urls(playlist_url)
    return title, video_urls

def download_video(video_url, output_folder):
    """
    Download a single video (merged into an MP4 file) using yt-dlp.
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

def download_task(video_url, folder, download_queue):
    """
    Download a single video and, if successful, immediately put its filename into the download_queue.
    """
    video_file = download_video(video_url, folder)
    if video_file:
        download_queue.put(video_file)

def convert_to_mp3(video_file):
    """
    Convert a downloaded merged video (MP4) to MP3 using FFmpeg.
    On success, delete the original MP4 file.
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
    Continuously pull a downloaded video filename from download_queue and convert it to MP3.
    When a sentinel value (None) is encountered, exit.
    """
    while True:
        video_file = download_queue.get()
        if video_file is None:
            download_queue.task_done()
            break
        convert_to_mp3(video_file)
        download_queue.task_done()

# --- Whisper Transcription Section ---

# Global transcription queue for Whisper tasks.
transcription_queue = queue.Queue()

def transcription_worker():
    """
    Worker thread that processes transcription tasks serially.
    Each task is a tuple: (audio_filepath, transcript_filepath).
    After a successful transcription, the intermediate MP3 file is deleted.
    """
    while True:
        task = transcription_queue.get()
        if task is None:
            transcription_queue.task_done()
            break
        audio_path, transcript_path = task
        print(f"[Transcription] Starting transcription for: {audio_path}")
        try:
            result = mlx_whisper.transcribe(audio_path, path_or_hf_repo=MODEL_ID)
            transcript_text = result.get("text", "")
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(transcript_text)
            print(f"[Transcription] Finished transcription for: {audio_path}")
            print(f"[Transcription] Transcript saved to: {transcript_path}")
        except Exception as e:
            print(f"[Transcription] Error transcribing {audio_path}: {e}")
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"[Transcription] Deleted intermediate MP3 file: {audio_path}")
        except Exception as e:
            print(f"[Transcription] Error deleting {audio_path}: {e}")
        transcription_queue.task_done()

def merge_transcripts_for_playlist(playlist_folder):
    """
    Merge all individual transcript (.txt) files in a playlist folder into one file.
    The merged file is named 'merged_transcript.txt' and placed in the same folder.
    Each transcript is preceded by a header with the video title (derived from its filename).
    """
    transcript_files = []
    for file in os.listdir(playlist_folder):
        if file.lower().endswith(".txt") and file != "merged_transcript.txt":
            transcript_files.append(file)
    if not transcript_files:
        return
    transcript_files.sort()
    merged_path = os.path.join(playlist_folder, "merged_transcript.txt")
    with open(merged_path, "w", encoding="utf-8") as merged_file:
        for transcript_filename in transcript_files:
            title = os.path.splitext(transcript_filename)[0]
            merged_file.write(f"=== {title} ===\n\n")
            transcript_path = os.path.join(playlist_folder, transcript_filename)
            with open(transcript_path, "r", encoding="utf-8") as f:
                merged_file.write(f.read())
            merged_file.write("\n\n")
    print(f"[Merge] Created merged transcript file: {merged_path}")

def main():
    # --- Input Phase ---
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

    # --- Metadata Retrieval (Parallel) ---
    playlist_info_list = []  # Each entry: (playlist_url, title, video_urls)
    with concurrent.futures.ThreadPoolExecutor(max_workers=METADATA_CONCURRENCY) as executor:
        future_to_url = {
            executor.submit(process_playlist_metadata, p_url): p_url
            for p_url in playlist_urls
        }
        for future in concurrent.futures.as_completed(future_to_url):
            p_url = future_to_url[future]
            try:
                title, video_urls = future.result()
                playlist_info_list.append((p_url, title, video_urls))
            except Exception as exc:
                print(f"[Metadata] Retrieval for {p_url} generated an exception: {exc}")

    tasks = []  # List of (video_url, target_folder)
    playlist_folders = []
    for p_url, title, video_urls in playlist_info_list:
        playlist_folder = os.path.join(download_folder, title)
        base_folder = playlist_folder
        counter = 1
        while os.path.exists(playlist_folder):
            playlist_folder = f"{base_folder}_{counter}"
            counter += 1
        os.makedirs(playlist_folder, exist_ok=True)
        playlist_folders.append(playlist_folder)
        print(f"[Metadata] Playlist '{title}' has {len(video_urls)} videos.")
        for video_url in video_urls:
            tasks.append((video_url, playlist_folder))

    # --- Download & Conversion Pipeline ---

    # Create a global queue for conversion tasks.
    downloaded_queue = queue.Queue()

    # Start conversion worker threads BEFORE download tasks.
    conversion_threads = []
    for _ in range(CONVERSION_CONCURRENCY):
        t = threading.Thread(target=conversion_worker, args=(downloaded_queue,))
        t.start()
        conversion_threads.append(t)

    # Start download tasks concurrently using a ThreadPoolExecutor.
    with concurrent.futures.ThreadPoolExecutor(max_workers=DOWNLOAD_CONCURRENCY) as download_executor:
        futures = [
            download_executor.submit(download_task, video_url, folder, downloaded_queue)
            for video_url, folder in tasks
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    # Signal conversion workers that no more files will be added.
    for _ in range(CONVERSION_CONCURRENCY):
        downloaded_queue.put(None)
    downloaded_queue.join()
    for t in conversion_threads:
        t.join()

    print("[Main] All download and conversion tasks are complete.")

    # --- Whisper Transcription Phase ---
    # Gather all MP3 files from the download folder.
    mp3_files = []
    for root, dirs, files in os.walk(download_folder):
        for file in files:
            if file.lower().endswith(".mp3"):
                mp3_files.append(os.path.join(root, file))
    print(f"[Main] Found {len(mp3_files)} MP3 files for transcription.")

    # Start a transcription worker thread.
    transcription_thread = threading.Thread(target=transcription_worker, daemon=True)
    transcription_thread.start()

    for mp3_file in mp3_files:
        base, _ = os.path.splitext(mp3_file)
        transcript_filename = base + ".txt"
        print(f"[Main] Enqueuing transcription task for: {mp3_file}")
        transcription_queue.put((mp3_file, transcript_filename))

    transcription_queue.join()
    transcription_queue.put(None)
    transcription_thread.join()

    print("[Main] All transcriptions completed. Only transcript text files remain.")

    # --- Merge Transcripts ---
    for folder in playlist_folders:
        merge_transcripts_for_playlist(folder)

if __name__ == "__main__":
    main()