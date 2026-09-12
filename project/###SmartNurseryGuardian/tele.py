import asyncio
from telegram.ext import ApplicationBuilder

async def send_message(token, chat_id, text):
    application = ApplicationBuilder().token("8843566763:AAHWOXuEpcTzH6hjY9RURnJNJOGfri294QU").build()
    # Initialize the bot
    application = ApplicationBuilder().token(token).build()
    
    # Send the message
    await application.bot.send_message(chat_id=chat_id, text=text)

asyncio.run(send_message("8843566763:AAHWOXuEpcTzH6hjY9RURnJNJOGfri294QU", "5058417837", "ابنك بيتحرق"))