import discord
from discord import app_commands
import os
import webServer
import asyncio
import datetime
import pytz
import json

token = os.environ["discordkey"]

# Role promotion tiers
ROLE_TIERS = [
    ("Scout", 0),
    ("Archer", 10),
    ("Mage", 20),
    ("Knight", 30),
    ("General", 40)
]

POINTS_FILE = "user_points.json"

def load_points():
    if os.path.exists(POINTS_FILE):
        with open(POINTS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_points(data):
    with open(POINTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Client(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.loop.create_task(self.send_daily_message()) # send everyday
        self.loop.create_task(self.check_scheduled_messages())


    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.lower() == "meow":
            await message.channel.send("🐱 Meow!")

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced.")


#Daily Message  
    async def send_daily_message(self):
        await self.wait_until_ready()
        channel = self.get_channel(announcements)
        
        last_sent_date = None  # Track date instead of boolean

        while not self.is_closed():
            now = datetime.datetime.now(pytz.timezone('US/Eastern'))
            today_str = now.strftime("%Y-%m-%d")

            if now.hour == 9 and now.minute == 00 and last_sent_date != today_str:
                if channel:
                    await channel.send("☀️ @everyone Good meowrning everyone! 🐾")
                    last_sent_date = today_str

            await asyncio.sleep(30)


# Check schedule
    async def check_scheduled_messages(self):
        await self.wait_until_ready()
        while not self.is_closed():
            now = datetime.datetime.now(pytz.timezone('US/Eastern'))
            for msg in scheduled_messages[:]:
                send_time, channel_id, text = msg
                if now >= send_time:
                    channel = self.get_channel(channel_id)
                    if channel:
                        await channel.send(text)
                    scheduled_messages.remove(msg)
            await asyncio.sleep(30)



#member has joined
    async def on_member_join(self, member):
        # when someone joins, send them the summon message
        channel = self.get_channel(welcomeMessage)
        if channel:
            await channel.send(
                f"🔔 **{member.name}** has been summoned as a soldier to the Shadow Legion Clan! @everyone ⚔️"
            )

#CHANNEL IDS
announcements = 1374917836278857769
welcomeMessage = 1375182087476215838

# Scheduled message storage
scheduled_messages = []  # list of tuples: (send_time, channel_id, message_text)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = Client(intents=intents)


# SLASH COMMAND: /schedule
@client.tree.command(name="schedule", description="Schedule a message for later.")
@app_commands.describe(
    date="Date in YYYY-MM-DD format",
    time="Time in HH:MM (24-hour) format",
    message="Message to send"
)
async def schedule(interaction: discord.Interaction, date: str, time: str, message: str):
    try:
        eastern = pytz.timezone('US/Eastern')
        scheduled_time = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        scheduled_time = eastern.localize(scheduled_time)

        scheduled_messages.append((scheduled_time, interaction.channel_id, message))

        await interaction.response.send_message(
            f"✅ Scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M %Z')}",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

@client.tree.command(name="cancel_schedule", description="Cancel your most recent scheduled message.")
async def cancel_schedule(interaction: discord.Interaction):
    # Filter all messages created by the user
    user_messages = [msg for msg in scheduled_messages if msg["user_id"] == interaction.user.id]

    if not user_messages:
        await interaction.response.send_message("⚠️ You have no scheduled messages to cancel.", ephemeral=True)
        return

    # Find the one with the latest `send_time`
    latest_msg = max(user_messages, key=lambda msg: msg["send_time"])
    scheduled_messages.remove(latest_msg)

    await interaction.response.send_message("🗑️ Your most recent scheduled message was cancelled.", ephemeral=True)

@client.tree.command(name="speak", description="Make Meow Bot say something.")
@app_commands.describe(message="What Meow Bot should say")
async def speak(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.send(message)
    await interaction.followup.send("✅ Message sent!", ephemeral=True)

    

@client.tree.command(name="award", description="Award a user with points for challenges.")
@app_commands.describe(user="User to award", points="Number of points to award")
async def award(interaction: discord.Interaction, user: discord.Member, points: int):
    data = load_points()
    user_id = str(user.id)

    if user_id not in data:
        data[user_id] = {"points": 0, "current_role": None}

    # If user is already maxed at General, block further points
    if data[user_id]["points"] >= 50:
        await interaction.response.send_message(f"🎖️ {user.display_name} is already a General! No more points awarded.", ephemeral=True)
        return

    data[user_id]["points"] += points
    if data[user_id]["points"] > 50:
        data[user_id]["points"] = 50  # Cap at 50

    new_role_name = None
    for role_name, required_points in ROLE_TIERS:
        if data[user_id]["points"] >= required_points:
            new_role_name = role_name

    current_role_name = data[user_id].get("current_role")
    if new_role_name and new_role_name != current_role_name:
        # Update role
        guild = interaction.guild
        new_role = discord.utils.get(guild.roles, name=new_role_name)
        if new_role:
            # Remove previous rank roles
            for role_name, _ in ROLE_TIERS:
                role = discord.utils.get(guild.roles, name=role_name)
                if role in user.roles:
                    await user.remove_roles(role)

            await user.add_roles(new_role)
            data[user_id]["current_role"] = new_role_name
            await interaction.channel.send(f"🥳 {user.mention} has ranked up to **{new_role_name}**!")

    save_points(data)
    await interaction.response.send_message(f"✅ {user.display_name} now has {data[user_id]['points']} points.", ephemeral=True)




webServer.keep_alive()

client.run(token)
