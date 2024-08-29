import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

#Loading enviorment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID =int(os.getenv('GUILD_ID'))

#initalzing the intents for the bot 
intents = discord .Intents.default()
intents.members = True

#initalizing bot
bot = commands.Bot(command_prefix="!", intents = intents)

#constants for the given roles
NEW_MEMBER_ROLE_NAME = "Gang Members"
BOT_ROLE_NAME = "Bots"

#Event bot is ready