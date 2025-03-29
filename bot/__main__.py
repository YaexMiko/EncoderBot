import os
import time
from datetime import datetime
import humanize
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import app, bot_data
from bot.helper.utils import add_task, update_stats

video_mimetype = [
    "video/x-flv", "video/mp4", "application/x-mpegURL", "video/MP2T",
    "video/3gpp", "video/quicktime", "video/x-msvideo", "video/x-ms-wmv",
    "video/x-matroska", "video/webm", "video/x-m4v", "video/quicktime", "video/mpeg"
]

@app.on_message(filters.incoming & filters.command(['start', 'help']))
def help_message(app, message):
    help_text = f"""
Hey {message.from_user.mention()} 🐭

**Encoder Bot Help:**
- Send me a video file to encode it to HEVC
- You can customize encoding with commands:
  `/encode crf=28 preset=medium audio=128k`
  
**Admin Commands:**
- `/queue` - Show current encoding queue
- `/stats` - Show bot statistics
- `/restart` - Restart the bot (admin only)
- `/broadcast` - Send message to all users (admin only)
"""
    message.reply_text(help_text, quote=True)

@app.on_message(filters.user(bot_data.sudo_users) & filters.incoming & filters.command('encode'))
def encode_command(app, message):
    try:
        crf = 28
        preset = 'medium'
        audio_bitrate = '128k'
        custom_thumbnail = None
        
        if message.reply_to_message:
            if len(message.command) > 1:
                args = message.text.split()[1:]
                for arg in args:
                    if 'crf=' in arg:
                        crf = int(arg.split('=')[1])
                    elif 'preset=' in arg:
                        preset = arg.split('=')[1]
                    elif 'audio=' in arg:
                        audio_bitrate = arg.split('=')[1] + 'k'
            
            if message.reply_to_message.video or message.reply_to_message.document:
                message.reply_text("Added To Queue With Custom Settings 🐭", quote=True)
                bot_data.data.append((message.reply_to_message, crf, preset, audio_bitrate, custom_thumbnail))
                if len(bot_data.data) == 1:
                    add_task(*bot_data.data[0])
            else:
                message.reply_text("Reply to a video file to encode it 🐭", quote=True)
        else:
            message.reply_text("Reply to a video file with this command 🐭", quote=True)
    except Exception as e:
        message.reply_text(f"Error: {e}", quote=True)

@app.on_message(filters.user(bot_data.sudo_users) & filters.incoming & (filters.video | filters.document))
def encode_video(app, message):
    if message.document and not message.document.mime_type in video_mimetype:
        message.reply_text("Invalid Video Format!\nMake Sure Its a Supported Video File 🐭", quote=True)
        return
    message.reply_text("Added To Queue 🐭", quote=True)
    bot_data.data.append((message, 28, 'medium', '128k', None))
    if len(bot_data.data) == 1:
        add_task(*bot_data.data[0])

@app.on_message(filters.user(bot_data.sudo_users) & filters.incoming & filters.command('queue'))
def show_queue(app, message):
    if not bot_data.data:
        message.reply_text("Queue is empty 🐭", quote=True)
    else:
        queue_text = "**Current Queue:**\n"
        for i, item in enumerate(bot_data.data, 1):
            msg = item[0]
            queue_text += f"{i}. {msg.video.file_name if msg.video else msg.document.file_name}\n"
        message.reply_text(queue_text, quote=True)

@app.on_message(filters.user(bot_data.sudo_users) & filters.incoming & filters.command('stats'))
def show_stats(app, message):
    uptime = humanize.precisedelta(time.time() - bot_data.stats['start_time'])
    stats_text = f"""
**Bot Statistics:**
- Total Encoded Videos: {bot_data.stats['total']}
- Today's Encodes: {bot_data.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), 0)}
- Uptime: {uptime}
- Queue Length: {len(bot_data.data)}
"""
    message.reply_text(stats_text, quote=True)

@app.on_message(filters.user(bot_data.sudo_users) & filters.incoming & filters.command('restart'))
def restart_bot(app, message):
    message.reply_text("Restarting bot...", quote=True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@app.on_message(filters.user(bot_data.sudo_users) & filters.incoming & filters.command('broadcast'))
def broadcast_message(app, message):
    if len(message.command) < 2:
        message.reply_text("Usage: /broadcast <message>", quote=True)
        return
    
    broadcast_text = ' '.join(message.command[1:])
    message.reply_text(
        f"Confirm broadcast:\n{broadcast_text}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Confirm", callback_data="broadcast_confirm")],
            [InlineKeyboardButton("Cancel", callback_data="broadcast_cancel")]
        ])
    )

@app.on_callback_query(filters.regex('^broadcast_'))
def handle_broadcast_callback(app, callback_query):
    if callback_query.data == 'broadcast_confirm':
        users = []  # Implement user tracking as needed
        callback_query.message.edit("Broadcasting to users...")
        for user in users:
            try:
                app.send_message(user.id, callback_query.message.text)
            except:
                pass
        callback_query.message.edit("Broadcast completed!")
    else:
        callback_query.message.edit("Broadcast cancelled")

app.run()
