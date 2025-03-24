import discord
from discord.ext import commands
import logging
import json
import random
from commands.elements.config import ( 
    STALLIONS_ROLE_NAME,
    TOKEN,
    WELCOME_CHANNEL,
    GANG_ROLE_NAME,
    GUILD_ID,
    bot,
    welc_msg_memb_path,
    welc_msg_bot_path
)
from commands.elements.sql_logger import DATABASE_PATH



from commands import (
    register_promote_command, 
    register_demote_command,
    register_kick_command,
    
)

welcome_sent = set()

async def load_commands():
    register_promote_command(bot)
    register_demote_command(bot)
    register_kick_command(bot)
    

@bot.event
async def on_ready():
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
        
        with open(welc_msg_bot_path, "r") as file:
            data = json.load(file)
        
        selected_message = random.choice(data["WELCOME_MESSAGES_BOTS"])
        
        formated_msg_bot = selected_message.format(
            member = member.display_name,
            role = role_assigned,
            welcome_channel = WELCOME_CHANNEL
        )
        
        welcome_message = formated_msg_bot
       
    elif gang_role:
        await member.add_roles(gang_role)
        role_assigned = gang_role.name
        logging.info(f'Assigned {GANG_ROLE_NAME} role to {member.display_name}.')
        
        # Choose a welcome message for members
        with open(welc_msg_memb_path, "r") as file:
            data = json.load(file)
        
        selected_message = random.choice(data["WELCOME_MESSAGES_MEMBERS"])
        
        formated_msg_memb = selected_message.format(
            member = member.display_name,
            role = role_assigned,
            welcome_channel = WELCOME_CHANNEL
        )
        
        welcome_message = formated_msg_memb
       
    else:
        logging.warning(f'No specific role assigned to {member.display_name}.')

    # Send the welcome message to the paddys-pub channel
    general_channel = discord.utils.get(member.guild.text_channels, name="🙌-new-members")
    
    
    if general_channel:
        # Send the welcome message to the channel
        await general_channel.send(welcome_message)
    welcome_sent.add(member.id)


# Log registration of slash commands
@bot.event
async def on_connect():
    logging.info("Bot connected to Discord API.")
    await load_commands()
    try:
        registered_commands = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        logging.info(f"Slash commands registered: {', '.join([cmd.name for cmd in registered_commands])}")
    except Exception as e:
        logging.error(f"failed to sync commands: {e}")

bot.run(TOKEN)
