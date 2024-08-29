import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging
from json_logger import log_member_event  # Import the JSON logger

# Configure logging for the bot
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file located in the 'environment' folder
load_dotenv(dotenv_path='environment/.env')  # Ensure the path is correct
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

def log_event(event_type, member_name, description):
    """Log events to the console and JSON file."""
    log_member_event(member_name, event_type, description)
    logging.info(f'[{event_type}] {member_name}: {description}')

# Event: Bot is ready
@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')

# Event: Bot joins a new guild
@bot.event
async def on_guild_join(guild):
    # Check if the Bot role exists, if not create it
    bot_role = discord.utils.get(guild.roles, name=BOT_ROLE_NAME)
    if bot_role is None:
        bot_role = await guild.create_role(name=BOT_ROLE_NAME)  # Create the Bot role
        log_event('Role Creation', BOT_ROLE_NAME, f'Created {BOT_ROLE_NAME} role in {guild.name}.')
    
    # Assign the bot role to itself
    await guild.me.add_roles(bot_role)
    log_event('Role Assignment', BOT_ROLE_NAME, f'Assigned {BOT_ROLE_NAME} role to the bot in {guild.name}.')

# Event: New member joins the server
@bot.event
async def on_member_join(member):
    general_channel = discord.utils.get(member.guild.text_channels, name="general")
    
    if member.bot:
        # Assign 'Bot' role to new member (if it's a bot)
        bot_role = discord.utils.get(member.guild.roles, name=BOT_ROLE_NAME)
        if bot_role and bot_role not in member.roles:  # Check if the role is already assigned
            await member.add_roles(bot_role)
            if general_channel:
                await general_channel.send(f"{member.display_name} has joined as a bot and has been assigned the {BOT_ROLE_NAME} role.")
            log_event('Role Assignment', member.display_name, f'Assigned {BOT_ROLE_NAME} role upon joining as a bot.')
        else:
            logging.info(f'{member.display_name} is already assigned the {BOT_ROLE_NAME} role or the role does not exist.')
    else:
        # Assign 'Gang Members' role to new member (if it's a human)
        gang_role = discord.utils.get(member.guild.roles, name=GANG_ROLE_NAME)
        if gang_role and gang_role not in member.roles:  # Check if the role is already assigned
            await member.add_roles(gang_role)
            if general_channel:
                await general_channel.send(f"{member.display_name} has joined the server and has been assigned to the {GANG_ROLE_NAME} role.")
            log_event('Role Assignment', member.display_name, f'Assigned to the {GANG_ROLE_NAME} role upon joining.')
        else:
            logging.info(f'{member.display_name} is already assigned the {GANG_ROLE_NAME} role or the role does not exist.')

# Event: Member updates (for checking bot role assignment)
@bot.event
async def on_member_update(before, after):
    general_channel = discord.utils.get(after.guild.text_channels, name="general")

    if after.bot:
        bot_role = discord.utils.get(after.guild.roles, name=BOT_ROLE_NAME)
        if bot_role and bot_role not in after.roles:
            await after.add_roles(bot_role)
            if general_channel:
                await general_channel.send(f"{after.display_name} has been assigned the {BOT_ROLE_NAME} role.")
            log_event('Role Assignment', after.display_name, f'Assigned {BOT_ROLE_NAME} role after being updated.')
        else:
            logging.info(f'{after.display_name} is already assigned the {BOT_ROLE_NAME} role.')

    # Optional: Check if a member has changed roles (promoted or demoted)
    if before.roles != after.roles:
        for role in after.roles:
            if role not in before.roles:  # Role was added
                if general_channel:
                    await general_channel.send(f"{after.display_name} has been promoted to {role.name}.")
                log_event('Promotion', after.display_name, f'Promoted to {role.name}.')
                break
        for role in before.roles:
            if role not in after.roles:  # Role was removed
                if general_channel:
                    await general_channel.send(f"{after.display_name} has been demoted to {role.name}.")
                log_event('Demotion', after.display_name, f'Demoted to {role.name}.')
                break

# Slash command: Promote a member
@bot.command(guild_ids=[GUILD_ID], description="Promote a member")
async def promote(ctx, member: discord.Member, role: discord.Role):
    admin_role = discord.utils.get(ctx.guild.roles, name="Admin")
    if admin_role in ctx.author.roles:
        await member.add_roles(role)
        general_channel = discord.utils.get(ctx.guild.text_channels, name="general")
        if general_channel:
            await general_channel.send(f"{member.display_name} has been promoted to {role.name}.")
        await ctx.respond(f"{member.display_name} has been promoted to {role.name}.")  # Acknowledge the command
        log_event('Promotion', member.display_name, f'Promoted to {role.name} by {ctx.author.display_name}.')
    else:
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        logging.warning(f'{ctx.author.display_name} attempted to promote {member.display_name} without permission.')

# Slash command: Demote a member
@bot.command(guild_ids=[GUILD_ID], description="Demote a member")
async def demote(ctx, member: discord.Member, role: discord.Role):
    admin_role = discord.utils.get(ctx.guild.roles, name="Admin")
    if admin_role in ctx.author.roles:
        await member.remove_roles(role)
        general_channel = discord.utils.get(ctx.guild.text_channels, name="general")
        if general_channel:
            await general_channel.send(f"{member.display_name} has been demoted to {role.name}.")
        await ctx.respond(f"{member.display_name} has been demoted to {role.name}.")  # Acknowledge the command
        log_event('Demotion', member.display_name, f'Demoted to {role.name} by {ctx.author.display_name}.')
    else:
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)