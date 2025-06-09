import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import os
# v2
# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables to store data
mute_role_id = None
welcome_data = {}  # Format: {guild_id: {'channel_id': int, 'message': str, 'enabled': bool}}
giveaway_data = {}  # Format: {message_id: {'host': user_id, 'prize': str, 'end_time': datetime, 'channel_id': int, 'guild_id': int, 'winners': int, 'participants': set()}}
leveling_data = {}  # Format: {guild_id: {user_id: {'xp': int, 'level': int, 'total_xp': int}}}
leveling_config = {}  # Format: {guild_id: {'enabled': bool, 'channel_id': int, 'xp_per_message': int, 'xp_cooldown': int}}
ticket_config = {}  # Format: {guild_id: {'category_id': int, 'staff_roles': [role_ids], 'enabled': bool}}
active_tickets = {}  # Format: {channel_id: {'user_id': int, 'guild_id': int, 'ticket_number': int}}
sticky_data = {}  # Format: {channel_id: {'message': str, 'active': bool, 'last_message_id': int, 'author_id': int, 'guild_id': int}}
sticky_messages = {}  # Alternative format for improved sticky functionality

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_guild_join(guild):
    """Send a welcome message when the bot joins a new server"""
    # Try to find a suitable channel to send the message
    # Priority: general, welcome, or first available text channel
    target_channel = None
    
    # Look for common welcome channel names
    for channel in guild.text_channels:
        if channel.name.lower() in ['general', 'welcome', 'chat', 'main']:
            if channel.permissions_for(guild.me).send_messages:
                target_channel = channel
                break
    
    # If no common channel found, use the first available text channel
    if not target_channel:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                target_channel = channel
                break
    
    # Send welcome message if we found a suitable channel
    if target_channel:
        try:
            embed = discord.Embed(
                title="🎉 Thanks for adding me!",
                description="Hello! I'm your new Discord bot with lots of features to help manage your server!",
                color=0x00ff00
            )
            embed.add_field(
                name="🚀 Getting Started",
                value="Use `/help` to see all available commands!",
                inline=False
            )
            embed.add_field(
                name="✨ Key Features",
                value="• Moderation tools\n• Welcome system\n• Leveling system\n• Ticket system\n• Giveaways\n• Sticky messages\n• And much more!",
                inline=False
            )
            embed.set_footer(text=f"Added to {guild.name}")
            embed.timestamp = datetime.now()
            
            await target_channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to send welcome message in {guild.name}: {e}")
    else:
        print(f"No suitable channel found to send welcome message in {guild.name}")

@bot.tree.command(name="ban", description="Ban a user from the server")
@app_commands.describe(user="The user to ban", reason="Reason for the ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ You don't have permission to ban members!", ephemeral=True)
        return

    try:
        await user.ban(reason=reason)
        await interaction.response.send_message(f"✅ **{user}** has been banned.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to ban this user!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="kick", description="Kick a user from the server")
@app_commands.describe(user="The user to kick", reason="Reason for the kick")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ You don't have permission to kick members!", ephemeral=True)
        return

    try:
        await user.kick(reason=reason)
        await interaction.response.send_message(f"✅ **{user}** has been kicked.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to kick this user!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="unban", description="Unban a user from the server")
@app_commands.describe(user_id="The ID of the user to unban", reason="Reason for the unban")
async def unban(interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ You don't have permission to unban members!", ephemeral=True)
        return

    try:
        user_id = int(user_id)
        user = await bot.fetch_user(user_id)
        await interaction.guild.unban(user, reason=reason)
        await interaction.response.send_message(f"✅ **{user}** has been unbanned.\n**Reason:** {reason}")
    except discord.NotFound:
        await interaction.response.send_message("❌ User not found or not banned!", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("❌ Invalid user ID!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="softban", description="Softban a user (ban then immediately unban to delete messages)")
@app_commands.describe(user="The user to softban", reason="Reason for the softban")
async def softban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ You don't have permission to ban members!", ephemeral=True)
        return

    try:
        await user.ban(reason=f"Softban: {reason}", delete_message_days=7)
        await interaction.guild.unban(user, reason=f"Softban completion: {reason}")
        await interaction.response.send_message(f"✅ **{user}** has been softbanned (messages deleted).\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to ban this user!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="mute", description="Mute a user")
@app_commands.describe(user="The user to mute", duration="Duration in minutes", reason="Reason for the mute")
async def mute(interaction: discord.Interaction, user: discord.Member, duration: int = None, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ You don't have permission to mute members!", ephemeral=True)
        return

    global mute_role_id
    mute_role = None

    if mute_role_id:
        mute_role = interaction.guild.get_role(mute_role_id)

    if not mute_role:
        await interaction.response.send_message("❌ Mute role not set! Use `/setmuterole` first.", ephemeral=True)
        return

    try:
        await user.add_roles(mute_role, reason=reason)

        if duration:
            await interaction.response.send_message(f"✅ **{user}** has been muted for {duration} minutes.\n**Reason:** {reason}")
            await asyncio.sleep(duration * 60)
            await user.remove_roles(mute_role, reason="Mute duration expired")
        else:
            await interaction.response.send_message(f"✅ **{user}** has been muted indefinitely.\n**Reason:** {reason}")

    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to mute this user!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="unmute", description="Unmute a user")
@app_commands.describe(user="The user to unmute", reason="Reason for the unmute")
async def unmute(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ You don't have permission to unmute members!", ephemeral=True)
        return

    global mute_role_id
    mute_role = None

    if mute_role_id:
        mute_role = interaction.guild.get_role(mute_role_id)

    if not mute_role:
        await interaction.response.send_message("❌ Mute role not set! Use `/setmuterole` first.", ephemeral=True)
        return

    try:
        await user.remove_roles(mute_role, reason=reason)
        await interaction.response.send_message(f"✅ **{user}** has been unmuted.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to unmute this user!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="lock", description="Lock a channel")
@app_commands.describe(channel="The channel to lock", reason="Reason for locking")
async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ You don't have permission to manage channels!", ephemeral=True)
        return

    channel = channel or interaction.channel

    try:
        await channel.set_permissions(interaction.guild.default_role, send_messages=False, reason=reason)
        await interaction.response.send_message(f"🔒 **{channel.mention}** has been locked.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to lock this channel!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="unlock", description="Unlock a channel")
@app_commands.describe(channel="The channel to unlock", reason="Reason for unlocking")
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ You don't have permission to manage channels!", ephemeral=True)
        return

    channel = channel or interaction.channel

    try:
        await channel.set_permissions(interaction.guild.default_role, send_messages=None, reason=reason)
        await interaction.response.send_message(f"🔓 **{channel.mention}** has been unlocked.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to unlock this channel!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="lockall", description="Lock all channels in the server")
@app_commands.describe(reason="Reason for locking all channels")
async def lockall(interaction: discord.Interaction, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permission to lock all channels!", ephemeral=True)
        return

    await interaction.response.defer()

    locked_channels = []
    failed_channels = []

    for channel in interaction.guild.text_channels:
        try:
            await channel.set_permissions(interaction.guild.default_role, send_messages=False, reason=reason)
            locked_channels.append(channel.name)
        except:
            failed_channels.append(channel.name)

    response = f"🔒 **Locked {len(locked_channels)} channels**\n**Reason:** {reason}"
    if failed_channels:
        response += f"\n❌ **Failed to lock:** {', '.join(failed_channels[:5])}"
        if len(failed_channels) > 5:
            response += f" and {len(failed_channels) - 5} more..."

    await interaction.followup.send(response)

@bot.tree.command(name="unlockall", description="Unlock all channels in the server")
@app_commands.describe(reason="Reason for unlocking all channels")
async def unlockall(interaction: discord.Interaction, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permission to unlock all channels!", ephemeral=True)
        return

    await interaction.response.defer()

    unlocked_channels = []
    failed_channels = []

    for channel in interaction.guild.text_channels:
        try:
            await channel.set_permissions(interaction.guild.default_role, send_messages=None, reason=reason)
            unlocked_channels.append(channel.name)
        except:
            failed_channels.append(channel.name)

    response = f"🔓 **Unlocked {len(unlocked_channels)} channels**\n**Reason:** {reason}"
    if failed_channels:
        response += f"\n❌ **Failed to unlock:** {', '.join(failed_channels[:5])}"
        if len(failed_channels) > 5:
            response += f" and {len(failed_channels) - 5} more..."

    await interaction.followup.send(response)

@bot.tree.command(name="clear", description="Clear messages from a channel")
@app_commands.describe(amount="Number of messages to delete (1-100)", channel="Channel to clear messages from")
async def clear(interaction: discord.Interaction, amount: int, channel: discord.TextChannel = None):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to manage messages!", ephemeral=True)
        return

    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Amount must be between 1 and 100!", ephemeral=True)
        return

    channel = channel or interaction.channel

    try:
        deleted = await channel.purge(limit=amount)
        await interaction.response.send_message(f"✅ Deleted {len(deleted)} messages from {channel.mention}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to delete messages in this channel!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="setmuterole", description="Set the mute role for the server")
@app_commands.describe(role="The role to use for muting users")
async def setmuterole(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permission to set the mute role!", ephemeral=True)
        return

    global mute_role_id
    mute_role_id = role.id

    await interaction.response.send_message(f"✅ Mute role set to **{role.name}**!")

# Welcome System Commands
@bot.tree.command(name="welcome", description="Main welcome system command")
async def welcome_main(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return

    guild_id = interaction.guild.id
    welcome_config = welcome_data.get(guild_id, {})

    embed = discord.Embed(title="🎉 Welcome System", color=0x00ff00)

    if welcome_config:
        channel = interaction.guild.get_channel(welcome_config.get('channel_id'))
        channel_name = channel.mention if channel else "❌ Channel not found"
        status = "✅ Enabled" if welcome_config.get('enabled', False) else "❌ Disabled"

        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Channel", value=channel_name, inline=True)
        embed.add_field(name="Message Preview", value=welcome_config.get('message', 'No message set')[:100] + "..." if len(welcome_config.get('message', '')) > 100 else welcome_config.get('message', 'No message set'), inline=False)
    else:
        embed.add_field(name="Status", value="❌ Not configured", inline=False)
        embed.description = "Use `/welcome create` to set up the welcome system."

    embed.set_footer(text="Use /welcome <subcommand> to manage settings")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-info", description="Show detailed welcome system information")
async def welcome_info(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to view welcome settings!", ephemeral=True)
        return

    guild_id = interaction.guild.id
    welcome_config = welcome_data.get(guild_id, {})

    embed = discord.Embed(title="🎉 Welcome System Information", color=0x0099ff)

    if welcome_config:
        channel = interaction.guild.get_channel(welcome_config.get('channel_id'))
        channel_name = channel.mention if channel else "❌ Channel not found"
        status = "✅ Enabled" if welcome_config.get('enabled', False) else "❌ Disabled"

        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Welcome Channel", value=channel_name, inline=True)
        embed.add_field(name="Full Message", value=welcome_config.get('message', 'No message set'), inline=False)

        embed.add_field(name="Available Variables", value="`{user}` - User mention\n`{username}` - Username\n`{server}` - Server name\n`{membercount}` - Member count", inline=False)
    else:
        embed.description = "❌ Welcome system is not configured for this server.\nUse `/welcome-create` to set it up."

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-preview", description="Preview how the welcome message will look")
async def welcome_preview(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to preview welcome messages!", ephemeral=True)
        return

    guild_id = interaction.guild.id
    welcome_config = welcome_data.get(guild_id, {})

    if not welcome_config or not welcome_config.get('message'):
        await interaction.response.send_message("❌ No welcome message configured! Use `/welcome-create` first.", ephemeral=True)
        return

    # Format the message with sample data
    message = welcome_config['message']
    formatted_message = message.replace('{user}', interaction.user.mention)
    formatted_message = formatted_message.replace('{username}', interaction.user.display_name)
    formatted_message = formatted_message.replace('{server}', interaction.guild.name)
    formatted_message = formatted_message.replace('{membercount}', str(interaction.guild.member_count))

    embed = discord.Embed(title="🎉 Welcome Message Preview", description=formatted_message, color=0x00ff00)
    embed.set_footer(text="This is how the welcome message will appear for new members")

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="welcome-create", description="Create/setup the welcome system")
@app_commands.describe(channel="The channel where welcome messages will be sent", message="The welcome message (use {user}, {username}, {server}, {membercount})")
async def welcome_create(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return

    guild_id = interaction.guild.id

    # Check if bot can send messages in the channel
    if not channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}!", ephemeral=True)
        return

    welcome_data[guild_id] = {
        'channel_id': channel.id,
        'message': message,
        'enabled': True
    }

    embed = discord.Embed(title="✅ Welcome System Created", color=0x00ff00)
    embed.add_field(name="Channel", value=channel.mention, inline=True)
    embed.add_field(name="Status", value="✅ Enabled", inline=True)
    embed.add_field(name="Message", value=message, inline=False)
    embed.set_footer(text="Welcome system is now active!")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-change", description="Change welcome message or channel")
@app_commands.describe(channel="New welcome channel (optional)", message="New welcome message (optional)")
async def welcome_change(interaction: discord.Interaction, channel: discord.TextChannel = None, message: str = None):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return

    guild_id = interaction.guild.id

    if guild_id not in welcome_data:
        await interaction.response.send_message("❌ Welcome system not configured! Use `/welcome-create` first.", ephemeral=True)
        return

    if not channel and not message:
        await interaction.response.send_message("❌ You must specify either a new channel or a new message!", ephemeral=True)
        return

    changes = []

    if channel:
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}!", ephemeral=True)
            return
        welcome_data[guild_id]['channel_id'] = channel.id
        changes.append(f"Channel updated to {channel.mention}")

    if message:
        welcome_data[guild_id]['message'] = message
        changes.append("Welcome message updated")

    embed = discord.Embed(title="✅ Welcome System Updated", color=0x00ff00)
    embed.description = "\n".join(changes)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-delete", description="Delete/disable the welcome system")
async def welcome_delete(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return

    guild_id = interaction.guild.id

    if guild_id not in welcome_data:
        await interaction.response.send_message("❌ Welcome system is not configured!", ephemeral=True)
        return

    del welcome_data[guild_id]

    embed = discord.Embed(title="✅ Welcome System Deleted", description="Welcome system has been completely removed from this server.", color=0xff0000)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-text", description="Update only the welcome message text")
@app_commands.describe(message="The new welcome message")
async def welcome_text(interaction: discord.Interaction, message: str):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return

    guild_id = interaction.guild.id

    if guild_id not in welcome_data:
        await interaction.response.send_message("❌ Welcome system not configured! Use `/welcome-create` first.", ephemeral=True)
        return

    welcome_data[guild_id]['message'] = message

    embed = discord.Embed(title="✅ Welcome Message Updated", color=0x00ff00)
    embed.add_field(name="New Message", value=message, inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-toggle", description="Enable or disable the welcome system")
async def welcome_toggle(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return

    guild_id = interaction.guild.id

    if guild_id not in welcome_data:
        await interaction.response.send_message("❌ Welcome system not configured! Use `/welcome-create` first.", ephemeral=True)
        return

    current_status = welcome_data[guild_id].get('enabled', True)
    welcome_data[guild_id]['enabled'] = not current_status

    new_status = "✅ Enabled" if not current_status else "❌ Disabled"
    color = 0x00ff00 if not current_status else 0xff0000

    embed = discord.Embed(title=f"Welcome System {new_status.split()[1]}", color=color)
    embed.add_field(name="Status", value=new_status, inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="list-bot", description="List all bots in the server")
async def list_bot(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to view bot list!", ephemeral=True)
        return

    # Get all bot members
    bots = [member for member in interaction.guild.members if member.bot]

    if not bots:
        await interaction.response.send_message("❌ No bots found in this server!", ephemeral=True)
        return

    # Sort bots by name
    bots.sort(key=lambda b: b.display_name.lower())

    # Pagination setup
    bots_per_page = 10
    total_pages = (len(bots) + bots_per_page - 1) // bots_per_page
    current_page = 0

    def create_embed(page):
        start_idx = page * bots_per_page
        end_idx = min(start_idx + bots_per_page, len(bots))
        page_bots = bots[start_idx:end_idx]

        embed = discord.Embed(
            title=f"🤖 Server Bots ({len(bots)} total)",
            color=0x0099ff,
            timestamp=datetime.now()
        )

        bot_list = []
        for i, bot in enumerate(page_bots, start=start_idx + 1):
            discriminator = f"#{bot.discriminator}" if bot.discriminator and bot.discriminator != "0" else ""
            bot_list.append(f"`#{i}.` [{bot.display_name}{discriminator}](https://discord.com/users/{bot.id}) [<@{bot.id}>]")

        embed.description = "\n".join(bot_list)
        embed.set_footer(text=f"Page {page + 1}/{total_pages} • {interaction.guild.name}")

        return embed

    def create_view(page):
        view = discord.ui.View(timeout=300)

        # Previous button
        prev_button = discord.ui.Button(
            label="◀️ Previous",
            style=discord.ButtonStyle.secondary,
            disabled=(page == 0)
        )

        async def prev_callback(button_interaction):
            nonlocal current_page
            current_page = max(0, current_page - 1)
            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)

        prev_button.callback = prev_callback
        view.add_item(prev_button)

        # Page indicator
        page_button = discord.ui.Button(
            label=f"{page + 1}/{total_pages}",
            style=discord.ButtonStyle.primary,
            disabled=True
        )
        view.add_item(page_button)

        # Next button
        next_button = discord.ui.Button(
            label="Next ▶️",
            style=discord.ButtonStyle.secondary,
            disabled=(page >= total_pages - 1)
        )

        async def next_callback(button_interaction):
            nonlocal current_page
            current_page = min(total_pages - 1, current_page + 1)
            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)

        next_button.callback = next_callback
        view.add_item(next_button)

        # Refresh button
        refresh_button = discord.ui.Button(
            label="🔄 Refresh",
            style=discord.ButtonStyle.success
        )

        async def refresh_callback(button_interaction):
            # Refresh the bots list
            updated_bots = [member for member in button_interaction.guild.members if member.bot]
            updated_bots.sort(key=lambda b: b.display_name.lower())
            nonlocal bots, total_pages, current_page
            bots = updated_bots
            total_pages = (len(bots) + bots_per_page - 1) // bots_per_page
            current_page = min(current_page, total_pages - 1) if total_pages > 0 else 0

            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)

        refresh_button.callback = refresh_callback
        view.add_item(refresh_button)

        return view

    embed = create_embed(current_page)
    view = create_view(current_page)

    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="role-all", description="Give a role to all members in the server")
@app_commands.describe(role="The role to give to all members")
async def role_all(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ You don't have permission to manage roles!", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ I don't have permission to manage roles!", ephemeral=True)
        return

    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ I cannot assign roles that are higher than or equal to my highest role!", ephemeral=True)
        return

    if role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You cannot assign roles that are higher than or equal to your highest role!", ephemeral=True)
        return

    await interaction.response.defer()

    members = [member for member in interaction.guild.members]
    success_count = 0
    failed_count = 0
    already_have = 0

    for member in members:
        try:
            if role not in member.roles:
                await member.add_roles(role, reason=f"Role added to all members by {interaction.user}")
                success_count += 1
            else:
                already_have += 1
        except Exception as e:
            failed_count += 1

    embed = discord.Embed(title="🎯 Role Assignment Complete", color=0x00ff00)
    embed.add_field(name="Role", value=role.mention, inline=True)
    embed.add_field(name="Target", value="All Members", inline=True)
    embed.add_field(name="✅ Successfully Added", value=str(success_count), inline=True)
    embed.add_field(name="📋 Already Had Role", value=str(already_have), inline=True)
    embed.add_field(name="❌ Failed", value=str(failed_count), inline=True)
    embed.add_field(name="📊 Total Members", value=str(len(members)), inline=True)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="role-human", description="Give a role to all human members in the server")
@app_commands.describe(role="The role to give to all human members")
async def role_human(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ You don't have permission to manage roles!", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ I don't have permission to manage roles!", ephemeral=True)
        return

    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ I cannot assign roles that are higher than or equal to my highest role!", ephemeral=True)
        return

    if role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You cannot assign roles that are higher than or equal to your highest role!", ephemeral=True)
        return

    await interaction.response.defer()

    humans = [member for member in interaction.guild.members if not member.bot]
    success_count = 0
    failed_count = 0
    already_have = 0

    for member in humans:
        try:
            if role not in member.roles:
                await member.add_roles(role, reason=f"Role added to all humans by {interaction.user}")
                success_count += 1
            else:
                already_have += 1
        except Exception as e:
            failed_count += 1

    embed = discord.Embed(title="👥 Role Assignment Complete", color=0x00ff00)
    embed.add_field(name="Role", value=role.mention, inline=True)
    embed.add_field(name="Target", value="Human Members", inline=True)
    embed.add_field(name="✅ Successfully Added", value=str(success_count), inline=True)
    embed.add_field(name="📋 Already Had Role", value=str(already_have), inline=True)
    embed.add_field(name="❌ Failed", value=str(failed_count), inline=True)
    embed.add_field(name="👥 Total Humans", value=str(len(humans)), inline=True)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="role-bots", description="Give a role to all bot members in the server")
@app_commands.describe(role="The role to give to all bot members")
async def role_bots(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ You don't have permission to manage roles!", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ I don't have permission to manage roles!", ephemeral=True)
        return

    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ I cannot assign roles that are higher than or equal to my highest role!", ephemeral=True)
        return

    if role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You cannot assign roles that are higher than or equal to your highest role!", ephemeral=True)
        return

    await interaction.response.defer()

    bots = [member for member in interaction.guild.members if member.bot]
    success_count = 0
    failed_count = 0
    already_have = 0

    for member in bots:
        try:
            if role not in member.roles:
                await member.add_roles(role, reason=f"Role added to all bots by {interaction.user}")
                success_count += 1
            else:
                already_have += 1
        except Exception as e:
            failed_count += 1

    embed = discord.Embed(title="🤖 Role Assignment Complete", color=0x00ff00)
    embed.add_field(name="Role", value=role.mention, inline=True)
    embed.add_field(name="Target", value="Bot Members", inline=True)
    embed.add_field(name="✅ Successfully Added", value=str(success_count), inline=True)
    embed.add_field(name="📋 Already Had Role", value=str(already_have), inline=True)
    embed.add_field(name="❌ Failed", value=str(failed_count), inline=True)
    embed.add_field(name="🤖 Total Bots", value=str(len(bots)), inline=True)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="role-removeall", description="Remove a specific role from all members in the server")
@app_commands.describe(role="The role to remove from all members")
async def role_removeall(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ You don't have permission to manage roles!", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ I don't have permission to manage roles!", ephemeral=True)
        return

    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ I cannot remove roles that are higher than or equal to my highest role!", ephemeral=True)
        return

    if role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You cannot remove roles that are higher than or equal to your highest role!", ephemeral=True)
        return

    if role == interaction.guild.default_role:
        await interaction.response.send_message("❌ Cannot remove the @everyone role!", ephemeral=True)
        return

    await interaction.response.defer()

    members = [member for member in interaction.guild.members if not member.bot]
    success_count = 0
    failed_count = 0
    no_role_count = 0

    for member in members:
        try:
            if role in member.roles:
                await member.remove_roles(role, reason=f"Role {role.name} removed from all members by {interaction.user}")
                success_count += 1
            else:
                no_role_count += 1
        except Exception as e:
            failed_count += 1

    embed = discord.Embed(title="🧹 Role Removal Complete", color=0xff6b6b)
    embed.add_field(name="Role Removed", value=role.mention, inline=True)
    embed.add_field(name="Target", value="All Members", inline=True)
    embed.add_field(name="✅ Successfully Removed", value=str(success_count), inline=True)
    embed.add_field(name="👤 Didn't Have Role", value=str(no_role_count), inline=True)
    embed.add_field(name="❌ Failed", value=str(failed_count), inline=True)
    embed.add_field(name="📊 Total Members", value=str(len(members)), inline=True)
    embed.set_footer(text=f"Role {role.name} has been removed from all eligible members")

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="role-removehumans", description="Remove a specific role from all human members in the server")
@app_commands.describe(role="The role to remove from all human members")
async def role_removehumans(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ You don't have permission to manage roles!", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ I don't have permission to manage roles!", ephemeral=True)
        return

    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ I cannot remove roles that are higher than or equal to my highest role!", ephemeral=True)
        return

    if role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You cannot remove roles that are higher than or equal to your highest role!", ephemeral=True)
        return

    if role == interaction.guild.default_role:
        await interaction.response.send_message("❌ Cannot remove the @everyone role!", ephemeral=True)
        return

    await interaction.response.defer()

    humans = [member for member in interaction.guild.members if not member.bot]
    success_count = 0
    failed_count = 0
    no_role_count = 0

    for member in humans:
        try:
            if role in member.roles:
                await member.remove_roles(role, reason=f"Role {role.name} removed from all humans by {interaction.user}")
                success_count += 1
            else:
                no_role_count += 1
        except Exception as e:
            failed_count += 1

    embed = discord.Embed(title="👥 Role Removal Complete", color=0xff6b6b)
    embed.add_field(name="Role Removed", value=role.mention, inline=True)
    embed.add_field(name="Target", value="Human Members", inline=True)
    embed.add_field(name="✅ Successfully Removed", value=str(success_count), inline=True)
    embed.add_field(name="👤 Didn't Have Role", value=str(no_role_count), inline=True)
    embed.add_field(name="❌ Failed", value=str(failed_count), inline=True)
    embed.add_field(name="👥 Total Humans", value=str(len(humans)), inline=True)
    embed.set_footer(text=f"Role {role.name} has been removed from all eligible human members")

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="role-removebots", description="Remove a specific role from all bot members in the server")
@app_commands.describe(role="The role to remove from all bot members")
async def role_removebots(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ You don't have permission to manage roles!", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ I don't have permission to manage roles!", ephemeral=True)
        return

    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ I cannot remove roles that are higher than or equal to my highest role!", ephemeral=True)
        return

    if role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You cannot remove roles that are higher than or equal to your highest role!", ephemeral=True)
        return

    if role == interaction.guild.default_role:
        await interaction.response.send_message("❌ Cannot remove the @everyone role!", ephemeral=True)
        return

    await interaction.response.defer()

    bots = [member for member in interaction.guild.members if member.bot]
    success_count = 0
    failed_count = 0
    no_role_count = 0

    for member in bots:
        try:
            if role in member.roles:
                await member.remove_roles(role, reason=f"Role {role.name} removed from all bots by {interaction.user}")
                success_count += 1
            else:
                no_role_count += 1
        except Exception as e:
            failed_count += 1

    embed = discord.Embed(title="🤖 Role Removal Complete", color=0xff6b6b)
    embed.add_field(name="Role Removed", value=role.mention, inline=True)
    embed.add_field(name="Target", value="Bot Members", inline=True)
    embed.add_field(name="✅ Successfully Removed", value=str(success_count), inline=True)
    embed.add_field(name="🤖 Didn't Have Role", value=str(no_role_count), inline=True)
    embed.add_field(name="❌ Failed", value=str(failed_count), inline=True)
    embed.add_field(name="🤖 Total Bots", value=str(len(bots)), inline=True)
    embed.set_footer(text=f"Role {role.name} has been removed from all eligible bot members")

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="ping", description="Check bot latency and API response time")
async def ping(interaction: discord.Interaction):
    # Measure API latency
    start_time = datetime.now()
    await interaction.response.defer()
    api_latency = (datetime.now() - start_time).total_seconds() * 1000
    
    # Get WebSocket latency
    ws_latency = bot.latency * 1000
    
    embed = discord.Embed(title="🏓 Pong!", color=0x00ff00)
    embed.add_field(name="API Latency", value=f"{api_latency:.2f}ms", inline=True)
    embed.add_field(name="WebSocket Latency", value=f"{ws_latency:.2f}ms", inline=True)
    embed.set_footer(text="Bot response time")
    embed.timestamp = datetime.now()
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="help", description="Display all available bot commands with descriptions")
async def help_command(interaction: discord.Interaction):
    commands_data = [
        ("🔨 **Moderation Commands**", [
            ("`/mute <user> [duration] [reason]`", "Temporarily mute a user"),
            ("`/unmute <user> [reason]`", "Unmute a user"),
            ("`/timeout <user> <duration> [reason]`", "Timeout a user"),
            ("`/kick <user> [reason]`", "Kick a user from the server"),
            ("`/ban <user> [reason]`", "Ban a user from the server"),
            ("`/unban <user_id> [reason]`", "Unban a user by ID"),
            ("`/set-mute-role <role>`", "Set the mute role for the server")
        ]),
        ("🔒 **Channel Management**", [
            ("`/lockall [reason]`", "Lock all channels in the server"),
            ("`/unlockall [reason]`", "Unlock all channels in the server")
        ]),
        ("🎉 **Welcome System**", [
            ("`/welcome`", "View welcome system status"),
            ("`/welcome-create <channel> <message>`", "Set up welcome system"),
            ("`/welcome-change [channel] [message]`", "Update welcome settings"),
            ("`/welcome-text <message>`", "Update welcome message only"),
            ("`/welcome-toggle`", "Enable/disable welcome system"),
            ("`/welcome-delete`", "Delete welcome system"),
            ("`/welcome-info`", "Show detailed welcome information"),
            ("`/welcome-preview`", "Preview welcome message"),
            ("`/welcome-format`", "Show formatting options")
        ]),
        ("📋 **Server Information**", [
            ("`/roles`", "Display server roles with pagination"),
            ("`/list-bot`", "List all bots in the server"),
            ("`/ping`", "Check bot latency and API response time"),
            ("`/help`", "Show this help menu")
        ]),
        ("👥 **Role Management**", [
            ("`/role-all <role>`", "Add a role to all members in the server"),
            ("`/role-human <role>`", "Add a role to all human members in the server"),
            ("`/role-bots <role>`", "Add a role to all bot members in the server"),
            ("`/role-removeall <role>`", "Remove a specific role from all members"),
            ("`/role-removehumans <role>`", "Remove a specific role from all human members"),
            ("`/role-removebots <role>`", "Remove a specific role from all bot members")
        ]),
        ("🎁 **Giveaway Commands**", [
            ("`/giveaway-create <prize> <duration> [winners] [channel]`", "Create a new giveaway"),
            ("`/giveaway-delete <message_id>`", "Delete a giveaway"),
            ("`/giveaway-edit <message_id> [prize] [duration] [winners]`", "Edit a giveaway"),
            ("`/giveaway-end <message_id>`", "End a giveaway early"),
            ("`/giveaway-reroll <message_id> [winners]`", "Reroll giveaway winners")
        ]),
        ("📈 **Leveling System**", [
            ("`/level [user]`", "Check your or someone's level"),
            ("`/leaderboard`", "Show server level leaderboard"),
            ("`/leveling-setup [channel] [xp_per_message] [cooldown]`", "Setup leveling system"),
            ("`/leveling-toggle`", "Enable/disable leveling system"),
            ("`/add-xp <user> <amount>`", "Add XP to a user (Admin only)")
        ]),
        ("🎫 **Ticket System**", [
            ("`/ticket-setup <category> <staff_role>`", "Setup ticket system"),
            ("`/ticket [reason]`", "Create a new support ticket"),
            ("`/close-ticket`", "Close a ticket channel")
        ]),
        ("📌 **Sticky Messages**", [
            ("`/stick <message>`", "Stick a message to the channel"),
            ("`/stickstop`", "Stop the stickied message in the channel"),
            ("`/stickstart`", "Restart a stopped sticky message"),
            ("`/stickremove`", "Remove the stickied message"),
            ("`/getstickies`", "Show all active and stopped stickies")
        ])
    ]

    # Pagination setup
    commands_per_page = 1  # Show 1 category per page for better readability with SelectMenu
    total_pages = len(commands_data)
    current_page = 0

    def create_embed(page):
        embed = discord.Embed(
            title="🤖 Bot Commands Help",
            color=0x0099ff,
            timestamp=datetime.now()
        )

        category_name, commands = commands_data[page]
        embed.add_field(name=category_name, value="\n".join([f"{cmd} - {desc}" for cmd, desc in commands]), inline=False)

        embed.set_footer(text=f"Page {page + 1}/{total_pages} • Use dropdown to jump to categories")
        return embed

    def create_view(page):
        view = discord.ui.View(timeout=300)

        # Category SelectMenu
        category_select = discord.ui.Select(
            placeholder="📋 Select a command category...",
            options=[
                discord.SelectOption(
                    label=commands_data[i][0].replace("**", "").replace("*", ""),
                    description=f"{len(commands_data[i][1])} commands available",
                    value=str(i),
                    emoji=commands_data[i][0].split()[0]
                ) for i in range(len(commands_data))
            ]
        )

        async def select_callback(select_interaction):
            nonlocal current_page
            current_page = int(select_interaction.data['values'][0])
            embed = create_embed(current_page)
            view = create_view(current_page)
            await select_interaction.response.edit_message(embed=embed, view=view)

        category_select.callback = select_callback
        view.add_item(category_select)

        # Previous button
        prev_button = discord.ui.Button(
            label="◀ Previous",
            style=discord.ButtonStyle.primary,
            disabled=page == 0
        )

        async def prev_callback(button_interaction):
            nonlocal current_page
            current_page = max(0, current_page - 1)
            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)

        prev_button.callback = prev_callback
        view.add_item(prev_button)

        # Page indicator
        page_button = discord.ui.Button(
            label=f"{page + 1}/{total_pages}",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        view.add_item(page_button)

        # Next button
        next_button = discord.ui.Button(
            label="Next ▶",
            style=discord.ButtonStyle.primary,
            disabled=page >= total_pages - 1
        )

        async def next_callback(button_interaction):
            nonlocal current_page
            current_page = min(total_pages - 1, current_page + 1)
            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)

        next_button.callback = next_callback
        view.add_item(next_button)

        # All Commands button
        all_commands_button = discord.ui.Button(
            label="📋 All Commands",
            style=discord.ButtonStyle.success
        )

        async def all_commands_callback(button_interaction):
            all_embed = discord.Embed(
                title="🤖 All Bot Commands",
                color=0x0099ff,
                timestamp=datetime.now()
            )

            for category_name, commands in commands_data:
                command_list = "\n".join([f"{cmd}" for cmd, desc in commands[:5]])  # Show first 5 commands
                if len(commands) > 5:
                    command_list += f"\n*... and {len(commands) - 5} more*"
                all_embed.add_field(name=category_name, value=command_list, inline=True)

            all_embed.set_footer(text="Use the dropdown menu to see detailed descriptions")

            view_all = discord.ui.View(timeout=300)
            back_button = discord.ui.Button(label="◀ Back to Help", style=discord.ButtonStyle.secondary)

            async def back_callback(back_interaction):
                embed = create_embed(current_page)
                view = create_view(current_page)
                await back_interaction.response.edit_message(embed=embed, view=view)

            back_button.callback = back_callback
            view_all.add_item(back_button)

            await button_interaction.response.edit_message(embed=all_embed, view=view_all)

        all_commands_button.callback = all_commands_callback
        view.add_item(all_commands_button)

        return view

    embed = create_embed(current_page)
    view = create_view(current_page)

    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="welcome-format", description="Show available formatting options for welcome messages")
async def welcome_format(interaction: discord.Interaction):
    embed = discord.Embed(title="🎨 Welcome Message Formatting", color=0x0099ff)

    embed.add_field(name="Available Variables", value="`{user}` - Mentions the new user\n`{username}` - User's display name\n`{server}` - Server name\n`{membercount}` - Current member count", inline=False)

    embed.add_field(name="Example Message", value="Welcome {user} to **{server}**! 🎉\nYou are our {membercount}th member!", inline=False)

    embed.add_field(name="Result", value=f"Welcome {interaction.user.mention} to **{interaction.guild.name}**! 🎉\nYou are our {interaction.guild.member_count}th member!", inline=False)

    embed.set_footer(text="Use these variables in your welcome message for dynamic content!")

    await interaction.response.send_message(embed=embed, ephemeral=True)

# Role Info Command with Pagination
@bot.tree.command(name="roles", description="Display server roles with pagination")
async def role_info(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ You don't have permission to view role information!", ephemeral=True)
        return

    roles = [role for role in interaction.guild.roles if role != interaction.guild.default_role]
    roles.sort(key=lambda r: r.position, reverse=True)

    if not roles:
        await interaction.response.send_message("❌ No roles found in this server!", ephemeral=True)
        return

    # Pagination setup
    roles_per_page = 10
    total_pages = (len(roles) + roles_per_page - 1) // roles_per_page
    current_page = 0

    def create_embed(page):
        start_idx = page * roles_per_page
        end_idx = min(start_idx + roles_per_page, len(roles))
        page_roles = roles[start_idx:end_idx]

        embed = discord.Embed(
            title=f"📋 Server Roles ({len(roles)} total)",
            color=0x0099ff,
            timestamp=datetime.now()
        )

        role_list = []
        for role in page_roles:
            role_list.append(f"{role.mention} `({role.id})`")

        embed.description = "\n".join(role_list)
        embed.set_footer(text=f"Page {page + 1}/{total_pages} • {interaction.guild.name}")

        return embed

    def create_view(page):
        view = discord.ui.View(timeout=300)

        # Previous button
        prev_button = discord.ui.Button(
            label="◀️ Previous",
            style=discord.ButtonStyle.secondary,
            disabled=(page == 0)
        )

        async def prev_callback(button_interaction):
            nonlocal current_page
            current_page = max(0, current_page - 1)
            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)

        prev_button.callback = prev_callback
        view.add_item(prev_button)

        # Page indicator
        page_button = discord.ui.Button(
            label=f"{page + 1}/{total_pages}",
            style=discord.ButtonStyle.primary,
            disabled=True
        )
        view.add_item(page_button)

        # Next button
        next_button = discord.ui.Button(
            label="Next ▶️",
            style=discord.ButtonStyle.secondary,
            disabled=(page >= total_pages - 1)
        )

        async def next_callback(button_interaction):
            nonlocal current_page
            current_page = min(total_pages - 1, current_page + 1)
            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)

        next_button.callback = next_callback
        view.add_item(next_button)

        # Refresh button
        refresh_button = discord.ui.Button(
            label="🔄 Refresh",
            style=discord.ButtonStyle.success
        )

        async def refresh_callback(button_interaction):
            # Refresh the roles list
            updated_roles = [role for role in button_interaction.guild.roles if role != button_interaction.guild.default_role]
            updated_roles.sort(key=lambda r: r.position, reverse=True)
            nonlocal roles, total_pages, current_page
            roles = updated_roles
            total_pages = (len(roles) + roles_per_page - 1) // roles_per_page
            current_page = min(current_page, total_pages - 1) if total_pages > 0 else 0

            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)

        refresh_button.callback = refresh_callback
        view.add_item(refresh_button)

        return view

    embed = create_embed(current_page)
    view = create_view(current_page)

    await interaction.response.send_message(embed=embed, view=view)

# Leveling System Commands
@bot.tree.command(name="level", description="Check your or someone else's level")
@app_commands.describe(user="The user to check level for (optional)")
async def level(interaction: discord.Interaction, user: discord.Member = None):
    target_user = user or interaction.user
    guild_id = interaction.guild.id
    user_id = target_user.id

    if guild_id not in leveling_data:
        leveling_data[guild_id] = {}

    if user_id not in leveling_data[guild_id]:
        leveling_data[guild_id][user_id] = {'xp': 0, 'level': 1, 'total_xp': 0}

    user_data = leveling_data[guild_id][user_id]

    embed = discord.Embed(title=f"📊 {target_user.display_name}'s Level", color=0x00ff00)
    embed.add_field(name="Level", value=f"**{user_data['level']}**", inline=True)
    embed.add_field(name="XP", value=f"**{user_data['xp']}** / **{calculate_xp_needed(user_data['level'])}**", inline=True)
    embed.add_field(name="Total XP", value=f"**{user_data['total_xp']}**", inline=True)
    embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard", description="Show the server level leaderboard")
async def leaderboard(interaction: discord.Interaction):
    guild_id = interaction.guild.id

    if guild_id not in leveling_data or not leveling_data[guild_id]:
        await interaction.response.send_message("❌ No leveling data found for this server!", ephemeral=True)
        return

    # Sort users by total XP
    sorted_users = sorted(leveling_data[guild_id].items(), key=lambda x: x[1]['total_xp'], reverse=True)

    embed = discord.Embed(title="🏆 Server Leaderboard", color=0xffd700)

    for i, (user_id, data) in enumerate(sorted_users[:10], 1):
        try:
            user = interaction.guild.get_member(user_id)
            if user:
                embed.add_field(
                    name=f"{i}. {user.display_name}",
                    value=f"Level {data['level']} • {data['total_xp']} Total XP",
                    inline=False
                )
        except:
            continue

    if not embed.fields:
        embed.description = "No active users found!"

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leveling-setup", description="Setup the leveling system")
@app_commands.describe(
    channel="Channel for level up messages (optional)",
    xp_per_message="XP gained per message (default: 15)",
    cooldown="Cooldown between XP gains in seconds (default: 60)"
)
async def leveling_setup(interaction: discord.Interaction, channel: discord.TextChannel = None, xp_per_message: int = 15, cooldown: int = 60):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permission to setup leveling!", ephemeral=True)
        return

    guild_id = interaction.guild.id

    if xp_per_message < 1 or xp_per_message > 100:
        await interaction.response.send_message("❌ XP per message must be between 1 and 100!", ephemeral=True)
        return

    if cooldown < 10 or cooldown > 300:
        await interaction.response.send_message("❌ Cooldown must be between 10 and 300 seconds!", ephemeral=True)
        return

    leveling_config[guild_id] = {
        'enabled': True,
        'channel_id': channel.id if channel else None,
        'xp_per_message': xp_per_message,
        'xp_cooldown': cooldown
    }

    embed = discord.Embed(title="✅ Leveling System Setup", color=0x00ff00)
    embed.add_field(name="Status", value="✅ Enabled", inline=True)
    embed.add_field(name="Level Up Channel", value=channel.mention if channel else "Current channel", inline=True)
    embed.add_field(name="XP per Message", value=str(xp_per_message), inline=True)
    embed.add_field(name="XP Cooldown", value=f"{cooldown} seconds", inline=True)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leveling-toggle", description="Enable or disable the leveling system")
async def leveling_toggle(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permission to manage leveling!", ephemeral=True)
        return

    guild_id = interaction.guild.id

    if guild_id not in leveling_config:
        await interaction.response.send_message("❌ Leveling system not configured! Use `/leveling-setup` first.", ephemeral=True)
        return

    current_status = leveling_config[guild_id].get('enabled', True)
    leveling_config[guild_id]['enabled'] = not current_status

    status = "✅ Enabled" if not current_status else "❌ Disabled"
    color = 0x00ff00 if not current_status else 0xff0000

    embed = discord.Embed(title=f"Leveling System {status.split()[1]}", color=color)
    embed.add_field(name="Status", value=status, inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="add-xp", description="Add XP to a user (Admin only)")
@app_commands.describe(user="The user to add XP to", amount="Amount of XP to add")
async def add_xp(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permission to add XP!", ephemeral=True)
        return

    if amount < 1 or amount > 10000:
        await interaction.response.send_message("❌ XP amount must be between 1 and 10,000!", ephemeral=True)
        return

    guild_id = interaction.guild.id
    user_id = user.id

    if guild_id not in leveling_data:
        leveling_data[guild_id] = {}

    if user_id not in leveling_data[guild_id]:
        leveling_data[guild_id][user_id] = {'xp': 0, 'level': 1, 'total_xp': 0}

    leveling_data[guild_id][user_id]['xp'] += amount
    leveling_data[guild_id][user_id]['total_xp'] += amount

    # Check for level up
    await check_level_up(user, guild_id, interaction.channel)

    embed = discord.Embed(title="✅ XP Added", color=0x00ff00)
    embed.add_field(name="User", value=user.mention, inline=True)
    embed.add_field(name="XP Added", value=str(amount), inline=True)
    embed.add_field(name="New Total XP", value=str(leveling_data[guild_id][user_id]['total_xp']), inline=True)

    await interaction.response.send_message(embed=embed)

# Ticket System Commands
@bot.tree.command(name="ticket-setup", description="Setup the ticket system")
@app_commands.describe(category="Category for ticket channels", staff_role="Role that can view tickets")
async def ticket_setup(interaction: discord.Interaction, category: discord.CategoryChannel, staff_role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permission to setup tickets!", ephemeral=True)
        return

    guild_id = interaction.guild.id

    ticket_config[guild_id] = {
        'category_id': category.id,
        'staff_roles': [staff_role.id],
        'enabled': True
    }

    embed = discord.Embed(title="🎫 Ticket System Setup", color=0x00ff00)
    embed.add_field(name="Category", value=category.name, inline=True)
    embed.add_field(name="Staff Role", value=staff_role.mention, inline=True)
    embed.add_field(name="Status", value="✅ Enabled", inline=True)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ticket", description="Create a new support ticket")
@app_commands.describe(reason="Reason for creating the ticket")
async def create_ticket(interaction: discord.Interaction, reason: str = "No reason provided"):
    guild_id = interaction.guild.id

    if guild_id not in ticket_config or not ticket_config[guild_id].get('enabled', False):
        await interaction.response.send_message("❌ Ticket system is not enabled on this server!", ephemeral=True)
        return

    # Check if user already has an open ticket
    user_ticket = None
    for channel_id, ticket_data in active_tickets.items():
        if ticket_data['user_id'] == interaction.user.id and ticket_data['guild_id'] == guild_id:
            user_ticket = interaction.guild.get_channel(channel_id)
            break

    if user_ticket:
        await interaction.response.send_message(f"❌ You already have an open ticket: {user_ticket.mention}", ephemeral=True)
        return

    category = interaction.guild.get_channel(ticket_config[guild_id]['category_id'])
    if not category:
        await interaction.response.send_message("❌ Ticket category not found! Please contact an administrator.", ephemeral=True)
        return

    # Generate ticket number
    ticket_number = len([t for t in active_tickets.values() if t['guild_id'] == guild_id]) + 1

    # Create ticket channel
    channel_name = f"ticket-{interaction.user.name}-{ticket_number}"

    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    # Add staff roles
    for role_id in ticket_config[guild_id]['staff_roles']:
        role = interaction.guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    try:
        ticket_channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        # Store ticket data
        active_tickets[ticket_channel.id] = {
            'user_id': interaction.user.id,
            'guild_id': guild_id,
            'ticket_number': ticket_number
        }

        # Create ticket embed
        embed = discord.Embed(title="🎫 Support Ticket", color=0x0099ff)
        embed.add_field(name="Created by", value=interaction.user.mention, inline=True)
        embed.add_field(name="Ticket #", value=str(ticket_number), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text="Staff will be with you shortly!")
        embed.timestamp = datetime.now()

        # Create close button
        class TicketView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
            async def close_ticket(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.channel.id not in active_tickets:
                    await button_interaction.response.send_message("❌ This is not a valid ticket channel!", ephemeral=True)
                    return

                ticket_data = active_tickets[button_interaction.channel.id]

                # Check permissions
                is_ticket_owner = button_interaction.user.id == ticket_data['user_id']
                is_staff = any(role.id in ticket_config[guild_id]['staff_roles'] for role in button_interaction.user.roles)
                is_admin = button_interaction.user.guild_permissions.administrator

                if not (is_ticket_owner or is_staff or is_admin):
                    await button_interaction.response.send_message("❌ You don't have permission to close this ticket!", ephemeral=True)
                    return

                # Create transcript (simple version)
                transcript_embed = discord.Embed(title="🎫 Ticket Closed", color=0xff0000)
                transcript_embed.add_field(name="Ticket #", value=str(ticket_data['ticket_number']), inline=True)
                transcript_embed.add_field(name="Closed by", value=button_interaction.user.mention, inline=True)
                transcript_embed.add_field(name="Original Creator", value=f"<@{ticket_data['user_id']}>", inline=True)
                transcript_embed.timestamp = datetime.now()

                await button_interaction.response.send_message(embed=transcript_embed)

                # Remove from active tickets
                del active_tickets[button_interaction.channel.id]

                # Delete channel after 5 seconds
                await asyncio.sleep(5)
                await button_interaction.channel.delete()

        view = TicketView()
        await ticket_channel.send(embed=embed, view=view)

        await interaction.response.send_message(f"✅ Ticket created: {ticketchannel.mention}", ephemeral=True)

    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to create channels!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="close-ticket", description="Close a ticket channel")
async def close_ticket_command(interaction: discord.Interaction):
    if interaction.channel.id not in active_tickets:
        await interaction.response.send_message("❌ This is not a ticket channel!", ephemeral=True)
        return

    guild_id = interaction.guild.id
    ticket_data = active_tickets[interaction.channel.id]

    # Check permissions
    is_ticket_owner = interaction.user.id == ticket_data['user_id']
    is_staff = any(role.id in ticket_config[guild_id]['staff_roles'] for role in interaction.user.roles)
    is_admin = interaction.user.guild_permissions.administrator

    if not (is_ticket_owner or is_staff or is_admin):
        await interaction.response.send_message("❌ You don't have permission to close this ticket!", ephemeral=True)
        return

    embed = discord.Embed(title="🎫 Ticket Closed", color=0xff0000)
    embed.add_field(name="Closed by", value=interaction.user.mention, inline=True)
    embed.description = "This ticket will be deleted in 5 seconds..."
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed)

    # Remove from active tickets
    del active_tickets[interaction.channel.id]

    # Delete channel after 5 seconds
    await asyncio.sleep(5)
    await interaction.channel.delete()

# Helper functions for leveling
def calculate_xp_needed(level):
    """Calculate XP needed for next level"""
    return 100 * (level ** 2)

async def check_level_up(user, guild_id, channel):
    """Check if user leveled up and send message"""
    user_data = leveling_data[guild_id][user.id]
    current_level = user_data['level']

    while user_data['xp'] >= calculate_xp_needed(current_level):
        user_data['xp'] -= calculate_xp_needed(current_level)
        user_data['level'] += 1

        # Send level up message
        config = leveling_config.get(guild_id, {})
        if config.get('enabled', True):
            level_channel = None
            if config.get('channel_id'):
                level_channel = user.guild.get_channel(config['channel_id'])
            level_channel = level_channel or channel

            embed = discord.Embed(title="🎉 Level Up!", color=0xffd700)
            embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="New Level", value=str(user_data['level']), inline=True)
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)

            try:
                await level_channel.send(embed=embed)
            except:
                pass

        current_level = user_data['level']

# XP tracking for messages
user_xp_cooldowns = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = message.guild.id if message.guild else None
    if not guild_id:
        return

    # Check if leveling is enabled
    if guild_id not in leveling_config or not leveling_config[guild_id].get('enabled', True):
        return

    user_id = message.author.id

    # Check cooldown
    cooldown_key = f"{guild_id}_{user_id}"
    now = datetime.now()
    cooldown_time = leveling_config[guild_id].get('xp_cooldown', 60)

    if cooldown_key in user_xp_cooldowns:
        if (now - user_xp_cooldowns[cooldown_key]).total_seconds() < cooldown_time:
            return

    user_xp_cooldowns[cooldown_key] = now

    # Initialize user data
    if guild_id not in leveling_data:
        leveling_data[guild_id] = {}

    if user_id not in leveling_data[guild_id]:
        leveling_data[guild_id][user_id] = {'xp': 0, 'level': 1, 'total_xp': 0}

    # Add XP
    xp_gain = leveling_config[guild_id].get('xp_per_message', 15)
    leveling_data[guild_id][user_id]['xp'] += xp_gain
    leveling_data[guild_id][user_id]['total_xp'] += xp_gain

    # Check for level up
    await check_level_up(message.author, guild_id, message.channel)

    # Sticky Message System
    channel_id = message.channel.id
    if channel_id in sticky_messages and sticky_messages[channel_id]['active']:
        await send_sticky_message(message.channel, channel_id)

async def send_sticky_message(channel, channel_id):
    """Sends or resends the sticky message"""
    data = sticky_messages[channel_id]
    try:
        # Delete the previous sticky message
        if data.get('last_message_id'):
            try:
                old_message = await channel.fetch_message(data['last_message_id'])
                await old_message.delete()
            except:
                pass

        # Send the new sticky message
        embed = discord.Embed(
            title="📌 Sticky Message",
            description=data['message'],
            color=discord.Color.gold()
        )
        embed.set_footer(text="This message is pinned to this channel")
        new_message = await channel.send(embed=embed)

        # Update the last_message_id
        data['last_message_id'] = new_message.id

    except Exception as e:
        print(f"Error sending sticky message: {e}")

# Giveaway Commands
@bot.tree.command(name="giveaway-create", description="Create a new giveaway")
@app_commands.describe(
    prize="What you're giving away",
    duration="Duration (e.g., 1h, 30m, 2d)",
    winners="Number of winners (default: 1)",
    channel="Channel to post giveaway (default: current channel)"
)
async def giveaway_create(interaction: discord.Interaction, prize: str, duration: str, winners: int = 1, channel: discord.TextChannel = None):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to create giveaways!", ephemeral=True)
        return

    if winners < 1:
        await interaction.response.send_message("❌ Number of winners must be at least 1!", ephemeral=True)
        return

    # Parse duration
    try:
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        duration_lower = duration.lower()

        if duration_lower[-1] in time_units:
            time_value = int(duration_lower[:-1])
            time_unit = duration_lower[-1]
            total_seconds = time_value * time_units[time_unit]
        else:
            raise ValueError("Invalid format")

        if total_seconds < 60:  # Minimum 1 minute
            await interaction.response.send_message("❌ Minimum giveaway duration is 1 minute!", ephemeral=True)
            return

        if total_seconds > 2592000:  # Maximum 30 days
            await interaction.response.send_message("❌ Maximum giveaway duration is 30 days!", ephemeral=True)
            return

    except (ValueError, IndexError):
        await interaction.response.send_message("❌ Invalid duration format! Use format like: 1h, 30m, 2d", ephemeral=True)
        return

    channel = channel or interaction.channel

    if not channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}!", ephemeral=True)
        return

    end_time = datetime.now() + timedelta(seconds=total_seconds)

    # Create giveaway embed
    embed = discord.Embed(title="🎉 GIVEAWAY 🎉", color=0xff6b6b)
    embed.add_field(name="Prize", value=f"**{prize}**", inline=False)
    embed.add_field(name="Ends", value=f"<t:{int(end_time.timestamp())}:R> (<t:{int(end_time.timestamp())}:f>)", inline=False)
    embed.add_field(name="Hosted by", value=interaction.user.mention, inline=True)
    embed.add_field(name="Entries", value="**0**", inline=True)
    embed.add_field(name="Winners", value=f"**{winners}**", inline=True)
    embed.add_field(name="How to enter", value="Click the 🎉 button below to enter!", inline=False)
    embed.set_footer(text="Good luck!")
    embed.timestamp = end_time

    # Create join button
    class GiveawayView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="🎉 Join Giveaway", style=discord.ButtonStyle.green, custom_id="join_giveaway")
        async def join_giveaway(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            message_id = button_interaction.message.id
            giveaway = giveaway_data.get(message_id)

            if not giveaway:
                await button_interaction.response.send_message("❌ This giveaway no longer exists!", ephemeral=True)
                return

            if datetime.now() >= giveaway['end_time']:
                await button_interaction.response.send_message("❌ This giveaway has already ended!", ephemeral=True)
                return

            user_id = button_interaction.user.id

            if user_id in giveaway['participants']:
                giveaway['participants'].remove(user_id)
                response_msg = "✅ You have left the giveaway!"
            else:
                giveaway['participants'].add(user_id)
                response_msg = "✅ You have joined the giveaway! Good luck!"

            # Update the embed with new entry count
            embed = button_interaction.message.embeds[0]
            entry_count = len(giveaway['participants'])

            # Update the entries field (field index 3)
            embed.set_field_at(3, name="Entries", value=f"**{entry_count}**", inline=True)

            await button_interaction.response.edit_message(embed=embed, view=self)
            await button_interaction.followup.send(response_msg, ephemeral=True)

    view = GiveawayView()

    try:
        message = await channel.send(embed=embed, view=view)

        # Store giveaway data
        giveaway_data[message.id] = {
            'host': interaction.user.id,
            'prize': prize,
            'end_time': end_time,
            'channel_id': channel.id,
            'guild_id': interaction.guild.id,
            'winners': winners,
            'participants': set()
        }

        # Update embed to include giveaway ID
        embed.add_field(name="Giveaway ID", value=f"`{message.id}`", inline=True)
        await message.edit(embed=embed, view=view)

        # Schedule giveaway end
        asyncio.create_task(schedule_giveaway_end(message.id, total_seconds))

        await interaction.response.send_message(f"✅ Giveaway created in {channel.mention}!\n**Giveaway ID:** `{message.id}`", ephemeral=True)

    except discord.Forbidden:
        await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}!", ephemeral=True)

@bot.tree.command(name="giveaway-delete", description="Delete a giveaway")
@app_commands.describe(message_id="The message ID of the giveaway to delete")
async def giveaway_delete(interaction: discord.Interaction, message_id: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to delete giveaways!", ephemeral=True)
        return

    try:
        message_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
        return

    giveaway = giveaway_data.get(message_id)

    if not giveaway:
        await interaction.response.send_message("❌ Giveaway not found!", ephemeral=True)
        return

    if giveaway['host'] != interaction.user.id and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You can only delete your own giveaways!", ephemeral=True)
        return

    # Try to delete the message
    try:
        channel = bot.get_channel(giveaway['channel_id'])
        if channel:
            message = await channel.fetch_message(message_id)
            await message.delete()
    except:
        pass  # Message might already be deleted

    # Remove from data
    del giveaway_data[message_id]

    await interaction.response.send_message("✅ Giveaway has been deleted!", ephemeral=True)

@bot.tree.command(name="giveaway-edit", description="Edit a giveaway")
@app_commands.describe(
    message_id="The message ID of the giveaway to edit",
    prize="New prize (optional)",
    duration="New duration (optional, e.g., 1h, 30m, 2d)",
    winners="New number of winners (optional)"
)
async def giveaway_edit(interaction: discord.Interaction, message_id: str, prize: str = None, duration: str = None, winners: int = None):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to edit giveaways!", ephemeral=True)
        return

    try:
        message_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
        return

    giveaway = giveaway_data.get(message_id)

    if not giveaway:
        await interaction.response.send_message("❌ Giveaway not found!", ephemeral=True)
        return

    if giveaway['host'] != interaction.user.id and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You can only edit your own giveaways!", ephemeral=True)
        return

    if datetime.now() >= giveaway['end_time']:
        await interaction.response.send_message("❌ Cannot edit an ended giveaway!", ephemeral=True)
        return

    changes = []

    # Update prize
    if prize:
        giveaway['prize'] = prize
        changes.append("prize")

    # Update duration
    if duration:
        try:
            time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
            duration_lower = duration.lower()

            if duration_lower[-1] in time_units:
                time_value = int(duration_lower[:-1])
                time_unit = duration_lower[-1]
                total_seconds = time_value * time_units[time_unit]
            else:
                raise ValueError("Invalid format")

            if total_seconds < 60:
                await interaction.response.send_message("❌ Minimum giveaway duration is 1 minute!", ephemeral=True)
                return

            if total_seconds > 2592000:
                await interaction.response.send_message("❌ Maximum giveaway duration is 30 days!", ephemeral=True)
                return

            giveaway['end_time'] = datetime.now() + timedelta(seconds=total_seconds)
            changes.append("duration")

        except (ValueError, IndexError):
            await interaction.response.send_message("❌ Invalid duration format! Use format like: 1h, 30m, 2d", ephemeral=True)
            return

    # Update winners
    if winners:
        if winners < 1:
            await interaction.response.send_message("❌ Number of winners must be at least 1!", ephemeral=True)
            return
        giveaway['winners'] = winners
        changes.append("winners")

    if not changes:
        await interaction.response.send_message("❌ You must specify at least one thing to change!", ephemeral=True)
        return

    # Update the message
    try:
        channel = bot.get_channel(giveaway['channel_id'])
        message = await channel.fetch_message(message_id)

        embed = discord.Embed(title="🎉 GIVEAWAY 🎉", color=0xff6b6b)
        embed.add_field(name="Prize", value=f"**{giveaway['prize']}**", inline=False)
        embed.add_field(name="Ends", value=f"<t:{int(giveaway['end_time'].timestamp())}:R> (<t:{int(giveaway['end_time'].timestamp())}:f>)", inline=False)
        embed.add_field(name="Hosted by", value=f"<@{giveaway['host']}>", inline=True)
        embed.add_field(name="Entries", value=f"**{len(giveaway['participants'])}**", inline=True)
        embed.add_field(name="Winners", value=f"**{giveaway['winners']}**", inline=True)
        embed.add_field(name="How to enter", value="Click the 🎉 button below to enter!", inline=False)
        embed.set_footer(text="Good luck! (Edited)")
        embed.timestamp = giveaway['end_time']

        await message.edit(embed=embed)

        await interaction.response.send_message(f"✅ Giveaway updated! Changed: {', '.join(changes)}", ephemeral=True)

    except discord.NotFound:
        await interaction.response.send_message("❌ Giveaway message not found!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="giveaway-end", description="End a giveaway early")
@app_commands.describe(message_id="The message ID of the giveaway to end")
async def giveaway_end(interaction: discord.Interaction, message_id: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to end giveaways!", ephemeral=True)
        return

    try:
        message_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
        return

    giveaway = giveaway_data.get(message_id)

    if not giveaway:
        await interaction.response.send_message("❌ Giveaway not found!", ephemeral=True)
        return

    if giveaway['host'] != interaction.user.id and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You can only end your own giveaways!", ephemeral=True)
        return

    await end_giveaway(message_id, early=True)
    await interaction.response.send_message("✅ Giveaway has been ended early!", ephemeral=True)

@bot.tree.command(name="giveaway-reroll", description="Reroll giveaway winners")
@app_commands.describe(
    message_id="The message ID of the giveaway to reroll",
    winners="Number of new winners to pick (optional, uses original amount)"
)
async def giveaway_reroll(interaction: discord.Interaction, message_id: str, winners: int = None):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to reroll giveaways!", ephemeral=True)
        return

    try:
        message_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
        return

    # Check if this was a giveaway (might be ended and removed from active data)
    giveaway = giveaway_data.get(message_id)

    # Try to get the message to check if it was a giveaway
    try:
        for channel in interaction.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
                if message.author == bot.user and message.embeds and "GIVEAWAY" in message.embeds[0].title:
                    break
            except:
                continue
        else:
            await interaction.response.send_message("❌ Giveaway message not found!", ephemeral=True)
            return
    except:
        await interaction.response.send_message("❌ Could not find giveaway message!", ephemeral=True)
        return

    if giveaway and datetime.now() < giveaway['end_time']:
        await interaction.response.send_message("❌ Cannot reroll an active giveaway! End it first.", ephemeral=True)
        return

    # If no giveaway data, try to get participants from button interactions (limited)
    if not giveaway:
        await interaction.response.send_message("❌ Cannot reroll this giveaway - participant data not available!", ephemeral=True)
        return

    participants = list(giveaway['participants'])

    if not participants:
        await interaction.response.send_message("❌ No participants to reroll!", ephemeral=True)
        return

    winner_count = winners or giveaway['winners']
    winner_count = min(winner_count, len(participants))

    import random
    new_winners = random.sample(participants, winner_count)

    # Create reroll embed
    embed = discord.Embed(title="🎉 GIVEAWAY REROLLED 🎉", color=0x00ff00)
    embed.add_field(name="Prize", value=giveaway['prize'], inline=False)

    if len(new_winners) == 1:
        embed.add_field(name="New Winner", value=f"<@{new_winners[0]}>", inline=False)
    else:
        winners_list = "\n".join([f"<@{winner}>" for winner in new_winners])
        embed.add_field(name="New Winners", value=winners_list, inline=False)

    embed.set_footer(text="Congratulations!")
    embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=embed)

async def schedule_giveaway_end(message_id: int, delay_seconds: int):
    """Schedule a giveaway to end after the specified delay"""
    await asyncio.sleep(delay_seconds)
    await end_giveaway(message_id)

async def end_giveaway(message_id: int, early: bool = False):
    """End a giveaway and pick winners"""
    giveaway = giveaway_data.get(message_id)

    if not giveaway:
        return

    participants = list(giveaway['participants'])

    try:
        channel = bot.get_channel(giveaway['channel_id'])
        message = await channel.fetch_message(message_id)

        # Create ended giveaway embed
        embed = discord.Embed(title="🎉 GIVEAWAY ENDED 🎉", color=0x555555)
        embed.add_field(name="Prize", value=giveaway['prize'], inline=False)
        embed.add_field(name="Hosted by", value=f"<@{giveaway['host']}>", inline=True)

        if participants:
            import random
            winner_count = min(giveaway['winners'], len(participants))
            winners = random.sample(participants, winner_count)

            if len(winners) == 1:
                embed.add_field(name="Winner", value=f"<@{winners[0]}>", inline=False)
                winner_mentions = f"<@{winners[0]}>"
            else:
                winners_list = "\n".join([f"<@{winner}>" for winner in winners])
                embed.add_field(name="Winners", value=winners_list, inline=False)
                winner_mentions = " ".join([f"<@{winner}>" for winner in winners])

            embed.set_footer(text="Congratulations to the winner(s)!" + (" (Ended Early)" if early else ""))

            # Send winner announcement
            await channel.send(f"🎉 Congratulations {winner_mentions}! You won **{giveaway['prize']}**!")

        else:
            embed.add_field(name="Winner", value="No participants", inline=False)
            embed.set_footer(text="No one participated in this giveaway" + (" (Ended Early)" if early else ""))

        embed.timestamp = datetime.now()

        # Update the original message
        await message.edit(embed=embed, view=None)

    except Exception as e:
        print(f"Error ending giveaway {message_id}: {e}")

    # Remove from active giveaways
    if message_id in giveaway_data:
        del giveaway_data[message_id]

# Welcome event handler
@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    welcome_config = welcome_data.get(guild_id)

    if not welcome_config or not welcome_config.get('enabled', True):
        return

    channel = member.guild.get_channel(welcome_config['channel_id'])
    if not channel:
        return

    message = welcome_config['message']
    formatted_message = message.replace('{user}', member.mention)
    formatted_message = formatted_message.replace('{username}', member.display_name)
    formatted_message = formatted_message.replace('{server}', member.guild.name)
    formatted_message = formatted_message.replace('{membercount}', str(member.guild.member_count))

    try:
        embed = discord.Embed(description=formatted_message, color=0x00ff00)
        embed.set_author(name=f"Welcome to {member.guild.name}!", icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.timestamp = datetime.now()

        await channel.send(embed=embed)
    except:
        # Fallback to plain text if embed fails
        await channel.send(formatted_message)

# Sticky Message Commands
@bot.tree.command(name="stick", description="Sticks a message to the channel")
async def stick_message(interaction: discord.Interaction, message: str):
    """Stick a message to the channel"""
    if not interaction.user.guild_permissions.manage_messages:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need the 'Manage Messages' permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    channel_id = interaction.channel.id
    
    # Remove existing sticky if any
    if channel_id in sticky_messages:
        old_data = sticky_messages[channel_id]
        if old_data.get('last_message_id'):
            try:
                old_message = await interaction.channel.fetch_message(old_data['last_message_id'])
                await old_message.delete()
            except:
                pass
    
    # Create new sticky
    sticky_messages[channel_id] = {
        'message': message,
        'active': True,
        'last_message_id': None
    }
    
    # Post the sticky message
    sticky_embed = discord.Embed(
        title="📌 Sticky Message",
        description=message,
        color=discord.Color.gold()
    )
    sticky_embed.set_footer(text="This message is pinned to this channel")
    
    sticky_msg = await interaction.channel.send(embed=sticky_embed)
    sticky_messages[channel_id]['last_message_id'] = sticky_msg.id
    
    embed = discord.Embed(
        title="✅ Sticky Message Created",
        description=f"Successfully created sticky message in {interaction.channel.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="stickstop", description="Stops the stickied message in the channel")
async def stick_stop(interaction: discord.Interaction):
    """Stop the sticky message in the channel"""
    if not interaction.user.guild_permissions.manage_messages:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need the 'Manage Messages' permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    channel_id = interaction.channel.id
    
    if channel_id not in sticky_messages:
        embed = discord.Embed(
            title="❌ No Sticky Message",
            description="There is no sticky message in this channel.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    sticky_messages[channel_id]['active'] = False
    
    embed = discord.Embed(
        title="⏸️ Sticky Message Stopped",
        description="The sticky message has been stopped but not deleted. Use `/stickstart` to resume it.",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="stickstart", description="Restarts a stopped sticky message using the previous message")
async def stick_start(interaction: discord.Interaction):
    """Restart the sticky message in the channel"""
    if not interaction.user.guild_permissions.manage_messages:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need the 'Manage Messages' permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    channel_id = interaction.channel.id
    
    if channel_id not in sticky_messages:
        embed = discord.Embed(
            title="❌ No Sticky Message",
            description="There is no sticky message configured for this channel.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    sticky_data = sticky_messages[channel_id]
    sticky_data['active'] = True
    
    # Post the sticky message
    sticky_embed = discord.Embed(
        title="📌 Sticky Message",
        description=sticky_data['message'],
        color=discord.Color.gold()
    )
    sticky_embed.set_footer(text="This message is pinned to this channel")
    
    sticky_msg = await interaction.channel.send(embed=sticky_embed)
    sticky_data['last_message_id'] = sticky_msg.id
    
    embed = discord.Embed(
        title="▶️ Sticky Message Restarted",
        description="The sticky message has been reactivated.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="stickremove", description="Stops and completely deletes the stickied message in this channel")
async def stick_remove(interaction: discord.Interaction):
    """Remove the sticky message from the channel"""
    if not interaction.user.guild_permissions.manage_messages:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need the 'Manage Messages' permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    channel_id = interaction.channel.id
    
    if channel_id not in sticky_messages:
        embed = discord.Embed(
            title="❌ No Sticky Message",
            description="There is no sticky message in this channel.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Delete the sticky message if it exists
    sticky_data = sticky_messages[channel_id]
    if sticky_data.get('last_message_id'):
        try:
            old_message = await interaction.channel.fetch_message(sticky_data['last_message_id'])
            await old_message.delete()
        except:
            pass
    
    # Remove from storage
    del sticky_messages[channel_id]
    
    embed = discord.Embed(
        title="🗑️ Sticky Message Removed",
        description="The sticky message has been completely removed from this channel.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="getstickies", description="Show all active and stopped stickies in your server")
async def get_stickies(interaction: discord.Interaction):
    """Show all sticky messages in the server"""
    if not interaction.user.guild_permissions.manage_messages:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need the 'Manage Messages' permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    guild = interaction.guild
    server_stickies = []
    
    for channel_id, sticky_data in sticky_messages.items():
        channel = guild.get_channel(channel_id)
        if channel:
            status = "🟢 Active" if sticky_data['active'] else "🔴 Stopped"
            message_preview = sticky_data['message'][:50] + "..." if len(sticky_data['message']) > 50 else sticky_data['message']
            server_stickies.append(f"**{channel.mention}** - {status}\n`{message_preview}`")
    
    if not server_stickies:
        embed = discord.Embed(
            title="📌 Server Sticky Messages",
            description="No sticky messages found in this server.",
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title="📌 Server Sticky Messages",
            description="\n\n".join(server_stickies),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Total: {len(server_stickies)} sticky message(s)")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Welcome event handler
@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    welcome_config = welcome_data.get(guild_id)

    if not welcome_config or not welcome_config.get('enabled', True):
        return

    channel = member.guild.get_channel(welcome_config['channel_id'])
    if not channel:
        return

    message = welcome_config['message']
    formatted_message = message.replace('{user}', member.mention)
    formatted_message = formatted_message.replace('{username}', member.display_name)
    formatted_message = formatted_message.replace('{server}', member.guild.name)
    formatted_message = formatted_message.replace('{membercount}', str(member.guild.member_count))

    try:
        embed = discord.Embed(description=formatted_message, color=0x00ff00)
        embed.set_author(name=f"Welcome to {member.guild.name}!", icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.timestamp = datetime.now()

        await channel.send(embed=embed)
    except:
        # Fallback to plain text if embed fails
        await channel.send(formatted_message)

bot.run('bot tokken')
