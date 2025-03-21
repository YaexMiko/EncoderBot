import os
import time
import re
import ffmpeg
from subprocess import Popen, PIPE
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from bot import data, download_dir
from pyrogram.types import Message

# ────────────────────────────────
# 🔹 Utility Functions
# ────────────────────────────────

def format_time(seconds):
    """Convert seconds to a human-readable format."""
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}m {seconds}s"

def progress_bar(percentage):
    """Generate a progress bar for visual representation."""
    filled = int(percentage // 10)
    return '█' * filled + '░' * (10 - filled)

def on_task_complete():
    """Remove completed task and start the next one if available."""
    del data[0]
    if len(data) > 0:
        add_task(data[0])

# ────────────────────────────────
# 🔹 FFmpeg Encoding Functions
# ────────────────────────────────

def get_codec(filepath, channel='v:0'):
    """Get codec info for a video or audio stream."""
    from subprocess import check_output
    output = check_output(['ffprobe', '-v', 'error', '-select_streams', channel,
                           '-show_entries', 'stream=codec_name,codec_tag_string',
                           '-of', 'default=nokey=1:noprint_wrappers=1', filepath])
    return output.decode('utf-8').split()

def encode(filepath, progress_callback=None):
    """Convert video to HEVC format with progress updates."""
    basefilepath, extension = os.path.splitext(filepath)
    output_filepath = basefilepath + '.[HEVC].mp4'

    if os.path.isfile(output_filepath):
        print(f'File "{output_filepath}" already exists, overwriting 🐭')
        os.remove(output_filepath)
    
    print(f'Processing file: {filepath}')
    
    # Set encoding options
    video_opts = '-c:v libx265 -crf 28 -tag:v hvc1 -preset medium -threads 8'
    
    # Check audio codec
    audio_codec = get_codec(filepath, channel='a:0')
    if not audio_codec:
        audio_opts = ''  # No audio stream
    elif audio_codec[0] == 'aac':
        audio_opts = '-c:a copy'  # Copy AAC audio stream
    else:
        audio_opts = '-c:a aac -b:a 128k'  # Transcode non-AAC audio to AAC
    
    # Run FFmpeg
    command = ['ffmpeg', '-y', '-i', filepath, '-map', '0'] + video_opts.split() + audio_opts.split() + [output_filepath]
    process = Popen(command, stderr=PIPE, universal_newlines=True)
    
    total_duration = get_duration(filepath)
    start_time = time.time()
    
    # Regex for extracting encoding progress
    time_regex = re.compile(r'time=(\d{2}:\d{2}:\d{2}\.\d{2})')
    
    for line in process.stderr:
        if progress_callback:
            match = time_regex.search(line)
            if match:
                current_time_str = match.group(1)
                current_time = sum(float(x) * 60 ** i for i, x in enumerate(reversed(current_time_str.split(':'))))
                progress = (current_time / total_duration) * 100
                elapsed_time = time.time() - start_time
                eta = (elapsed_time / progress) * (100 - progress) if progress > 0 else 0
                progress_callback(progress, eta)
    
    process.wait()
    
    if process.returncode != 0:
        print("Encoding failed!")
        return None
    
    os.remove(filepath)  # Remove original file
    return output_filepath

def get_thumbnail(filepath, path, ttl):
    """Generate a video thumbnail."""
    out_filename = os.path.join(path, f"thumb_{int(time.time())}.jpg")
    try:
        (
            ffmpeg
            .input(filepath, ss=ttl)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return out_filename
    except ffmpeg.Error as e:
        print(f'Error generating thumbnail: {e.stderr.decode()}')
        return None

def get_duration(filepath):
    """Get video duration in seconds."""
    metadata = extractMetadata(createParser(filepath))
    return metadata.get('duration').seconds if metadata and metadata.has("duration") else 0

def get_width_height(filepath):
    """Get video resolution."""
    metadata = extractMetadata(createParser(filepath))
    return (metadata.get("width"), metadata.get("height")) if metadata and metadata.has("width") and metadata.has("height") else (1280, 720)

# ────────────────────────────────
# 🔹 Task Handling Functions
# ────────────────────────────────

def add_task(message: Message):
    """Handle downloading, encoding, and uploading a video with progress updates."""
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
            msg.edit_text("Uploading...\nProgress: 0%")
            
            start_time = time.time()
            message.reply_video(
                new_file,
                quote=True,
                supports_streaming=True,
                thumb=get_thumbnail(new_file, download_dir, get_duration(new_file) / 4),
                duration=get_duration(new_file),
                width=get_width_height(new_file)[0],
                height=get_width_height(new_file)[1]
            )
            os.remove(new_file)
            msg.edit_text("Video Successfully Encoded to x265 🐭")
        else:
            msg.edit_text("Encoding failed. Try again later 🐭")
            os.remove(filepath)
    
    except Exception as e:
        msg.edit_text(f"Error: {e}")
    on_task_complete()
