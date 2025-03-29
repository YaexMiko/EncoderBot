import os
import time
from datetime import datetime
import humanize
from bot import bot_data
from pyrogram.types import Message
from .ffmpeg_utils import encode, get_thumbnail, get_duration, get_width_height

def update_stats(action):
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in bot_data.stats['daily']:
        bot_data.stats['daily'][today] = 0
    bot_data.stats['total'] += 1
    bot_data.stats['daily'][today] += 1

def on_task_complete():
    if bot_data.data:
        del bot_data.data[0]
        if bot_data.data:
            add_task(*bot_data.data[0])

def progress_callback(current, total, msg, start_time):
    elapsed = time.time() - start_time
    speed = current / elapsed if elapsed > 0 else 0
    percentage = current * 100 / total
    msg.edit(f"Downloading... {percentage:.1f}%\n"
             f"Speed: {humanize.naturalsize(speed)}/s\n"
             f"Elapsed: {humanize.precisedelta(elapsed)}")

def encoding_progress(progress, msg):
    msg.edit(f"Encoding... {progress:.1f}% 🐭")

def add_task(message: Message, crf=28, preset='medium', audio_bitrate='128k', custom_thumbnail=None):
    try:
        start_time = time.time()
        msg = message.reply_text("Downloading 🐭", quote=True)
        
        filepath = message.download(
            file_name=bot_data.download_dir,
            progress=progress_callback,
            progress_args=(msg, start_time)
        )
        
        msg.edit("Encoding 🐭")
        new_file = encode(
            filepath,
            crf=crf,
            preset=preset,
            audio_bitrate=audio_bitrate,
            progress_callback=lambda p: encoding_progress(p, msg)
        )
        
        if new_file:
            update_stats('encode')
            msg.edit("Video Encoded Successfully\nGetting Metadata 🐭")
            duration = get_duration(new_file)
            thumb = get_thumbnail(new_file, bot_data.download_dir, duration / 4, custom_thumbnail)
            width, height = get_width_height(new_file)
            
            msg.edit("Uploading 🐭")
            message.reply_video(
                new_file,
                quote=True,
                supports_streaming=True,
                thumb=thumb,
                duration=duration,
                width=width,
                height=height,
                progress=progress_callback,
                progress_args=(msg, time.time())
            )
            
            os.remove(new_file)
            if thumb and not custom_thumbnail:
                os.remove(thumb)
            msg.edit("Video Successfully Encoded to x265 🐭")
        else:
            msg.edit("Something Went Wrong While Encoding :(\nTry Again Later 🐭")
            os.remove(filepath)
    except Exception as e:
        msg.edit(f"```{e}```")
    on_task_complete()
