import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import random 
import json


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file located in the 'environmental' folder
load_dotenv(dotenv_path='/home/DiscordPi/code/discord_bots/memb-assign-bot/environmental/.env')  
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
WELCOME_CHANNEL = os.getenv('WELCOME_CHANNEL')

# Check if GUILD_ID is  loaded
if GUILD_ID is None:
    raise ValueError("GUILD_ID is not set in the .env file.")

GUILD_ID = int(GUILD_ID)  # Convert after checking 

# Initialize bot with intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  

# Bot initialization
bot = commands.Bot(command_prefix="!", intents=intents)

# Variables for role names and emojis
GANG_ROLE_NAME = "Gang Members"
STALLIONS_ROLE_NAME = "The Stallions"
BOTS_ROLE_NAME = "Bots"
EMOJI_APPROVE = "✅" 
EMOJI_DENY = "❌"  

welc_msg_bot_path = os.getenv("welcome_member_messages")
welc_msg_memb_path = os.getenv('welcome_bot_messages')