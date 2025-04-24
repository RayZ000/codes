# %%
# ToDo: test the behavior of podcast-archiver with placeholder mp3 files

import os
import subprocess
import mlx_whisper
import shutil

# --- Configuration ---
AUDIO_FOLDERS = [
    '/Volumes/HezeORICO/life/Huberman Lab', 
    '/Volumes/HezeORICO/life/独树不成林', 
    '/Volumes/HezeORICO/life/Lex Fridman Podcast' # , '/path/to/third/folder'
]

PARENT_FOLDER =  '/Volumes/HezeORICO/life'  # Replace with the actual parent folder path

# New: Podcast feed URLs corresponding to each folder
PODCAST_FEEDS = [
    'https://podcasts.apple.com/hk/podcast/huberman-lab/id1545953110',  # Replace with the actual feed URL for the first folder
    'https://podcasts.apple.com/hk/podcast/%E7%8B%AC%E6%A0%91%E4%B8%8D%E6%88%90%E6%9E%97/id1711052890',
    'https://podcasts.apple.com/hk/podcast/lex-fridman-podcast/id1434243584' # Replace with the actual feed URL for the second folder
    # Add more feeds as needed
]

# Destination base folder for backup of processed audio folders. Replace with your desired destination path.
DESTINATION_BASE_FOLDER = '/Volumes/HezeSamsung/life'

# Audio file extensions
AUDIO_EXTENSIONS = [".wav", ".mp3", ".flac", ".ogg", ".m4a"]
# Video file extensions that should be processed
VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv"]
PROGRESS_INTERVAL = 300
# Model repository identifier from Hugging Face.
MODEL_ID = "mlx-community/whisper-large-v3-turbo"
# ----------------------


def is_audio_file(filename: str) -> bool:
    """Check if a file is an audio file based on its extension."""
    return any(filename.lower().endswith(ext) for ext in AUDIO_EXTENSIONS)

def is_video_file(filename: str) -> bool:
    """Check if a file is a video file based on its extension."""
    return any(filename.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)

# Process each folder in AUDIO_FOLDERS along with their corresponding podcast feed
for folder, feed in zip(AUDIO_FOLDERS, PODCAST_FEEDS):
    # Run the podcast-archiver command to update podcasts for this folder
    # parent_folder is the directory where the podcast-archiver will save the files (automatically look for subfolders)
    update_cmd = ["podcast-archiver", "--dir", PARENT_FOLDER, "--feed", feed]
    print(f"\nUpdating podcast for folder: {folder} with feed: {feed}")
    subprocess.run(update_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    print(f"\nProcessing folder: {folder}")
    for filename in os.listdir(folder):
        # Skip hidden files and system files.
        if filename.startswith('._'):
            continue
        
        # Compute base name and output file path
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(folder, base_name + ".txt")
        
        # If the transcript already exists, skip processing this file
        if os.path.exists(output_file):
            print(f"Output file {output_file} already exists. Skipping {filename}.")
            continue
        
        file_path = os.path.join(folder, filename)
        input_path = None  # will be set to the file to transcribe
        
        if is_audio_file(filename):
            input_path = file_path
        elif is_video_file(filename):
            # Extract audio from video using ffmpeg.
            temp_audio_path = os.path.join(folder, base_name + "_extracted.mp3")
            print(f"\nExtracting audio from video file: {file_path}")
            ffmpeg_command = ["ffmpeg", "-y", "-i", file_path, "-q:a", "0", "-map", "a", temp_audio_path]
            subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            input_path = temp_audio_path
        else:
            # Skip files that are neither audio nor video.
            continue
        
        print(f"\nProcessing file: {input_path}")
        
        # Transcribe the file using mlx_whisper.
        result = mlx_whisper.transcribe(
            input_path,
            path_or_hf_repo=MODEL_ID
        )
        
        # Use the full transcript from the "text" key.
        full_transcript = result["text"]
        
        # Optionally, log progress based on the segments.
        next_progress = PROGRESS_INTERVAL
        for segment in result["segments"]:
            if segment["start"] >= next_progress:
                print(f"Reached approximately {int(segment['start'])} seconds in '{filename}'")
                next_progress += PROGRESS_INTERVAL
        
        # Write the full transcript to a text file.
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_transcript)
        
        print(f"Transcription saved to: {output_file}")
        
        # If a temporary audio file was created from a video, remove it.
        if is_video_file(filename) and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path) 



# Replace transcribed audio and video files with empty placeholder files.
for folder in AUDIO_FOLDERS:
    for filename in os.listdir(folder):
        # Process only audio or video files using defined helper functions
        if is_audio_file(filename) or is_video_file(filename):
            base_name = os.path.splitext(filename)[0]
            transcript_file = os.path.join(folder, base_name + ".txt")
            file_path = os.path.join(folder, filename)
            # If a transcript exists for this file, consider it transcribed
            if os.path.exists(transcript_file):
                print(f"Replacing {file_path} with a placeholder file.")
                # Remove the original file
                os.remove(file_path)
                # Create an empty (0-byte) placeholder file
                with open(file_path, "wb") as f:
                    pass  # Creates an empty file


# Copy processed audio folders to the backup destination
print("\nCopying processed audio folders to backup destination:")
for folder in AUDIO_FOLDERS:
    # Get the folder name (e.g., 'Huberman Lab') from the folder path
    folder_name = os.path.basename(os.path.normpath(folder))
    destination_folder = os.path.join(DESTINATION_BASE_FOLDER, folder_name)
    print(f"Copying contents of {folder} to {destination_folder}")
    # Recursively copy the folder and its contents. dirs_exist_ok=True allows merging if the folder exists.
    shutil.copytree(folder, destination_folder, dirs_exist_ok=True)
# %%
