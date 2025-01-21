import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from sql_logger import log_request, DATABASE_PATH  #
import random 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file located in the 'environmental' folder
load_dotenv(dotenv_path='environmental/.env')  
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

# Connect to the SQLite database on startup
@bot.event
async def on_ready():
    welcome_sent.clear()
    logging.info(f'Bot is ready and connected as {bot.user}!')
    logging.info(f'Connected to the SQLite database: {DATABASE_PATH}')  # Log database connection status

    for guild in bot.guilds:
        logging.info(f'Checking role assignment in guild: {guild.name} (ID: {guild.id})')

        # Get the bot's member object
        bot_member = guild.me

        # Find the "The Stallions" role
        stallions_role = discord.utils.get(guild.roles, name=STALLIONS_ROLE_NAME)

        if stallions_role:
            logging.info(f"Found {STALLIONS_ROLE_NAME} role in {guild.name}.")

            # Check if the bot already has the role
            if stallions_role in bot_member.roles:
                logging.info(f'Bot is already assigned to the {STALLIONS_ROLE_NAME} role in {guild.name}.')
            else:
                # Try to assign the role to the bot
                try:
                    await bot_member.add_roles(stallions_role)
                    logging.info(f'Successfully assigned {STALLIONS_ROLE_NAME} role to {bot.user.display_name} in {guild.name}.')
                except discord.Forbidden:
                    logging.error(f"Failed to assign {STALLIONS_ROLE_NAME} role due to insufficient permissions in {guild.name}.")
                except discord.HTTPException as e:
                    logging.error(f"HTTP Exception: {e}")

        else:
            logging.warning(f'{STALLIONS_ROLE_NAME} role not found in {guild.name}.')

@bot.event
async def on_guild_join(guild):
    logging.info(f'Joined new guild: {guild.name}')

    # Check if the bot has any roles in the guild
    if not guild.me.roles or len(guild.me.roles) == 1:  # The bot might only have the @everyone role
        logging.info(f'Bot has no roles in {guild.name}. Requesting to join The Stallions role.')

        # Get the Admin role and admins in the guild
        admin_role = discord.utils.get(guild.roles, name="Admin")
        admins = [member for member in guild.members if admin_role in member.roles]

        if admins:
            admin_mentions = ', '.join(admin.mention for admin in admins)
            general_channel = discord.utils.get(guild.text_channels, name="🙌-new-members") or guild.system_channel
            
            if general_channel:
                try:
                    approval_message = await general_channel.send(
                        f"{admin_mentions}, the bot {guild.me.mention} is requesting to join the {STALLIONS_ROLE_NAME} role. "
                        f"React with {EMOJI_APPROVE} to approve or {EMOJI_DENY} to deny."
                    )

                    def check(reaction, user):
                        return user in admins and reaction.message.id == approval_message.id and str(reaction.emoji) in [EMOJI_APPROVE, EMOJI_DENY]

                    # Wait for a reaction from an admin
                    reaction, user = await bot.wait_for('reaction_add', check=check)

                    if str(reaction.emoji) == EMOJI_APPROVE:
                        stallions_role = discord.utils.get(guild.roles, name=STALLIONS_ROLE_NAME)
                        if stallions_role:
                            await guild.me.add_roles(stallions_role)
                            logging.info(f'Successfully assigned The Stallions role to the bot in {guild.name}.')
                        else:
                            logging.error(f'The Stallions role does not exist in {guild.name}.')
                    else:
                        logging.info(f'{user.display_name} denied the bot\'s request to join The Stallions role in {guild.name}.')
                except Exception as e:
                    logging.error(f"Error sending approval message: {e}")
            else:
                logging.error(f"Can't find channel to send the approval request in {guild.name}.")
        else:
            logging.error(f"No Admins found in {guild.name} to approve the request.")
    else:
        logging.info(f'Bot is already assigned to a role in {guild.name}.')

# Define separate arrays of welcome messages for members and bots
WELCOME_MESSAGES_MEMBERS = [
    "Welcome to the server, {member}! You have been assigned the role of {role}!\nPlease take a look at the {WELCOME_CHANNEL} to learn more about the server!",
    "Hey {member}, welcome aboard! Enjoy your stay as a {role}!\nPlease take a look at the {WELCOME_CHANNEL} to learn more about the server!",
    "Greetings {member}! Hope you have a great time as a {role} in our community!\nPlease take a look at the {WELCOME_CHANNEL} to learn more about the server!",
    "Welcome, {member}! You are now part of the {role} team!\nPlease take a look at the {WELCOME_CHANNEL} to learn more about the server!",
    "Hello {member}! We're excited to have you join us as a {role}! \nPlease take a look at the {WELCOME_CHANNEL} to learn more about the server!"
]

WELCOME_MESSAGES_BOTS = [
    "Welcome, bot {member}! You have been assigned the role of {role}!\nPlease take a look at the {WELCOME_CHANNEL} to learn more about the server!",
    "Hello, bot {member}! Enjoy your time in the server as a {role}!\nPlease take a look at the {WELCOME_CHANNEL} to learn more about the server!",
    "Hey there, bot {member}! Glad to have you join us as a {role}!\nPlease take a look at the {WELCOME_CHANNEL} to learn more about the server!",
    "Welcome, {member}! You are now part of the bot squad with the role of {role}!\nPlease take a look at the {WELCOME_CHANNEL} to learn more about the server!!",
    "Greetings, bot {member}! Hope you find your role as a {role} enjoyable!\nPlease take a look at the {WELCOME_CHANNEL} to learn more about the server!"
]

welcome_sent = set()  # Dictionary to store welcome counts for each member ID, regardless of bot or human

@bot.event
async def on_member_join(member):
    if member.id in welcome_sent:
        return 

    # Get the roles from the guild
    gang_role = discord.utils.get(member.guild.roles, name=GANG_ROLE_NAME)
    stallions_role = discord.utils.get(member.guild.roles, name=STALLIONS_ROLE_NAME)

    # Initialize role_assigned
    role_assigned = "No specific role assigned."

    if member.bot and stallions_role:
        await member.add_roles(stallions_role)
        role_assigned = stallions_role.name
        logging.info(f'Assigned {STALLIONS_ROLE_NAME} role to bot {member.display_name}.')
        
        # Choose a welcome message for bots
        welcome_message = random.choice(WELCOME_MESSAGES_BOTS).format(member=member.display_name, role=role_assigned, WELCOME_CHANNEL=WELCOME_CHANNEL)
    elif gang_role:
        await member.add_roles(gang_role)
        role_assigned = gang_role.name
        logging.info(f'Assigned {GANG_ROLE_NAME} role to {member.display_name}.')
        
        # Choose a welcome message for members
        welcome_message = random.choice(WELCOME_MESSAGES_MEMBERS).format(member=member.display_name, role=role_assigned, WELCOME_CHANNEL=WELCOME_CHANNEL)
    else:
        logging.warning(f'No specific role assigned to {member.display_name}.')

    # Send the welcome message to the paddys-pub channel
    general_channel = discord.utils.get(member.guild.text_channels, name="🙌-new-members")
    
    
    if general_channel:
        # Send the welcome message to the channel
        await general_channel.send(welcome_message)
    welcome_sent.add(member.id)

# Function to promote a member
async def promote_member(interaction, member, role):
    await member.add_roles(role)
    await interaction.followup.send(f"{member.display_name} has been promoted to {role.name}.", ephemeral=True)
    
    # Log the promotion request
    log_request(interaction.user.display_name, f"Promoted {member.display_name} to {role.name}", True, interaction.user.display_name)

# Slash command: Promote a member
@bot.tree.command(guild=discord.Object(id=GUILD_ID), name="promote", description="Request to promote a <member> from a <role>")
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
            general_channel = discord.utils.get(interaction.guild.text_channels, name="🙌-new-members")
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
    try:
        await member.remove_roles(role)
        await interaction.followup.send(f"{member.display_name} has been demoted from {role.name}.", ephemeral=True)
            # Log the demotion request
        log_request(interaction.user.display_name, f"Demoted {member.display_name} from {role.name}", True, interaction.user.display_name)
        
        # Log the demotion request
        log_request(interaction.user.display_name, f"Demoted {member.display_name} from {role.name}", True, interaction.user.display_name)

    except discord.Forbidden:
        await interaction.followup.send(f"Insufficient permissions to demote {member.display_name}.", ephemeral=True)
        # Optionally log the error
        logging.error(f"Failed to demote {member.display_name} from {role.name} due to insufficient permissions.")

    except discord.HTTPException as e:
        await interaction.followup.send(f"An error occurred while demoting {member.display_name}.", ephemeral=True)
        # Optionally log the error
        logging.error(f"HTTP Exception while demoting {member.display_name} from {role.name}: {e}")

# Slash command: Demote a member
@bot.tree.command(guild=discord.Object(id=GUILD_ID), name="demote", description="Request to demote a <member> from <role>")
async def demote(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await interaction.response.defer()
    admin_role = discord.utils.get(interaction.guild.roles, name="Admin")

    # Check if the user is an admin
    if admin_role in interaction.user.roles:
        await demote_member(interaction, member, role)
        logging.info(f'{interaction.user.display_name} aka: Admin just demoted {member.display_name} from {role.name}.')
        log_request(interaction.user.display_name, f"just demoted {member.display_name} from {role.name}", True, interaction.user.display_name)
    else:
        # Notify admins for approval
        admins = [admin for admin in interaction.guild.members if admin_role in admin.roles]
        if admins:
            admin_mentions = ', '.join(admin.mention for admin in admins)

            # Send the approval request message to the paddys-pub channel
            general_channel = discord.utils.get(interaction.guild.text_channels, name="🙋-requests")
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