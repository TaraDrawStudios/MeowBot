import discord

import asyncio
import datetime
import pytz

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.loop.create_task(self.send_daily_message()) # send everyday

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.lower() == "meow":
            await message.channel.send("🐱 Meow!")

##date and time
    async def send_daily_message(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)

        while not self.is_closed():
            now = datetime.datetime.now(pytz.timezone('US/Eastern'))

            # Send at exactly 9:00 AM Eastern Time
            if now.hour == 9 and now.minute == 0:
                if channel:
                    await channel.send("☀️ @everyone Good meowrning everyone! 🐾")
                await asyncio.sleep(60)  # Avoid sending multiple times that minute

            await asyncio.sleep(30)  # Check twice a minute

CHANNEL_ID = 1374917836278857769

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run('MTM3NTEzMjUzNzM0NDQ5NTgyMA.G51Rhi.51uFzBfy5rm3YA9voVdGNJuoxL2vahSfEGH9RM')



