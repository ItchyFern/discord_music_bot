import discord
from discord.ext import commands
from urllib.request import urlopen
from requests import get
import os
from dotenv import load_dotenv
import music

# more commented out stuff

prefix="!"
bot = commands.Bot(command_prefix=prefix, intents=discord.Intents.all(), activity=discord.Activity(type=discord.ActivityType.watching, name=f"for {prefix}help"))
client = discord.Client()

# Music commands
cogs = [music]

for i in range(len(cogs)):
  cogs[i].setup(bot)

# PROOF OF RUNNING SCRIPT
@bot.event
# Print when the program is ready for input
async def on_ready():
  print("We have logged in as {0.user}".format(bot))

load_dotenv()
bot.run(os.environ['DISCORD_TOKEN'])
