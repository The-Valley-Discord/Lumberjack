import logging

import discord
from discord.ext import commands, tasks

from Helpers.database import Database
from Helpers.models import LJMessage


class Cleanup(commands.Cog):
    def __init__(self, bot: discord.Client, logs: logging, db: Database):
        self.bot: discord.Client = bot
        self.logs: logging = logs
        self.db: Database = db
        self.cleanup_old_log_messages.start()

    @tasks.loop(seconds=0.5)
    async def cleanup_old_log_messages(self):
        self.db.delete_old_db_messages()
        db_message: LJMessage = self.db.get_oldest_lumberjack_message()
        if not db_message:
            return
        channel: discord.TextChannel = self.bot.get_channel(db_message.channel_id)
        if channel:
            message: discord.Message = await channel.fetch_message(
                db_message.message_id
            )
            if message:
                try:
                    await message.delete()
                except discord.Forbidden or discord.NotFound:
                    pass
        self.db.delete_lumberjack_messages_from_db(db_message.message_id)
