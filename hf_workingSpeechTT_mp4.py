import os
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip

# --- Configuration ---
# Folder where your video files are located.
VIDEO_FOLDER = "/Volumes/HezeSamsung/Lectures/Mec/rec"
# Allowed video file extension.
VIDEO_EXTENSIONS = [".mp4"]
# Progress message interval in seconds.
PROGRESS_INTERVAL = 30
# Language for transcription.
LANGUAGE = "en"
# Model identifier from Hugging Face (e.g., "distil-large-v3").
MODEL_ID = "distil-large-v3"
# ----------------------

def is_video_file(filename: str) -> bool:
    """Check if a file is a video file based on its extension."""
    return any(filename.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)

# Load the Whisper model once for processing.
model = WhisperModel(MODEL_ID)

# Process each video file in the folder.
for filename in os.listdir(VIDEO_FOLDER):
    if is_video_file(filename):
        video_path = os.path.join(VIDEO_FOLDER, filename)
        base_name = os.path.splitext(filename)[0]
        # Define the path for the converted MP3 audio.
        audio_path = os.path.join(VIDEO_FOLDER, base_name + ".mp3")
        
        print(f"\nProcessing video file: {video_path}")
        
        # Convert MP4 to MP3 using MoviePy.
        with VideoFileClip(video_path) as video:
            # Extract and write the audio to an MP3 file.
            video.audio.write_audiofile(audio_path, logger=None)
        print(f"Converted '{filename}' to audio file: {audio_path}")
        
        # Transcribe the generated MP3 audio file.
        segments, info = model.transcribe(
            audio_path,
            language=LANGUAGE,
            condition_on_previous_text=False
        )
        
        transcript_lines = []
        next_progress = PROGRESS_INTERVAL
        
        # Collect transcript text from each segment.
        for segment in segments:
            transcript_lines.append(segment.text)
            # Print a progress message at every 30-second interval.
            if segment.start >= next_progress:
                print(f"Reached approximately {int(segment.start)} seconds in '{filename}'")
                next_progress += PROGRESS_INTERVAL
        
        # Combine all the segment texts into one full transcript.
        full_transcript = "\n".join(transcript_lines)
        
        # Save the full transcript to a text file.
        transcript_file = os.path.join(VIDEO_FOLDER, base_name + ".txt")
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(full_transcript)
        
        print(f"Transcription saved to: {transcript_file}")