import discord
from discord.ext import commands
import sys
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime

bot = commands.Bot(command_prefix="%")
base = declarative_base()
engine = create_engine('sqlite:///hashbrown.db')
session = sessionmaker(bind=engine)

@bot.event
async def on_ready():
    print("Logged in as {} ({})".format(bot.user.name,bot.user.id))

"""===Commands==="""

@bot.command
async def hash(ctx):
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("This command must be done in a DM to preserve the security of your hash.")
        return
    

"""===Config File Handling==="""

if os.path.isfile("config.json"):
    with open("config.json", "r") as f:
        config = json.load(f)
else:
    with open("config.json", "w") as f:
        config = {"discord_key": "YOUR_KEY_HERE",
                  "developers": [],
                  "server_ids": [],
                  "prefix": "%"
                  }
        f.write(json.dumps(config))

if config["discord_key"] == "YOUR_KEY_HERE":
    sys.exit("Please specify a discord token!")
bot.run(config["discord_key"], command_prefix=config["prefix"])

"""Database Definitions"""
class UserCheck(base):
    __tablename__ = "user_checks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    time_hashed = Column(DateTime)

class Hash(base):
    __tablename__ = "hashes"
    hash = Column(String, primary_key=True)
