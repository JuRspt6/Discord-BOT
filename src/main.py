from discord.ext import commands, tasks
import discord
import random
from datetime import datetime, timedelta
import urllib.request
import os
from dotenv import load_dotenv
load_dotenv()

#################

from name import name

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(
    command_prefix="!",  # Change to desired prefix
    case_insensitive=True, # Commands aren't case-sensitive
    intents = intents # Set up basic permissions
)
flood_active = False
max_messages = 5  # The maximum number of messages allowed in Y minutes
time_period = 1  # Y minutes

user_message_counts = {}

bot.author_id = 361104744799797249  # Change to your discord id

@bot.event
async def on_ready():  # When the bot is ready
    print("I'm in")
    print(bot.user)  # Prints the bot's username and identifier

@bot.command(name='name')
async def name(ctx):
    user = ctx.author
    await ctx.send(f'Votre nom est {user.display_name}')


@bot.command(name='d6')
async def d6(ctx):
    await ctx.send(random.randint(1,6))

async def send_warning_message(ctx, user, message_count):
    await ctx.send(f"{user.mention}, tu as envoyé {message_count} messages dans un court laps de temps. Evite d'inonder le chat.")

@bot.event
async def on_message(message):
    if message.content == "Salut tout le monde":
        res = f"Salut tout seul {message.author.mention}"
        await message.channel.send(res)

    if flood_active:
        author = message.author

        # Check if the message author is a bot or the message was sent in a DM
        if author.bot or not message.guild:
            return

        # Get the current time
        current_time = datetime.now()

        # Update the user's message count
        if author.id not in user_message_counts:
            user_message_counts[author.id] = [(current_time, 1)]
        else:
            user_message_counts[author.id] = [(timestamp, count) for timestamp, count in user_message_counts[author.id] if
                                               current_time - timestamp < timedelta(minutes=time_period)] + [
                                                (current_time, user_message_counts[author.id][-1][1] + 1)]

        # Check if the user has exceeded the message limit
        if user_message_counts[author.id][-1][1] > max_messages:
            await send_warning_message(message.channel, author, user_message_counts[author.id][-1][1])

    await bot.process_commands(message)

@bot.command(name='admin')
async def admin(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Admin")
    if not role:
        await ctx.guild.create_role(name="Admin", permissions=discord.Permissions(8))
    await member.add_roles(role)

@bot.command(name='ban')
async def ban(ctx, member: discord.Member, reason=""):
    liste = ["Mangeur de carte graphique compulsif", "Insulte à la patrie", "A plus de flop qu'un supercomputer"]
    if reason == "":
        reason = random.choice(liste)
    await ctx.guild.ban(member, reason=reason)
    await ctx.send(f'{member} est ban pour cette raison : {reason}')

@bot.command(name='flood')
async def toggle_flood(ctx):
    global flood_active

    if flood_active:
        flood_active = False
        cleanup_message_counts.stop()
        for user_id in list(user_message_counts.keys()):
            del user_message_counts[user_id]
        await ctx.send("Flood prevention est maintenant désactivé.")
    else:
        flood_active = True
        cleanup_message_counts.start()
        await ctx.send("Flood prevention est maintenant activé.")

@tasks.loop(minutes=time_period)
async def cleanup_message_counts():
    for user_id in list(user_message_counts.keys()):
        if not user_message_counts[user_id] or datetime.now() - user_message_counts[user_id][-1][0] > timedelta(
                minutes=time_period):
            del user_message_counts[user_id]

@bot.command(name='xkcd')
async def get_random_xkcd(ctx):
    latest_comic_url = "https://xkcd.com/info.0.json"
    response = urllib.request.urlopen(latest_comic_url)
    data = response.read().decode("utf-8")

    import json
    latest_comic_data = json.loads(data)
    latest_comic_number = latest_comic_data['num']

    random_comic_number = random.randint(1, latest_comic_number)

    random_comic_url = f"https://xkcd.com/{random_comic_number}/info.0.json"
    response = urllib.request.urlopen(random_comic_url)
    data = response.read().decode("utf-8")

    comic_data = json.loads(data)
    image_url = comic_data['img']

    embed = discord.Embed(title=f"xkcd Comic #{random_comic_number}")
    embed.set_image(url=image_url)
    await ctx.send(embed=embed)

@bot.command(name='poll')
async def create_poll(ctx, *, question=""):
    mention = "@here"

    if question == "":
        await ctx.send("Frérot il manque la question 🙃")
        return
    poll_message = await ctx.send(f'{mention} \n**{question}**')

    await poll_message.add_reaction('👍')  # Thumbs-up
    await poll_message.add_reaction('👎')  # Thumbs-down

token = os.environ.get('TOKEN')
bot.run(token)  # Starts the bot