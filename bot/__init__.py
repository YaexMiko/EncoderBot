import os
from pyrogram import Client
from dotenv import load_dotenv

#if os.path.exists('config.env'):
#  load_dotenv('config.env')

api_id = int(os.environ.get('API_ID', "28614709"))
api_hash = os.environ.get('API_HASH', "f36fd2ee6e3d3a17c4d244ff6dc1bac8")
bot_token = os.environ.get('BOT_TOKEN', "7412589100:AAH3thhFXvNyP-5mw6q1vP399Xb4EEM98P4")
download_dir = os.environ.get("DOWNLOAD_DIR", "downloads/")
sudo_users = list(set(int(x) for x in os.environ.get('SUDO_USERS', "7604092691").split()))

app = Client(":memory:", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

data = []

if not download_dir.endswith("/"):
  download_dir = str(download_dir) + "/"
if not os.path.isdir(download_dir):
  os.makedirs(download_dir)
