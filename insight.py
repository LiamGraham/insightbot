import discord
from discord import TextChannel, Embed, Colour
import os
import time

from discord import file
from discord.emoji import Emoji

TOKEN = os.environ.get('BOT_TOKEN')
CHECK_EMOJI = str('✅')
CLOCK_EMOJI = str('🕑')

client = discord.Client()

class Digest:
    HISTORY_LIMIT = 500

    def __init__(self, channel: TextChannel, limit: int=0):
        self._limit = limit if limit > 0 else self.HISTORY_LIMIT
        
        self.channel = channel
        self.file_formats = {}
        self.user_count = 0
        self.file_count = 0

    def _reset(self):
        self.file_formats = {}
        self.user_count = 0
        self.file_count = 0

    async def collect(self):
        self._reset()
        user_ids = set()
        async for message in self.channel.history(limit=self._limit):
            if not message.attachments:
                continue
            user_ids.add(message.author.id)
            attachment = message.attachments[0]
            format = os.path.splitext(attachment.filename)[1]
            self.file_formats[format] = self.file_formats.get(format, 0) + 1
            self.file_count += 1

        self.user_count = len(user_ids)

    def format(self) -> Embed:
        format_list = "\n".join([f"• {count} **{file_format}** file{'' if count == 1 else 's'}" for file_format, count in self.file_formats.items()])
        return Embed(
            title="Digest",
            colour=Colour.blue(),
            description=f"Here's a digest for the channel <#{self.channel.id}>.",
        ).add_field(
            name="Files",
            value=f"""
            In the last {self._limit} messages, {self.file_count} files have been sent by {self.user_count} user{'' if self.user_count == 1 else 's'}.

            {format_list}
            """
        )

async def add_loading_reaction(message):
    await message.add_reaction(CLOCK_EMOJI)

async def add_done_reaction(message):
    await message.remove_reaction(CLOCK_EMOJI, client.user)
    await message.add_reaction(CHECK_EMOJI)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!digest'):
        channel = message.channel
        await add_loading_reaction(message)
        print(f"Retrieving digest for #{channel.name} in '{message.guild.name}'")
        
        digest = Digest(channel)
        await digest.collect()
        await message.channel.send(embed=digest.format()) 
        await add_done_reaction(message)

client.run(TOKEN)