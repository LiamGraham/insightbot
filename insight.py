import discord
from discord import TextChannel, Embed, Colour
import os

from discord import file

TOKEN = os.environ.get('BOT_TOKEN')

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
            if message.embeds:
                print(message.embeds[0].to_dict())
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
            {self.file_count} files have been sent by {self.user_count} user{'' if self.user_count == 1 else 's'}.

            {format_list}
            """
        )

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!digest'):
        channel = message.channel
        
        digest = Digest(channel)
        await digest.collect()
        await message.channel.send(embed=digest.format()) 

client.run(TOKEN)