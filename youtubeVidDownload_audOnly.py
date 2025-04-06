import os
import yt_dlp

def download_youtube_audio(urls, audio_quality=None, download_folder="."):
    """
    Download the audio from one or more YouTube videos from the given list of URLs.
    The output is an MP3 file only (the video is deleted after extraction) and files
    are saved in the specified download folder.

    Parameters:
      urls (list): List of YouTube video URLs.
      audio_quality (str or None): Maximum audio bitrate (e.g., "192" for 192 kbps).
                                   If None, no audio bitrate constraint is applied.
      download_folder (str): Path to the folder where files will be saved.
    """
    # Ensure the download folder exists.
    os.makedirs(download_folder, exist_ok=True)
    
    # Build the format selector for audio only.
    if audio_quality:
        # Filter audio by average bitrate.
        format_str = f"bestaudio[abr<=?{audio_quality}]/bestaudio"
    else:
        format_str = "bestaudio/best"
    
    # Construct the output template (the final extension will be set to .mp3 by the postprocessor).
    outtmpl = os.path.join(download_folder, "%(title)s [%(id)s].%(ext)s")
    
    # Set yt-dlp options.
    ydl_opts = {
        'format': format_str,
        'outtmpl': outtmpl,
        'ignoreerrors': True,  # Skip videos that error out.
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',      # Extract audio using ffmpeg.
            'preferredcodec': 'mp3',            # Convert the audio to MP3.
            'preferredquality': '192',          # Set audio quality (bitrate in kbps).
        }],
        'keepvideo': False,  # Delete the video file after audio extraction.
    }
    
    # Download the audio from the provided URLs.
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)

if __name__ == "__main__":
    # Prompt the user for a list of YouTube URLs (comma separated).
    urls_input = "https://www.youtube.com/watch?v=CEke9IdN43A"
    #input("Enter YouTube URL(s) separated by commas: ")
    urls = [url.strip() for url in urls_input.split(",") if url.strip()]

    # Prompt for desired maximum audio bitrate (in kbps, e.g. 192).
    audio_quality = None
    #input("Enter desired maximum audio bitrate in kbps (e.g., 192, leave blank for best): ").strip()


    # Prompt for download folder.
    download_folder = "/Volumes/HezeSamsung/codes/nexa try py"

    # Start downloading audio.
    download_youtube_audio(urls, audio_quality, download_folder)