import os
import time
from bot import data, download_dir
from pyrogram.types import Message
from .ffmpeg_utils import encode, get_thumbnail, get_duration, get_width_height

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

async def add_task(message: Message):
    """
    Handle the task of downloading, encoding, and uploading a video with progress updates.
    """
    try:
        # Downloading
        msg = await message.reply_text("Downloading...\nProgress: 0%\n[░░░░░░░░░░]\nSize: 0.00 MB of 0.00 MB\nSpeed: 0.00 MB/s\nETA: 0s\nElapsed: 0s", quote=True)
        
        last_update_time = time.time()
        
        async def download_progress(current, total):
            nonlocal last_update_time
            current_time = time.time()
            if current_time - last_update_time < 5:  # Update every 5 seconds
                return
            
            progress = (current / total) * 100
            speed = current / (current_time - start_time)
            eta = (total - current) / speed if speed > 0 else 0
            elapsed = current_time - start_time
            await msg.edit_text(
                f"Downloading...\n"
                f"Progress: {progress:.2f}%\n"
                f"[{progress_bar(progress)}]\n"
                f"Size: {current / 1024 / 1024:.2f} MB of {total / 1024 / 1024:.2f} MB\n"
                f"Speed: {speed / 1024 / 1024:.2f} MB/s\n"
                f"ETA: {format_time(eta)}\n"
                f"Elapsed: {format_time(elapsed)}"
            )
            last_update_time = current_time
        
        start_time = time.time()
        filepath = await message.download(file_name=download_dir, progress=download_progress)
        
        # Encoding
        await msg.edit_text("Encoding...\nProgress: 0%\n[░░░░░░░░░░]\nETA: 0s")
        
        last_update_time = time.time()
        
        def encode_progress(progress, eta):
            nonlocal last_update_time
            current_time = time.time()
            if current_time - last_update_time < 5:  # Update every 5 seconds
                return
            
            msg.edit_text(
                f"Encoding...\n"
                f"Progress: {progress:.2f}%\n"
                f"[{progress_bar(progress)}]\n"
                f"ETA: {format_time(eta)}"
            )
            last_update_time = current_time
        
        new_file = encode(filepath, progress_callback=encode_progress)
        
        if new_file:
            # Uploading
            await msg.edit_text("Uploading...\nProgress: 0%\nSize: 0.00 MB of 0.00 MB\nSpeed: 0.00 MB/s\nETA: 0s\nElapsed: 0s")
            
            last_update_time = time.time()
            
            async def upload_progress(current, total):
                nonlocal last_update_time
                current_time = time.time()
                if current_time - last_update_time < 5:  # Update every 5 seconds
                    return
                
                progress = (current / total) * 100
                speed = current / (current_time - start_time)
                eta = (total - current) / speed if speed > 0 else 0
                elapsed = current_time - start_time
                await msg.edit_text(
                    f"Uploading...\n"
                    f"Progress: {progress:.2f}%\n"
                    f"Size: {current / 1024 / 1024:.2f} MB of {total / 1024 / 1024:.2f} MB\n"
                    f"Speed: {speed / 1024 / 1024:.2f} MB/s\n"
                    f"ETA: {format_time(eta)}\n"
                    f"Elapsed: {format_time(elapsed)}"
                )
                last_update_time = current_time
            
            start_time = time.time()
            await message.reply_video(
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
            await msg.edit_text("Video Successfully Encoded to x265 🐭")
        else:
            await msg.edit_text("Something Went Wrong While Encoding :(\nTry Again Later 🐭")
            os.remove(filepath)
    except Exception as e:
        await msg.edit_text(f"```{e}```")
    on_task_complete()
