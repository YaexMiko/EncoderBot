from pyrogram import filters
from bot import app, data, sudo_users
from bot.helper.utils import add_task
from pyrogram import types

video_mimetype = [
    "video/x-flv",
    "video/mp4",
    "application/x-mpegURL",
    "video/MP2T",
    "video/3gpp",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-ms-wmv",
    "video/x-matroska",
    "video/webm",
    "video/x-m4v",
    "video/quicktime",
    "video/mpeg"
]

@app.on_message(filters.incoming & filters.command(['start', 'help']))
async def help_message(client, message):
    await message.reply_text(f"Hey {message.from_user.mention()} 🐭\nYou Know What I Can Do Right ?", quote=True)

@app.on_message(filters.user(sudo_users) & filters.incoming & (filters.video | filters.document))
async def encode_video(client, message):
    if message.document:
        if message.document.mime_type not in video_mimetype:
            await message.reply_text("Invalid Video Format !\nMake Sure Its a Supported Video File 🐭", quote=True)
            return
    await message.reply_text("Added To Queue 🐭", quote=True)
    data.append(message)
    if len(data) == 1:
        await add_task(message)

app.run()
