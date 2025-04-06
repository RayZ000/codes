import os
import sys
import threading
import queue
import time
import yt_dlp
import mlx_whisper
import subprocess

# Global transcription queue (ensures one ML process at a time)
transcription_queue = queue.Queue()

# ML model identifier for Whisper transcription
MODEL_ID = "mlx-community/whisper-large-v3-turbo"

def canonical_input(prompt):
    """
    Reset the terminal to a sane state before prompting for input.
    This is a simple workaround to avoid raw-mode issues.
    """
    os.system("stty sane")
    return input(prompt)

def convert_to_mp3(video_file):
    """
    Convert a downloaded video file (merged MP4) to MP3 using FFmpeg.
    On success, delete the original video file.
    Returns the path to the converted MP3.
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
        # Delete the original video file.
        os.remove(video_file)
        print(f"[Conversion] Deleted original video file: {video_file}")
    except subprocess.CalledProcessError as e:
        print(f"[Conversion] Error converting {video_file}: {e}")
    return mp3_file

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
            full_transcript = result.get("text", "")
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(full_transcript)
            print(f"[Transcription] Finished transcription for: {audio_path}")
            print(f"[Transcription] Transcript saved to: {transcript_path}")
        except Exception as e:
            print(f"[Transcription] Error transcribing {audio_path}: {e}")
        # Delete the intermediate MP3 file.
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"[Transcription] Deleted intermediate MP3 file: {audio_path}")
        except Exception as e:
            print(f"[Transcription] Error deleting {audio_path}: {e}")
        transcription_queue.task_done()

def download_playlist(playlist_url, playlist_folder, audio_quality=None):
    """
    Downloads all videos from a given playlist URL into the specified folder.
    Each video is downloaded as a merged MP4 file.
    Then, immediately spawns a conversion task to convert it to MP3.
    """
    os.makedirs(playlist_folder, exist_ok=True)
    print(f"[Playlist] Created folder for playlist: {playlist_folder}")

    conversion_threads = []

    # Use a format that downloads a merged file.
    # 'best' will select the best available combined format.
    format_str = "best"
    outtmpl = os.path.join(playlist_folder, "%(title)s [%(id)s].%(ext)s")

    def progress_hook(d):
        if d.get("status") == "finished":
            original_filename = d.get("filename")
            if original_filename:
                print(f"[Download] Finished downloading: {original_filename}")
                # Start a conversion thread to convert the merged video to MP3.
                t_conv = threading.Thread(target=convert_to_mp3, args=(original_filename,))
                t_conv.start()
                conversion_threads.append(t_conv)

    ydl_opts = {
        'format': format_str,
        'outtmpl': outtmpl,
        'ignoreerrors': True,
        'merge_output_format': 'mp4',  # Force merging into a single MP4 file.
        'progress_hooks': [progress_hook],
        'keepvideo': True,  # Keep the merged video until conversion is done.
    }

    try:
        print(f"[Playlist] Starting download for playlist: {playlist_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist_url])
        print(f"[Playlist] Completed download for playlist: {playlist_url}")
    except Exception as e:
        print(f"[Playlist] Error downloading playlist {playlist_url}: {e}")

    # Wait for all conversion threads in this playlist to finish.
    for t in conversion_threads:
        t.join()
    print(f"[Playlist] All video-to-MP3 conversions completed for playlist: {playlist_url}")

def merge_transcripts_for_playlist(playlist_folder):
    """
    Merge all individual transcript (.txt) files in a playlist folder into one file.
    The merged file is named 'merged_transcript.txt' and placed in the same folder.
    For each transcript file, the video title (derived from the filename, sans extension)
    is written as a header before its transcript content.
    """
    transcript_files = []
    for file in os.listdir(playlist_folder):
        if file.lower().endswith(".txt") and file != "merged_transcript.txt":
            transcript_files.append(file)
    if not transcript_files:
        return
    transcript_files.sort()  # sort alphabetically (or modify as needed)
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

    audio_quality_input = canonical_input("Enter desired maximum audio bitrate in kbps (e.g., 192, leave blank for best): ").strip()
    audio_quality = audio_quality_input if audio_quality_input else None

    download_folder = canonical_input("Enter the folder to store temporary audio-video files: ").strip()
    os.makedirs(download_folder, exist_ok=True)
    print(f"[Main] Using main download folder: {download_folder}")

    download_threads = []
    # Create a list to track the playlist folders.
    playlist_folders = []
    for idx, playlist_url in enumerate(playlist_urls, start=1):
        playlist_folder = os.path.join(download_folder, f"playlist_{idx}")
        playlist_folders.append(playlist_folder)
        t = threading.Thread(target=download_playlist, args=(playlist_url, playlist_folder, audio_quality))
        t.start()
        download_threads.append(t)

    for t in download_threads:
        t.join()
    print("[Main] All playlist downloads and conversions completed.")

    # Walk the download folder to find all MP3 files for transcription.
    mp3_files = []
    for root, dirs, files in os.walk(download_folder):
        for file in files:
            if file.lower().endswith(".mp3"):
                mp3_files.append(os.path.join(root, file))
    print(f"[Main] Found {len(mp3_files)} MP3 files for transcription.")

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

    # For each playlist folder, merge the individual transcript files.
    for folder in playlist_folders:
        merge_transcripts_for_playlist(folder)

if __name__ == "__main__":
    main()