import discord 
from discord.ext import commands
import logging
import asyncio
from .elements import (
    EMOJI_APPROVE,
    EMOJI_DENY,
    GUILD_ID,
    bot,
    log_request_kick
)

# Cooldown dictionary to prevent spam
kick_cooldowns = {}
COOLDOWN_TIME = 300  # 5 minutes



async def kick_member(interaction, member, admin_user):
    try:
        await member.kick(reason=f"Kick approved by {admin_user.display_name}")
        log_request_kick(member.display_name, "Kicked", interaction.user.display_name, admin_user.display_name)
        await interaction.followup.send(f"{member.display_name} has been kicked by {admin_user.mention}.", ephemeral=True)
        logging.info(f"{admin_user.display_name} approved and kicked {member.display_name}.")
    except discord.Forbidden:
        await interaction.followup.send("I don't have permission to kick this user.", ephemeral=True)
        logging.error(f"Failed to kick {member.display_name} due to insufficient permissions.")
    except discord.HTTPException as e:
        await interaction.followup.send("An error occurred while kicking the user.", ephemeral=True)
        logging.error(f"HTTP Exception while kicking {member.display_name}: {e}")

def register_kick_command(bot):
    @bot.tree.command(guild=discord.Object(id=GUILD_ID),name="kick_request", description="Request an admin to kick a member.")
    async def kick_request(interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()

        if interaction.user.id in kick_cooldowns and (discord.utils.utcnow() - kick_cooldowns[interaction.user.id]).total_seconds() < COOLDOWN_TIME:
            await interaction.followup.send("You must wait before making another kick request.", ephemeral=True)
            return

        kick_cooldowns[interaction.user.id] = discord.utils.utcnow()
        admin_role = discord.utils.get(interaction.guild.roles, name="Admin")
        if not admin_role:
            await interaction.followup.send("No Admin role found in this server.", ephemeral=True)
            return

        admin_channel = discord.utils.get(interaction.guild.text_channels, name="🏢-admin-approval")
        warning_channel = discord.utils.get(interaction.guild.text_channels, name="member-warnings")
        private_admin_channel =discord.utils.get(interaction.guild.text_channels, name= "private-admin-approval")
        if not admin_channel:
            await interaction.followup.send("Kick approval channel not found.", ephemeral=True)
            return

        try:
            await member.send(f"Hey {member.mention}, {interaction.user.mention} has sent a request to {admin_role.mention} to kick you from the server. Admins will review this request.")
        except (discord.Forbidden, discord.HTTPException) as e:
            logging.warning(f"Could not send DM to {member.display_name}: {e}")
            if warning_channel:
                await warning_channel.send(f"{member.mention}, you have been flagged for a kick request by {interaction.user.mention}. An admin will review this request.")
            
            
            # Notify admins
        admins = [admin for admin in interaction.guild.members if admin_role in admin.roles]
        if admins:
            admin_mentions = ', '.join(admin.mention for admin in admins)
            approval_message = await admin_channel.send(
                f"{admin_mentions}, {interaction.user.mention} is requesting to kick {member.mention}. "
                f"React with {EMOJI_APPROVE} to approve or {EMOJI_DENY} to deny."
            )
            await approval_message.add_reaction(EMOJI_APPROVE)
            await approval_message.add_reaction(EMOJI_DENY)


            def check(reaction, user):
                return user in admins and reaction.message.id == approval_message.id and str(reaction.emoji) in [EMOJI_APPROVE, EMOJI_DENY]

            try:
                reaction, admin_user = await bot.wait_for("reaction_add", check=check)

                if str(reaction.emoji) == EMOJI_APPROVE:
                    # Send second confirmation request
                    confirmation_message = await admin_channel.send(
                        f"{admin_user.mention}, are you sure you want to kick {member.mention}? "
                        f"React with {EMOJI_APPROVE} again to confirm."
                    )
                    await confirmation_message.add_reaction(EMOJI_APPROVE)

                    def check_second(reaction, user):
                        return user == admin_user and reaction.message.id == confirmation_message.id and str(reaction.emoji) == EMOJI_APPROVE
                    
                    try:
                        await interaction.client.wait_for("reaction_add", check=check_second, timeout=60.0)
                        await kick_member(interaction, member, admin_user)
                    except asyncio.TimeoutError:
                        await private_admin_channel.send(f"{admin_user.mention}, the second confirmation timed out. Kick request for {member.mention} has been cancelled.")
                else:
                    await interaction.followup.send(f"Kick request for {member.mention} has been denied.", ephemeral=True)
                    logging.info(f"{admin_user.display_name} denied kick request for {member.display_name}.")
            except asyncio.TimeoutError:
                await admin_channel.send("Kick request timed out.")
        else:
            await interaction.followup.send("No Admins found to approve the request.", ephemeral=True)
