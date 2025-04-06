import os
import yt_dlp

def download_playlist(playlist_url, quality="best", download_folder="."):
    """
    Download every video in the provided playlist URL at the given quality,
    saving the files to the specified download folder.

    Parameters:
        playlist_url (str): The URL of the playlist.
        quality (str): The quality selector (e.g., "best", "720p", "bestvideo+bestaudio").
                       Defaults to "best".
        download_folder (str): The directory to save downloaded videos.
                               Defaults to the current directory.
    """
    # Ensure the download folder exists.
    os.makedirs(download_folder, exist_ok=True)
    
    # Create an output template that places the file in the specified folder.
    outtmpl = os.path.join(download_folder, "%(title)s [%(id)s].%(ext)s")
    
    ydl_opts = {
        'format': quality,
        'ignoreerrors': True,   # Continue downloading even if one video fails.
        'playlist_items': '1-', # Download all items in the playlist.
        'outtmpl': outtmpl,     # Save files in the specified folder.
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])

# Example usage:
if __name__ == "__main__":
    # Replace the URL below with your target playlist URL.
    playlist_url = "https://www.youtube.com/playlist?list=PL8cOM__o7t6-P81mm5IzIp0wM06etqd9O"
    # Set the desired quality. For example: "best", "720p", or "bestvideo+bestaudio"
    quality = "worst"
    # Specify the download folder (it will be created if it doesn't exist).
    download_folder = "/Volumes/HezeSamsung/Lectures/COMSOLIndianGuide"
    
    download_playlist(playlist_url, quality, download_folder)