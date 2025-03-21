import os
import time
import subprocess
from bot import data, download_dir
from pyrogram.types import Message
from .ffmpeg_utils import get_thumbnail, get_duration, get_width_height

def format_time(seconds):
    """
    Format time in seconds to a human-readable format (e.g., 2m 30s).
    """
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}m {seconds}s"

def progress_bar(percentage):
    """
    Generate a progress bar based on the percentage.
    """
    filled = int(percentage // 10)
    return '█' * filled + '░' * (10 - filled)

def on_task_complete():
    """
    Remove the completed task from the queue and start the next one.
    """
    del data[0]
    if len(data) > 0:
        add_task(data[0])

def encode(input_file, progress_callback=None):
    """
    Encode the video using FFmpeg with x265 codec and provide real-time progress updates.
    """
    output_file = input_file.replace(".mp4", "_encoded.mp4")
    
    command = [
        "ffmpeg", "-y", "-i", input_file,
        "-c:v", "libx265", "-preset", "fast", "-crf", "28",
        "-c:a", "aac", "-b:a", "128k",
        output_file
    ]
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    total_frames = None
    for line in process.stderr:
        if "frame=" in line:
            parts = line.split()
            frame_index = next((i for i, p in enumerate(parts) if "frame=" in p), None)
            if frame_index is not None:
                try:
                    current_frame = int(parts[frame_index + 1])
                    if total_frames is None:
                        total_frames = 10000  # Approximate total frame count
                    
                    progress = (current_frame / total_frames) * 100
                    eta = (100 - progress) * 0.1  # Estimate time remaining
                    
                    if progress_callback:
                        progress_callback(progress, eta)
                except ValueError:
                    continue
    
    process.wait()

    return output_file if process.returncode == 0 else None

def add_task(message: Message):
    """
    Handle the task of downloading, encoding, and uploading a video with progress updates.
    """
    try:
        # Downloading
        msg = message.reply_text("Downloading...\nProgress: 0%\n[░░░░░░░░░░]\nSize: 0.00 MB of 0.00 MB\nSpeed: 0.00 MB/s\nETA: 0s\nElapsed: 0s", quote=True)
        
        def download_progress(current, total):
            progress = (current / total) * 100
            speed = current / (time.time() - start_time)
            eta = (total - current) / speed if speed > 0 else 0
            elapsed = time.time() - start_time
            msg.edit_text(
                f"Downloading...\n"
                f"Progress: {progress:.2f}%\n"
                f"[{progress_bar(progress)}]\n"
                f"Size: {current / 1024 / 1024:.2f} MB of {total / 1024 / 1024:.2f} MB\n"
                f"Speed: {speed / 1024 / 1024:.2f} MB/s\n"
                f"ETA: {format_time(eta)}\n"
                f"Elapsed: {format_time(elapsed)}"
            )
        
        start_time = time.time()
        filepath = message.download(file_name=download_dir, progress=download_progress)
        
        # Encoding
        msg.edit_text("Encoding...\nProgress: 0%\n[░░░░░░░░░░]\nETA: 0s")
        
        def encode_progress(progress, eta):
            msg.edit_text(
                f"Encoding...\n"
                f"Progress: {progress:.2f}%\n"
                f"[{progress_bar(progress)}]\n"
                f"ETA: {format_time(eta)}"
            )
        
        new_file = encode(filepath, progress_callback=encode_progress)
        
        if new_file:
            # Uploading
            msg.edit_text("Uploading...\nProgress: 0%\nSize: 0.00 MB of 0.00 MB\nSpeed: 0.00 MB/s\nETA: 0s\nElapsed: 0s")
            
            def upload_progress(current, total):
                progress = (current / total) * 100
                speed = current / (time.time() - start_time)
                eta = (total - current) / speed if speed > 0 else 0
                elapsed = time.time() - start_time
                msg.edit_text(
                    f"Uploading...\n"
                    f"Progress: {progress:.2f}%\n"
                    f"Size: {current / 1024 / 1024:.2f} MB of {total / 1024 / 1024:.2f} MB\n"
                    f"Speed: {speed / 1024 / 1024:.2f} MB/s\n"
                    f"ETA: {format_time(eta)}\n"
                    f"Elapsed: {format_time(elapsed)}"
                )
            
            start_time = time.time()
            message.reply_video(
                new_file,
                quote=True,
                supports_streaming=True,
                progress=upload_progress,
                thumb=get_thumbnail(new_file, download_dir, get_duration(new_file) / 4),
                duration=get_duration(new_file),
                width=get_width_height(new_file)[0],
                height=get_width_height(new_file)[1]
            )
            os.remove(new_file)
            msg.edit_text("Video Successfully Encoded to x265 🐭")
        else:
            msg.edit_text("Something Went Wrong While Encoding :(\nTry Again Later 🐭")
            os.remove(filepath)
    except Exception as e:
        msg.edit_text(f"```{e}```")
    on_task_complete()
