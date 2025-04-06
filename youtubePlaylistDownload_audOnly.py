import os
import yt_dlp

def download_audio_playlist(playlist_url, audio_format="mp3", quality="bestaudio", download_folder="."):
    """
    Download the audio of every video in the provided playlist URL, converting
    each video to the specified audio format.

    Parameters:
        playlist_url (str): URL of the playlist to download.
        audio_format (str): Target audio format (e.g., "mp3", "m4a", "wav").
                            Defaults to "mp3".
        quality (str): Audio quality selector. Typically "bestaudio" works well.
                       Defaults to "bestaudio".
        download_folder (str): Directory where the audio files will be saved.
                               Defaults to the current directory.
    """
    # Ensure the download folder exists
    os.makedirs(download_folder, exist_ok=True)
    
    # Construct an output template to store the files in the download folder.
    outtmpl = os.path.join(download_folder, "%(title)s [%(id)s].%(ext)s")
    
    # Set yt-dlp options, including postprocessor to extract audio
    ydl_opts = {
        'format': quality,
        'ignoreerrors': True,   # Continue with next video if one fails.
        'playlist_items': '1-', # Download all videos in the playlist.
        'outtmpl': outtmpl,     # Output file naming template.
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',      # Use ffmpeg to extract audio.
            'preferredcodec': audio_format,     # Convert to the specified audio format.
            'preferredquality': '192',          # Set the audio quality (bitrate in kbps).
        }],
        # Optionally, you can remove the original video file after conversion:
        # 'keepvideo': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])

# Example usage:
if __name__ == "__main__":
    # Replace with your playlist URL.
    playlist_url = "https://www.youtube.com/playlist?list=PL8cOM__o7t6-P81mm5IzIp0wM06etqd9O"
    # Set the target audio format ("mp3", "m4a", "wav", etc.)
    audio_format = "mp3"
    # Use "bestaudio" to select the best available audio quality.
    quality = "worstaudio"
    # Specify a download folder (it will be created if it doesn't exist).
    download_folder = "/Volumes/HezeSamsung/Lectures/COMSOLIndianGuide/audOnly2"
    
    download_audio_playlist(playlist_url, audio_format, quality, download_folder)