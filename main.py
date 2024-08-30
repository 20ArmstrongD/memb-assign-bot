import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from sql_logger import log_request  # Import the SQL logging function

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
intents.message_content = True  # Enable message content intent

# Bot initialization
bot = commands.Bot(command_prefix="!", intents=intents)

# Constants for role names and emoji file paths
GANG_ROLE_NAME = "Gang Members"
STALLIONS_ROLE_NAME = "The Stallions"
EMOJI_APPROVE = "✅"  # Unicode for the approve emoji
EMOJI_DENY = "❌"  # Unicode for the deny emoji

# Connect to the SQLite database on startup
@bot.event
async def on_ready():
    logging.info(f'Bot is ready and connected as {bot.user}!')
    logging.info('Connected to the SQLite database: logs.db')  # Log database connection status

# Function to assign roles upon member joining
@bot.event
async def on_member_join(member):
    # Get the roles from the guild
    gang_role = discord.utils.get(member.guild.roles, name=GANG_ROLE_NAME)
    stallions_role = discord.utils.get(member.guild.roles, name=STALLIONS_ROLE_NAME)

    # Check if the member is a bot
    if member.bot and stallions_role:
        await member.add_roles(stallions_role)
        logging.info(f'Assigned {STALLIONS_ROLE_NAME} role to bot {member.display_name}.')
    elif gang_role:
        await member.add_roles(gang_role)
        logging.info(f'Assigned {GANG_ROLE_NAME} role to {member.display_name}.')

# Function to promote a member
async def promote_member(interaction, member, role):
    await member.add_roles(role)
    general_channel = discord.utils.get(interaction.guild.text_channels, name="paddys-pub")
    if general_channel:
        await general_channel.send(f"{member.display_name} has been promoted to {role.name}.")
    await interaction.followup.send(f"{member.display_name} has been promoted to {role.name}.", ephemeral=True)
    
    # Log the promotion request
    log_request(interaction.user.display_name, f"Promoted {member.display_name} to {role.name}", True, interaction.user.display_name)

# Slash command: Promote a member
@bot.tree.command(guild=discord.Object(id=GUILD_ID), name="promote", description="Request to promote a member")
async def promote(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await interaction.response.defer()
    admin_role = discord.utils.get(interaction.guild.roles, name="Admin")

    # Check if the user is an admin
    if admin_role in interaction.user.roles:
        await promote_member(interaction, member, role)
        logging.info(f'{interaction.user.display_name} aka: Admin promoted {member.display_name} to {role.name}.')
        log_request(interaction.user.display_name, f"Promoted {member.display_name} to {role.name}", True, interaction.user.display_name)
    else:
        # Notify admins for approval
        admins = [admin for admin in interaction.guild.members if admin_role in admin.roles]
        if admins:
            admin_mentions = ', '.join(admin.mention for admin in admins)

            # Send the approval request message to the paddys-pub channel
            general_channel = discord.utils.get(interaction.guild.text_channels, name="paddys-pub")
            if general_channel:
                try:
                    approval_message = await general_channel.send(
                        f"{admin_mentions}, {interaction.user.mention} is requesting to promote {member.display_name} to {role.name}. "
                        f"React with {EMOJI_APPROVE} to approve or {EMOJI_DENY} to deny."
                    )

                    def check(reaction, user):
                        return user in admins and reaction.message.id == approval_message.id and str(reaction.emoji) in [EMOJI_APPROVE, EMOJI_DENY]

                    # Wait for a reaction from admins
                    reaction, user = await bot.wait_for('reaction_add', check=check)

                    if str(reaction.emoji) == EMOJI_APPROVE:
                        await promote_member(interaction, member, role)
                        logging.info(f'{user.display_name} approved promotion of {member.display_name} to {role.name}.')
                        log_request(user.display_name, f"Approved promotion of {member.display_name} to {role.name}", True, user.display_name)
                    else:
                        await interaction.followup.send(f"Promotion of {member.display_name} to {role.name} has been denied.", ephemeral=True)
                        logging.info(f'{user.display_name} denied promotion of {member.display_name} to {role.name}.')
                        log_request(user.display_name, f"Denied promotion of {member.display_name} to {role.name}", False, user.display_name)
                except Exception as e:
                    logging.error(f"Error sending approval message: {e}")
                    await interaction.followup.send("There was an error processing the approval request.", ephemeral=True)
            else:
                await interaction.followup.send("Could not find the paddys-pub channel.", ephemeral=True)
        else:
            await interaction.followup.send("No Admins found to approve the request.", ephemeral=True)

# Function to demote a member
async def demote_member(interaction, member, role):
    await member.remove_roles(role)
    general_channel = discord.utils.get(interaction.guild.text_channels, name="paddys-pub")
    if general_channel:
        await general_channel.send(f"{member.display_name} has been demoted from {role.name}.")
    await interaction.followup.send(f"{member.display_name} has been demoted from {role.name}.", ephemeral=True)
    
    # Log the demotion request
    log_request(interaction.user.display_name, f"Demoted {member.display_name} from {role.name}", True, interaction.user.display_name)

# Slash command: Demote a member
@bot.tree.command(guild=discord.Object(id=GUILD_ID), name="demote", description="Request to demote a member")
async def demote(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await interaction.response.defer()
    admin_role = discord.utils.get(interaction.guild.roles, name="Admin")

    # Check if the user is an admin
    if admin_role in interaction.user.roles:
        await demote_member(interaction, member, role)
        logging.info(f'{interaction.user.display_name} aka: Admin just demoted {member.display_name} from {role.name}.')
        log_request(interaction.user.display_name, f" just demoted {member.display_name} from {role.name}", True, interaction.user.display_name)
    else:
        # Notify admins for approval
        admins = [admin for admin in interaction.guild.members if admin_role in admin.roles]
        if admins:
            admin_mentions = ', '.join(admin.mention for admin in admins)

            # Send the approval request message to the paddys-pub channel
            general_channel = discord.utils.get(interaction.guild.text_channels, name="paddys-pub")
            if general_channel:
                try:
                    approval_message = await general_channel.send(
                        f"{admin_mentions}, {interaction.user.mention} is requesting to demote {member.display_name} from {role.name}. "
                        f"React with {EMOJI_APPROVE} to approve or {EMOJI_DENY} to deny."
                    )

                    def check(reaction, user):
                        return user in admins and reaction.message.id == approval_message.id and str(reaction.emoji) in [EMOJI_APPROVE, EMOJI_DENY]

                    # Wait for a reaction from admins
                    reaction, user = await bot.wait_for('reaction_add', check=check)

                    if str(reaction.emoji) == EMOJI_APPROVE:
                        await demote_member(interaction, member, role)
                        logging.info(f'{user.display_name} approved demotion of {member.display_name} from {role.name}.')
                        log_request(user.display_name, f"Approved demotion of {member.display_name} from {role.name}", True, user.display_name)
                    else:
                        await interaction.followup.send(f"Demotion of {member.display_name} from {role.name} has been denied.", ephemeral=True)
                        logging.info(f'{user.display_name} denied demotion of {member.display_name} from {role.name}.')
                        log_request(user.display_name, f"Denied demotion of {member.display_name} from {role.name}", False, user.display_name)
                except Exception as e:
                    logging.error(f"Error sending approval message: {e}")
                    await interaction.followup.send("There was an error processing the approval request.", ephemeral=True)
            else:
                await interaction.followup.send("Could not find the paddys-pub channel.", ephemeral=True)
        else:
            await interaction.followup.send("No Admins found to approve the request.", ephemeral=True)

# Log registration of slash commands
@bot.event
async def on_connect():
    logging.info("Bot connected to Discord API.")
    registered_commands = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    logging.info(f"Slash commands registered: {', '.join([cmd.name for cmd in registered_commands])}")

# Run the bot using the token from the .env file
bot.run(TOKEN)