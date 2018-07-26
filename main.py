import discord
from discord.ext import commands
import sys
import json
import os
import random
import string
import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime

bot = commands.Bot(command_prefix="%")
base = declarative_base()
engine = create_engine('sqlite:///hashbrown.db')

Session = sessionmaker(bind=engine)

@bot.event
async def on_ready():
    print("Logged in as {} ({})".format(bot.user.name,bot.user.id))

"""Database Definitions"""
class UserCheck(base):
    __tablename__ = "user_checks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    time_hashed = Column(DateTime)

class Hash(base):
    __tablename__ = "hashes"
    hash = Column(String, primary_key=True)

base.metadata.create_all(engine)

"""===Commands==="""

@bot.command()
async def hash(ctx):
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("This command must be done in a DM to preserve the security of your hash.")
        return
    for guild_id in config['server_ids']:
        guild = bot.get_guild(guild_id)
        if guild.get_member(ctx.author.id) is None:
            await ctx.send("You are not in a approved guild to generate a hash!")
            return
    session = Session()
    user_checks = session.query(UserCheck).all()
    user_ids = (check.user_id for check in user_checks)
    if ctx.author.id in user_ids:
        await ctx.send("You have already generated a hash. If you misplaced your hash, please contact @bkeeneykid#9671. Keep in mind that your hash cannot be traced back to you.")
        return
    hash_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    hash_obj = Hash(hash=hash_str)
    session.add(hash_obj)
    await ctx.send("Your hash is `{}`. Keep this secret, and copy it to your survey. This message will be deleted in 60 seconds so that we cannot track your hash, so please save your hash now. ".format(hash_str),
                   delete_after=60)
    user_check = UserCheck(user_id=ctx.author.id)
    user_check.time_hashed = datetime.datetime.utcnow()
    session.add(user_check)
    session.commit()

@bot.command()
async def listhashes(ctx):
    session = Session()
    hashes = session.query(Hash).all()
    hashes_list = (hash.hash for hash in hashes)
    hashes_str = '\n'.join(hashes_list)
    await ctx.send("All current valid hashes:\n{}".format(hashes_str))

@bot.command()
async def listusers(ctx):
    session = Session()
    users = session.query(UserCheck).all()
    users_obj = [bot.get_user(user.user_id) for user in users]
    print(users_obj)
    users_str = ""
    for user in users_obj:
        users_str += "{0.name} (`{0.id}`)\n".format(user)
    await ctx.send("The following users have generated a hash:\n{}".format(users_str))

"""===Config File Handling==="""

if os.path.isfile("config.json"):
    with open("config.json", "r") as f:
        config = json.load(f)
else:
    with open("config.json", "w") as f:
        config = {"discord_key": "YOUR_KEY_HERE",
                  "server_ids": [],
                  "prefix": "%"
                  }
        f.write(json.dumps(config, indent=3))

if config["discord_key"] == "YOUR_KEY_HERE":
    sys.exit("Please specify a discord token!")
bot.run(config["discord_key"], command_prefix=config["prefix"])

