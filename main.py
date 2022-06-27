from os import getenv
from random import randint

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


class ListButton(discord.ui.Button):
    def __init__(self, role: discord.Role):
        super().__init__(
            label="List me!",
            style=discord.ButtonStyle.primary,
            custom_id=str(role.id),
        )

    async def callback(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        user = interaction.user
        role = interaction.guild.get_role(int(self.custom_id))

        if role is None:
            return

        if role not in user.roles:
            list_id = "1"
            if config["guilds"][guild_id]["dual_list"]:
                list_id = str(randint(1, 2))
            config["guilds"][guild_id]["list"][list_id].append(user.id)
            n = config["guilds"][guild_id]["list"][list_id].index(user.id)
            await user.add_roles(role)
            list_channel = interaction.guild.get_channel(
                config["guilds"][guild_id]["list_channel"]
            )
            if not list_channel:
                await interaction.response.send_message(
                    "❌ ERROR! Please try again later.",
                    ephemeral=True,
                )
                return
            await list_channel.send(f"{list_id}:**{n+1}**. {user.mention}")
            await interaction.response.send_message(
                f"🎉 You have been listed at number {list_id}:**{n+1}**!",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "❌ You cannot get listed twice!",
                ephemeral=True,
            )


@bot.slash_command()
@discord.default_permissions(administrator=True)
@discord.guild_only()
async def set_list(ctx, list_channel: discord.TextChannel = None):
    """
    Sets the channel where everyones posistions will be sent.
    """
    list_channel = list_channel or ctx.channel
    guild_id = str(ctx.guild.id)
    if guild_id in config["guilds"]:
        config["guilds"][guild_id]["list_channel"] = list_channel.id
    else:
        config["guilds"][guild_id] = {
            "list_channel": list_channel.id,
            "list_role": None,
            "dual_list": False,
            "list": {"1": [], "2": []},
        }
    await ctx.respond(f"Successfully set list channel to {list_channel.mention}!")


@bot.slash_command()
@discord.default_permissions(administrator=True)
@discord.guild_only()
async def set_list_role(ctx, list_role: discord.Role):
    """
    Select the role you want to give to everyone who joins the list.
    """
    guild_id = str(ctx.guild.id)
    if guild_id in config["guilds"]:
        config["guilds"][guild_id]["list_role"] = list_role.id
    else:
        config["guilds"][guild_id] = {
            "list_channel": None,
            "list_role": list_role.id,
            "dual_list": False,
            "list": {"1": [], "2": []},
        }
    await ctx.respond(f"Successfully set list role to {list_role.mention}!")


@bot.slash_command()
@discord.default_permissions(administrator=True)
@discord.guild_only()
async def set_dual_list(ctx, enabled: bool):
    """
    By setting this option to True the list numbers are split in 2 versions this helps divide workflow.
    """
    guild_id = str(ctx.guild.id)
    if guild_id in config["guilds"]:
        config["guilds"][guild_id]["dual_list"] = enabled
    else:
        config["guilds"][guild_id] = {
            "list_channel": None,
            "list_role": None,
            "dual_list": enabled,
            "list": {"1": [], "2": []},
        }
    await ctx.respond(f"Successfully {'enabled' if enabled else 'disabled'} dual list!")


@bot.slash_command()
@discord.default_permissions(administrator=True)
@discord.guild_only()
async def post_menu(ctx: discord.ApplicationContext):
    guild_id = str(ctx.guild.id)
    view = discord.ui.View(timeout=None)
    view.add_item(
        ListButton(ctx.guild.get_role(config["guilds"][guild_id]["list_role"]))
    )
    await ctx.delete()
    await ctx.send(
        "Click the button to add yourself to the list.\nThe number in **bold** is your place in the queue the other number is which queue you are in.",
        view=view,
    )


@bot.event
async def on_ready():
    guilds = [int(guild_id) for guild_id in config["guilds"].keys()]
    for guild in guilds:
        view = discord.ui.View(timeout=None)
        guild = str(guild)
        if (
            not config["guilds"][guild]["list_channel"]
            or not config["guilds"][guild]["list_role"]
            or not config["guilds"][guild]["dual_list"]
        ):
            continue
        view.add_item(
            ListButton(
                bot.get_guild(int(guild)).get_role(config["guilds"][guild]["list_role"])
            )
        )
        bot.add_view(view)
    print(f"{bot.user.name}#{bot.user.discriminator} is ready!")


bot.run(getenv("TOKEN"))
