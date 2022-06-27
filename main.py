from os import getenv

import discord
from dotenv import load_dotenv

import jsonfile

load_dotenv()
intents = discord.Intents.default()
intents.members = True
bot = discord.Bot(intents=intents)
datastore = jsonfile.jsonfile("datastore.json")
if datastore.data == Ellipsis:
    datastore.data = {"version": "1.0.0", "guilds": {}}
config = datastore.data
list_emoji = discord.PartialEmoji(name="📖")


@bot.slash_command(guild_ids=[840699664239558736])
@discord.default_permissions(administrator=True)
@discord.guild_only()
async def set_list(ctx, list_channel: discord.TextChannel = None):
    list_channel = list_channel or ctx.channel
    guild_id = str(ctx.guild.id)
    if guild_id in config["guilds"]:
        config["guilds"][guild_id]["list_channel"] = list_channel.id
    else:
        config["guilds"][guild_id] = {
            "list_channel": list_channel.id,
            "list_role": None,
            "reaction_message": None,
            "list": [],
        }
    await ctx.respond(f"Successfully set list channel to {list_channel.mention}!")


@bot.slash_command(guild_ids=[840699664239558736])
@discord.default_permissions(administrator=True)
@discord.guild_only()
async def set_list_role(ctx, list_role: discord.Role):
    guild_id = str(ctx.guild.id)
    if guild_id in config["guilds"]:
        config["guilds"][guild_id]["list_role"] = list_role.id
    else:
        config["guilds"][guild_id] = {
            "list_channel": None,
            "list_role": list_role.id,
            "reaction_message": None,
            "list": [],
        }
    await ctx.respond(f"Successfully set list role to {list_role.mention}!")


@bot.slash_command(guild_ids=[840699664239558736])
@discord.default_permissions(administrator=True)
@discord.guild_only()
async def set_reaction_message(ctx, reaction_message_id):
    guild_id = str(ctx.guild.id)
    reaction_message_id = int(reaction_message_id)
    channels = [c for c in ctx.guild.channels if type(c) == discord.TextChannel]
    for channel in channels:
        reaction_message = await channel.fetch_message(reaction_message_id)
        if reaction_message:
            break
    if not reaction_message:
        await ctx.respond("Cannot find message!")
    if guild_id in config["guilds"]:
        config["guilds"][guild_id]["reaction_message"] = reaction_message_id
    else:
        config["guilds"][guild_id] = {
            "list_channel": None,
            "list_role": None,
            "reaction_message": reaction_message_id,
            "list": [],
        }
    await reaction_message.add_reaction(list_emoji)
    await ctx.respond("Successfully set reaction message!")


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.member.bot:
        return
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    guild_id = str(payload.guild_id)
    if guild_id not in config["guilds"]:
        return
    if (
        not config["guilds"][guild_id]["list_channel"]
        or not config["guilds"][guild_id]["list_role"]
        or not config["guilds"][guild_id]["reaction_message"]
    ):
        return
    if payload.emoji != list_emoji:
        return
    if payload.message_id != config["guilds"][guild_id]["reaction_message"]:
        return
    role = guild.get_role(config["guilds"][guild_id]["list_role"])
    if role is None:
        return
    try:
        if (
            guild.get_role(config["guilds"][guild_id]["list_role"])
            in payload.member.roles
        ):
            return
        config["guilds"][guild_id]["list"].append(payload.member.id)
        n = config["guilds"][guild_id]["list"].index(payload.member.id)
        await payload.member.add_roles(role)
        await guild.get_channel(config["guilds"][guild_id]["list_channel"]).send(
            f"{n}. {payload.member.mention}"
        )
        await payload.member.send(f"You are now on the list at number {n}!")
    except discord.HTTPException:
        pass


@bot.event
async def on_ready():
    print(bot.user.name + "#" + bot.user.discriminator + " is ready!")


bot.run(getenv("TOKEN"))
