from pyrogram import Client, filters

API_ID = 29667286
API_HASH = "2dddc2f98e16161cb50e41971f9591be"
BOT_TOKEN = "7795185106:AAGMAOVgGchw-YEKWWHR_DEyBINpGMvOGNY"

app = Client("test_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text("✅ البوت شغال!")

app.run()
