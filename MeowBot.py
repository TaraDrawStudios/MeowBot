import discord
from discord import app_commands
import os
import asyncio
import datetime
import pytz


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

        while not self.is_closed():
            now = datetime.datetime.now(pytz.timezone('US/Eastern'))

            # Send at exactly 9:00 AM Eastern Time
            if now.hour == 9 and now.minute == 0:
                if channel:
                    await channel.send("☀️ @everyone Good meowrning everyone! 🐾")
                await asyncio.sleep(60)  # Avoid sending multiple times that minute

            await asyncio.sleep(30)  # Check twice a minute

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



client.run(os.getenv("TOKEN"))
