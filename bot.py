import os
import telebot
import requests
from flask import Flask, request

# Configurations
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Use environment variable for bot token
CLOUDFLARE_WORKER_URL = os.getenv("CLOUDFLARE_WORKER_URL")  # Cloudflare Worker endpoint
ADMIN_ID = 6742022802  # Replace with your Telegram user ID

# Initialize bot and Flask app
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# Emoji definitions
EMOJI = {
    "robot": "🤖",
    "lightbulb": "💡",
    "image": "🖼️",
    "success": "✅",
    "thinking": "🤔",
    "alert": "🚨",
    "cogs": "⚙️"
}

# Commands
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@bot.message_handler(commands=['start'])
def start_command(message):
    welcome_text = f"""
{EMOJI['robot']} *Welcome! I am your AI-powered assistant.*

Available commands:
{EMOJI['lightbulb']} `/ai <question>` - Ask me anything!
{EMOJI['image']} `/image <description>` - Generate an image.

I’m here to assist you! 🤗
    """
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['ai'])
def ai_command(message):
    question = message.text[4:].strip()
    if not question:
        bot.reply_to(message, f"{EMOJI['alert']} Please provide a question for the AI.")
        return

    bot.reply_to(message, f"{EMOJI['thinking']} Thinking... Please wait!")

    # Request AI response from Cloudflare Worker
    response = requests.get(CLOUDFLARE_WORKER_URL, params={
        "command": "ai",
        "message": question
    })
    bot.reply_to(message, f"{EMOJI['success']} *Answer*: {response.text}", parse_mode="Markdown")

@bot.message_handler(commands=['image'])
def image_command(message):
    description = message.text[7:].strip()
    if not description:
        bot.reply_to(message, f"{EMOJI['alert']} Please provide a description for the image.")
        return

    bot.reply_to(message, f"{EMOJI['thinking']} Drawing... Hang tight!")

    # Request image from Cloudflare Worker
    response = requests.get(CLOUDFLARE_WORKER_URL, params={
        "command": "image",
        "message": description
    })

    if response.status_code == 200:
        bot.send_photo(message.chat.id, response.content, caption=f"{EMOJI['image']} *Here’s your image based on*: _{description}_", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"{EMOJI['alert']} Error generating image. Please try again.")

@bot.message_handler(commands=['changegptmodel'])
def change_model_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, f"{EMOJI['alert']} You are not authorized to change the model.")
        return

    model_path = message.text[15:].strip()
    if not model_path:
        bot.reply_to(message, f"{EMOJI['alert']} Please provide a model path.")
        return

    # Change model via Cloudflare Worker
    response = requests.get(CLOUDFLARE_WORKER_URL, params={
        "command": "changeModel",
        "message": model_path
    })
    bot.reply_to(message, f"{EMOJI['success']} Model changed to: *{model_path}*", parse_mode="Markdown")

# Flask route to handle webhook (if needed)
@app.route('/')
def index():
    return "Bot is running!"

# Flask handler to invoke polling (on serverless deployment)
def main():
    bot.remove_webhook()
    bot.polling(non_stop=True)

if __name__ == "__main__":
    main()
                     
