import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load environment variables from .env file located in the 'environment' folder
load_dotenv(dotenv_path='enviormental/.env')  # Ensure this path is correct
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))

# Check if GUILD_ID is correctly loaded
if GUILD_ID is None:
    raise ValueError("GUILD_ID is not set in the .env file.")

# Initialize bot with necessary intents
intents = discord.Intents.default()
intents.members = True

# Bot initialization
bot = commands.Bot(command_prefix="!", intents=intents)

# Constants for role names
GANG_ROLE_NAME = "Gang Members"
BOT_ROLE_NAME = "Bot"

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# Event: New member joins the server
@bot.event
async def on_member_join(member):
    # Assign 'Gang Members' role to new member
    if member.bot:
        bot_role = discord.utils.get(member.guild.roles, name=BOT_ROLE_NAME)
        if bot_role:
            await member.add_roles(bot_role)
            general_channel = discord.utils.get(member.guild.text_channels, name="general")
            if general_channel:
                await general_channel.send(f"{member.display_name} has joined as a bot and has been assigned the {BOT_ROLE_NAME} role.")
    else:
        gang_role = discord.utils.get(member.guild.roles, name=GANG_ROLE_NAME)
        if gang_role:
            await member.add_roles(gang_role)
            general_channel = discord.utils.get(member.guild.text_channels, name="general")
            if general_channel:
                await general_channel.send(f"{member.display_name} has joined the server and has been assigned to the {GANG_ROLE_NAME} role.")

# Event: Member updates (for checking bot role assignment)
@bot.event
async def on_member_update(before, after):
    # Check if the updated member is a bot
    if after.bot:
        bot_role = discord.utils.get(after.guild.roles, name=BOT_ROLE_NAME)
        if bot_role and bot_role not in after.roles:
            await after.add_roles(bot_role)
            general_channel = discord.utils.get(after.guild.text_channels, name="general")
            if general_channel:
                await general_channel.send(f"{after.display_name} has been assigned the {BOT_ROLE_NAME} role.")
    
    # Optional: Check if a member has changed roles (promoted or demoted)
    if before.roles != after.roles:
        general_channel = discord.utils.get(after.guild.text_channels, name="general")
        for role in after.roles:
            if role not in before.roles:  # Role was added
                if general_channel:
                    await general_channel.send(f"{after.display_name} has been promoted to {role.name}.")
                break
        for role in before.roles:
            if role not in after.roles:  # Role was removed
                if general_channel:
                    await general_channel.send(f"{after.display_name} has been demoted to {role.name}.")
                break

# Slash command: Promote a member
@bot.slash_command(guild_ids=[GUILD_ID], description="Promote a member")
async def promote(ctx, member: discord.Member, role: discord.Role):
    admin_role = discord.utils.get(ctx.guild.roles, name="Admin")
    if admin_role in ctx.author.roles:
        await member.add_roles(role)
        general_channel = discord.utils.get(ctx.guild.text_channels, name="general")
        if general_channel:
            await general_channel.send(f"{member.display_name} has been promoted to {role.name}.")
        await ctx.respond(f"{member.display_name} has been promoted to {role.name}.")  # Acknowledge the command
    else:
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)

# Slash command: Demote a member
@bot.slash_command(guild_ids=[GUILD_ID], description="Demote a member")
async def demote(ctx, member: discord.Member, role: discord.Role):
    admin_role = discord.utils.get(ctx.guild.roles, name="Admin")
    if admin_role in ctx.author.roles:
        await member.remove_roles(role)
        general_channel = discord.utils.get(ctx.guild.text_channels, name="general")
        if general_channel:
            await general_channel.send(f"{member.display_name} has been demoted to {role.name}.")
        await ctx.respond(f"{member.display_name} has been demoted to {role.name}.")  # Acknowledge the command
    else:
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)

# Run the bot using the token from the .env file
bot.run(TOKEN)