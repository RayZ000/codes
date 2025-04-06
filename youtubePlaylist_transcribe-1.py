import os
import yt_dlp
from faster_whisper import WhisperModel

def download_audio_playlist(playlist_url, audio_format="mp3", quality="bestaudio", download_folder="."):
    """
    Download the audio from every video in the provided YouTube playlist URL,
    converting each video to the specified audio format.

    Parameters:
      playlist_url (str): URL of the playlist to download.
      audio_format (str): Target audio format (e.g., "mp3", "m4a", "wav"). Defaults to "mp3".
      quality (str): Audio quality selector (e.g., "bestaudio", "worstaudio"). Defaults to "bestaudio".
      download_folder (str): Directory where the audio files will be saved.
                             Defaults to the current directory.
    """
    os.makedirs(download_folder, exist_ok=True)
    outtmpl = os.path.join(download_folder, "%(title)s [%(id)s].%(ext)s")
    
    ydl_opts = {
        'format': quality,
        'ignoreerrors': True,
        'playlist_items': '1-',  # Download all videos.
        'outtmpl': outtmpl,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': '192',
        }],
        'keepvideo': False,  # Delete video file after extracting audio.
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])

def transcribe_audio_file(audio_path, model, language="en"):
    """
    Transcribe the given audio file using the provided WhisperModel instance.
    Returns the transcription text (without timestamps).
    
    Parameters:
      audio_path (str): Path to the downloaded audio file.
      model (WhisperModel): A loaded Faster-Whisper model.
      language (str): Language code for transcription.
    """
    segments, info = model.transcribe(audio_path, language=language, condition_on_previous_text=False)
    transcript = "\n".join(segment.text for segment in segments)
    return transcript

def main():

    # ---------------------------------------------------
    # ---------------------------------------------------
    # ---------------------------------------------------
    # ---------------------------------------------------
    # ---------------------------------------------------
    # URL of the YouTube playlist.
    playlist_url = "https://www.youtube.com/playlist?list=PLd9hKAUC3AZuo7is-aN45pmfDwJHOqKAj"
    
    # Audio extraction settings.
    audio_format = "mp3"        # Format to convert to.
    quality = "worstaudio"        # Can be "bestaudio" or "worstaudio".
    
    # Folder where the audio files will be downloaded.
    download_folder = "/Volumes/HezeSamsung/Lectures/Simons Solid Sate Basics"
    
    # Folder where the transcript text files will be stored.
    transcript_folder = "/Volumes/HezeSamsung/Lectures/Simons Solid Sate Basics"
    
    # Switch: True to merge all transcripts into one file; False to keep individual files.
    merge_transcripts = False
    
    # Switch: True to delete audio (and video) files after transcription.
    delete_files = True
    
    # Language for transcription.
    language = "en"
    # ---------------------------------------------------
    # ---------------------------------------------------
    # ---------------------------------------------------
    # ---------------------------------------------------
    # ---------------------------------------------------

    os.makedirs(download_folder, exist_ok=True)
    os.makedirs(transcript_folder, exist_ok=True)
    
    print("Starting audio download from playlist...")
    download_audio_playlist(playlist_url, audio_format, quality, download_folder)
    print("Audio download complete.\n")
    
    print("Loading transcription model...")
    model = WhisperModel("distil-large-v3")
    
    # If merging transcripts, define a merged output file.
    if merge_transcripts:
        merged_output_file = os.path.join(transcript_folder, "merged_transcripts.txt")
        # Clear any previous content.
        with open(merged_output_file, "w", encoding="utf-8") as f:
            f.write("")
    
    # Process each downloaded audio file.
    for filename in os.listdir(download_folder):
        if filename.lower().endswith("." + audio_format.lower()):
            audio_path = os.path.join(download_folder, filename)
            transcript_text = transcribe_audio_file(audio_path, model, language)
            
            if merge_transcripts:
                with open(merged_output_file, "a", encoding="utf-8") as mf:
                    mf.write(f"Transcript for {filename}:\n")
                    mf.write(transcript_text + "\n\n")
                print(f"Appended transcription of '{filename}' to merged file.")
            else:
                transcript_filename = os.path.splitext(filename)[0] + ".txt"
                transcript_path = os.path.join(transcript_folder, transcript_filename)
                with open(transcript_path, "w", encoding="utf-8") as f:
                    f.write(transcript_text)
                print(f"Transcription saved to: {transcript_path}")
            
            # Optionally delete the audio file after transcription.
            if delete_files:
                try:
                    os.remove(audio_path)
                    print(f"Deleted audio file: {audio_path}")
                except Exception as e:
                    print(f"Error deleting {audio_path}: {e}")

if __name__ == "__main__":
    main()