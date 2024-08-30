import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging
import random
from sql_logger import initialize_database, log_member_event  # Import your SQL handler functions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file located in the 'environment' folder
load_dotenv(dotenv_path='environmental/.env')  # Ensure the path is correct
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

# Check if GUILD_ID is correctly loaded
if GUILD_ID is None:
    raise ValueError("GUILD_ID is not set in the .env file.")

GUILD_ID = int(GUILD_ID)  # Convert after checking for None

# Initialize bot with necessary intents
intents = discord.Intents.default()
intents.members = True

# Bot initialization
bot = commands.Bot(command_prefix="!", intents=intents)

# Constants for role names
GANG_ROLE_NAME = "Gang Members"
BOT_ROLE_NAME = "Bot"

# Welcome messages array
welcome_messages = [
    "Welcome to the server, {user}! We're glad to have you here!",
    "Hey {user}, welcome! Enjoy your stay!",
    "Greetings, {user}! Welcome aboard!",
    "Hello {user}! Happy to see you here!",
]

# Call the setup function to initialize the database
initialize_database()

# Event: Bot is ready
@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')

    # Automatically assign the bot role if it exists in each guild
    for guild in bot.guilds:
        bot_role = discord.utils.get(guild.roles, name=BOT_ROLE_NAME)
        if bot_role:
            await guild.me.add_roles(bot_role)
            logging.info(f'Assigned {BOT_ROLE_NAME} role to the bot in {guild.name}.')

# Event: New member joins the server
@bot.event
async def on_member_join(member):
    general_channel = discord.utils.get(member.guild.text_channels, name="paddys-pub")

    # Check if the member is a bot
    if member.bot:
        # Assign 'Bot' role to new bot member
        bot_role = discord.utils.get(member.guild.roles, name=BOT_ROLE_NAME)
        if bot_role and bot_role not in member.roles:  # Check if the role is already assigned
            await member.add_roles(bot_role)
            logging.info(f'Assigned {BOT_ROLE_NAME} role to {member.display_name}.')
            log_member_event(member.display_name, f'Assigned {BOT_ROLE_NAME} role', "Assigned bot role to new member.")
    else:
        # Assign 'Gang Members' role to new human member
        gang_role = discord.utils.get(member.guild.roles, name=GANG_ROLE_NAME)
        if gang_role and gang_role not in member.roles:  # Check if the role is already assigned
            await member.add_roles(gang_role)
            logging.info(f'Assigned {GANG_ROLE_NAME} role to {member.display_name}.')
            log_member_event(member.display_name, f'Assigned {GANG_ROLE_NAME} role', "Assigned gang role to new member.")
        
        # Send a welcome message
        welcome_message = random.choice(welcome_messages).format(user=member.display_name)
        if general_channel:
            await general_channel.send(welcome_message)
            log_member_event(member.display_name, 'Joined Server', welcome_message)

# Slash command: Test welcome message functionality
@bot.command(description="Send a test welcome message")
async def test_welcome(ctx):
    if ctx.guild:
        welcome_message = random.choice(welcome_messages).format(user=ctx.author.display_name)
        await ctx.send(welcome_message)  # Send message in the channel
        logging.info(f'Test welcome message sent to {ctx.author.display_name}.')

# Run the bot using the token from the .env file
bot.run(TOKEN)