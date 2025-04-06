import os
import yt_dlp

def download_youtube_videos(urls, video_resolution=None, audio_quality=None, download_folder="."):
    """
    Download one or more YouTube videos from the given list of URLs,
    using the desired video resolution and audio quality, and saving
    them in the specified download folder.

    Parameters:
      urls (list): List of YouTube video URLs.
      video_resolution (str or None): Maximum video height (e.g., "720" for 720p).
                                      If None, no video resolution constraint is applied.
      audio_quality (str or None): Maximum audio bitrate (e.g., "192" for 192 kbps).
                                   If None, no audio bitrate constraint is applied.
      download_folder (str): Path to the folder where files will be saved.
    """
    # Ensure the download folder exists.
    os.makedirs(download_folder, exist_ok=True)
    
    # Build the format selector based on user inputs.
    if video_resolution and audio_quality:
        # Filter video by height and audio by average bitrate.
        format_str = f"bestvideo[height<=?{video_resolution}]+bestaudio[abr<=?{audio_quality}]/best"
    elif video_resolution:
        format_str = f"bestvideo[height<=?{video_resolution}]+bestaudio/best"
    elif audio_quality:
        format_str = f"bestvideo+bestaudio[abr<=?{audio_quality}]/best"
    else:
        format_str = "best"
    
    # Construct the output template so that downloads go into the chosen folder.
    outtmpl = os.path.join(download_folder, "%(title)s [%(id)s].%(ext)s")
    
    # yt-dlp options.
    ydl_opts = {
        'format': format_str,
        'outtmpl': outtmpl,
        'ignoreerrors': True,  # Skip videos that error out.
    }
    
    # Download the videos.
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)

if __name__ == "__main__":
    # Prompt the user for a list of YouTube URLs (comma separated).
    urls_input = input("Enter YouTube URL(s) separated by commas: ")
    urls = [url.strip() for url in urls_input.split(",") if url.strip()]

    # Prompt for desired maximum video resolution (e.g. 720 for 720p).
    video_resolution = input("Enter desired video resolution (e.g., 720 for 720p, leave blank for best): ").strip()
    if not video_resolution:
        video_resolution = None

    # Prompt for desired maximum audio bitrate (in kbps, e.g. 192).
    audio_quality = input("Enter desired maximum audio bitrate in kbps (e.g., 192, leave blank for best): ").strip()
    if not audio_quality:
        audio_quality = None

    # Prompt for download folder.
    download_folder = input("Enter download folder (default is current directory): ").strip()
    if not download_folder:
        download_folder = "."

    # Start downloading.
    download_youtube_videos(urls, video_resolution, audio_quality, download_folder)