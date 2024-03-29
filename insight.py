import discord
from discord import TextChannel, Embed, Colour
import os
import logging

TOKEN = os.environ.get('BOT_TOKEN')

COMMAND = '!digest'
CHECK_EMOJI = str('✅')
CLOCK_EMOJI = str('🕑')
ERROR_EMOJI = str('⁉️')

ERROR_EMBED = Embed(
    description="Oops! Looks like something went wrong. Try again later.",
    colour=Colour.red()
)

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='insight.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())

client = discord.Client()

class Digest:
    DEFAULT_LIMIT = 500

    def __init__(self, channel: TextChannel, limit: int=0):
        self._limit = limit if limit > 0 else self.DEFAULT_LIMIT
        
        self.channel = channel
        self.file_formats = {}
        self.user_count = 0
        self.file_count = 0

    def _reset(self):
        self.file_formats = {}
        self.user_count = 0
        self.file_count = 0

    async def collect(self):
        """
        Collects digest for the channel (for the `self.limit` most recent messages). 
        """
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
        """
        Returns the contents of the digest formatted as an Embed.
        """
        files_text = f"In the last {self._limit} messages, {self.file_count} files have been sent by {self.user_count} user{'' if self.user_count == 1 else 's'}."
        
        if self.file_count > 0:
            format_list = "\n".join([f"• {count} **{file_format}** file{'' if count == 1 else 's'}" for file_format, count in self.file_formats.items()])
            files_text += "\n\n" + format_list

        return Embed(
            title="Digest",
            colour=Colour.blue(),
            description=f"Here's a digest for the channel <#{self.channel.id}>.",
        ).add_field(
            name="Files",
            value=files_text
        )

async def set_reaction(message, emoji):
    """
    Sets the bot reaction for the given message, removing all other reactions by the bot.
    """
    for reaction in message.reactions:
        if reaction.me:
            await message.remove_reaction(reaction, client.user)
    await message.add_reaction(emoji)
    logger.info(f'Set reaction for message {message.id} to {emoji}')
    
@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')


@client.event
async def on_message(message):
    try:
        channel = message.channel
        values = message.content.split(r"\s")

        if message.author == client.user or values[0] != COMMAND:
            return

        logger.info(f"Retrieving digest for {message.guild.name}/#{channel.name}")
        
        await set_reaction(message, CLOCK_EMOJI)
        digest = Digest(channel)
        await digest.collect()

        logger.info(f"Sending digest for {message.guild.name}/#{channel.name}")
        await channel.send(embed=digest.format()) 
        await set_reaction(message, CHECK_EMOJI)
        
        logger.info(f"Digest successfully sent for {message.guild.name}/#{channel.name}")
    except Exception as e:
        logger.error(f"Error occured when processing digest for {message.guild.name}/#{channel.name}: {e}")
        await set_reaction(message, ERROR_EMOJI)
        await channel.send(embed=ERROR_EMBED) 


client.run(TOKEN)