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

bot = commands.Bot(command_prefix="#")
base = declarative_base()
engine = create_engine('sqlite:///hashbrown.db?check_same_thread=False')

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

class FakeUser():
    id = 0
    name = "*Unknown User*"

    def __init__(self, id):
        self.id = id

"""===Commands==="""

@bot.command()
async def hash(ctx):
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("This command must be done in a DM to prevent other people from linking your hash to you.")
        return
    for guild_id in config['server_ids']:
        guild = bot.get_guild(guild_id)
        if guild is None:
            await ctx.send("The guild ID is incorrectly configurated and we cannot generate a hash. Please contact a administrator.")
            return
        if guild.get_member(ctx.author.id) is None:
            await ctx.send("You are not in a approved guild to generate a hash!")
            return
    session = Session()
    user_checks = session.query(UserCheck).all()
    user_ids = (check.user_id for check in user_checks)
    if ctx.author.id in user_ids:
        await ctx.send("You have already generated a hash. If you misplaced your hash, please contact a mod. Keep in mind that we are unable to retrieve your hash.")
        return
    hash_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    hash_obj = Hash(hash=hash_str)
    session.add(hash_obj)
    await ctx.send("Your hash is **`{}`**. Keep this secret, and copy it to your survey. This message will be deleted in 60 \
    seconds to prevent your hash from being traced back to you, and you won't be able to request it again, so please save your hash now."
                   .format(hash_str),delete_after=60)
    user_check = UserCheck(user_id=ctx.author.id)
    user_check.time_hashed = datetime.datetime.utcnow()
    session.add(user_check)
    session.commit()

@bot.command()
async def listhashes(ctx, page: int = 1):
    session = Session()
    hashes = session.query(Hash).order_by(Hash.hash).limit(15).offset((page-1)*15).all()
    hashes_list = (hash.hash for hash in hashes)
    hashes_str = '\n'.join(hashes_list)
    length = session.query(Hash).count()
    pages = round((length/15)+.5)
    await ctx.send("All current valid hashes (Page {}/{}):\n{}".format(page,pages,hashes_str))

@bot.command()
async def listusers(ctx, page: int = 1):
    session = Session()
    users = session.query(UserCheck).order_by(UserCheck.user_id).limit(15).offset((page-1)*15).all()
    users_obj = [bot.get_user(user.user_id) or FakeUser(user.user_id) for user in users]
    users_str = ""
    for user in users_obj:
        if user is None:
            continue
        users_str += "{0.name} (`{0.id}`)\n".format(user)
    length = session.query(UserCheck).count()
    pages = round((length/15)+.5)
    await ctx.send("The following users have generated a hash (Page {}/{}):\n{}".format(page,pages,users_str))

@bot.command()
async def update(ctx):
    """Pulls code from GitHub and restarts."""
    res = os.popen("git pull origin master").read()
    if res.startswith('Already up-to-date.'):
        await ctx.send('```\n' + res + '```')
    else:
        await ctx.send('```\n' + res + '```')
        await ctx.bot.get_command('restart').callback(ctx)

@bot.command()
async def restart(ctx):
    if ctx.author.permissions_in(ctx.channel).manage_messages:
        await ctx.send("Restarting Bot...")
        os.execl(sys.executable, sys.executable, *sys.argv)

"""===Config File Handling==="""

if os.path.isfile("config.json"):
    with open("config.json", "r") as f:
        config = json.load(f)
else:
    with open("config.json", "w") as f:
        config = {"discord_key": "YOUR_KEY_HERE",
                  "server_ids": [],
                  "prefix": "#"
                  }
        f.write(json.dumps(config, indent=3))

if config["discord_key"] == "YOUR_KEY_HERE":
    sys.exit("Please specify a discord token!")
bot.run(config["discord_key"], command_prefix=config["prefix"])

