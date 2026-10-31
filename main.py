import os
import discord
from discord.ext import commands

# Token with fallback included directly
BOT_TOKEN = os.getenv("BOT_TOKEN", "MTU2NTk5MDg4NTI3ODM1OTYzMg.GWmdvZ.paFwz74LYIeUyS3n1CI_ZkEIGmlKF26hgpGPJY")
MAX_SLOTS = 20
ROLE_NAME = "Confirmed Team"  # Role assigned to confirmed slot managers

EMOJI_CONFIRMED = "✅"
EMOJI_WAITLIST = "⏳"
EMOJI_REJECTED = "❌"

# Custom slot emojis for the embed view
NUMBER_EMOJIS = {
    1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣",
    6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟",
    11: "1️⃣1️⃣", 12: "1️⃣2️⃣", 13: "1️⃣3️⃣", 14: "1️⃣4️⃣", 15: "1️⃣5️⃣",
    16: "1️⃣6️⃣", 17: "1️⃣7️⃣", 18: "1️⃣8️⃣", 19: "1️⃣9️⃣", 20: "2️⃣0️⃣"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="%", intents=intents)

registered_teams = []
waitlist_teams = []

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Handle Registration Command
    if message.content.startswith("%register"):
        lines = [line.strip() for line in message.content.split("\n") if line.strip()]
        
        # Extract Team Name
        if len(lines) >= 2:
            team_name = lines[1]
        else:
            team_name = message.content.replace("%register", "").strip()

        if not team_name:
            await message.add_reaction(EMOJI_REJECTED)
            await message.channel.send(f"{EMOJI_REJECTED} **Registration failed:** Please provide a team name.")
            return

        # Extract Manager Tag/Mentions
        mentions = [user.mention for user in message.mentions]
        manager_tag = ", ".join(mentions) if mentions else message.author.mention

        entry = {
            "team_name": team_name,
            "manager": manager_tag,
            "author_id": message.author.id
        }

        # Check for slots vs waitlist
        if len(registered_teams) < MAX_SLOTS:
            registered_teams.append(entry)
            slot_no = len(registered_teams)
            await message.add_reaction(EMOJI_CONFIRMED)
            await message.channel.send(
                f"{EMOJI_CONFIRMED} **Slot #{slot_no} Confirmed!**\n"
                f"• **Team:** {team_name}\n"
                f"• **Manager:** {manager_tag}"
            )

            # Assign Confirmed Team Role automatically
            role = discord.utils.get(message.guild.roles, name=ROLE_NAME)
            if role:
                try:
                    await message.author.add_roles(role)
                except discord.Forbidden:
                    print("⚠️ Bot lacks permissions to assign roles. Ensure bot role is positioned higher.")
        else:
            waitlist_teams.append(entry)
            wait_no = len(waitlist_teams)
            await message.add_reaction(EMOJI_WAITLIST)
            await message.channel.send(
                f"{EMOJI_WAITLIST} **Main slots full! Added to Waitlist #{wait_no}**\n"
                f"• **Team:** {team_name}\n"
                f"• **Manager:** {manager_tag}"
            )

    await bot.process_commands(message)

# Command to display formatted Embed Teamlist
@bot.command(name="teamlist")
async def teamlist(ctx):
    title = f"⚔️ Slot List ({len(registered_teams)}/{MAX_SLOTS})"
    
    embed = discord.Embed(
        title=title,
        color=discord.Color.dark_gray()
    )
    
    description_lines = []
    
    for i in range(MAX_SLOTS):
        slot_num = i + 1
        emoji = NUMBER_EMOJIS.get(slot_num, f"{slot_num}.")
        
        if i < len(registered_teams):
            team = registered_teams[i]
            description_lines.append(f"{emoji} **{team['team_name']}** {team['manager']}")
        else:
            description_lines.append(f"{emoji} | EMPTY")
            
    embed.description = "\n".join(description_lines)
    
    embed.add_field(
        name="Confirmation", 
        value="✔️ Confirmation open until registration closes.", 
        inline=False
    )
    
    await ctx.send(embed=embed)

# Admin Command: Unregister a team
@bot.command(name="unregister")
@commands.has_permissions(administrator=True)
async def unregister(ctx, *, team_name: str):
    global registered_teams, waitlist_teams
    
    removed = False
    for team in registered_teams:
        if team["team_name"].lower() == team_name.lower():
            registered_teams.remove(team)
            removed = True
            await ctx.send(f"❌ Removed **{team['team_name']}** from confirmed slots.")
            
            # Remove Confirmed Team role from user
            member = ctx.guild.get_member(team["author_id"])
            role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)
            if member and role:
                try:
                    await member.remove_roles(role)
                except discord.Forbidden:
                    pass
            break

    if removed and waitlist_teams:
        promoted_team = waitlist_teams.pop(0)
        registered_teams.append(promoted_team)
        await ctx.send(
            f"🎉 **{promoted_team['team_name']}** ({promoted_team['manager']}) has been promoted from the waitlist to Slot #{len(registered_teams)}!"
        )
        
        # Give role to promoted manager
        promoted_member = ctx.guild.get_member(promoted_team["author_id"])
        role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)
        if promoted_member and role:
            try:
                await promoted_member.add_roles(role)
            except discord.Forbidden:
                pass

# Admin Command: Clear all slots
@bot.command(name="clearlist")
@commands.has_permissions(administrator=True)
async def clearlist(ctx):
    global registered_teams, waitlist_teams
    registered_teams.clear()
    waitlist_teams.clear()
    await ctx.send("🧹 All slots and waitlists have been cleared!")

bot.run(BOT_TOKEN)
