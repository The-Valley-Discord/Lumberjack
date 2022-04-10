from typing import Optional

import discord
from discord.ext import tasks

from lumberjack import Lumberjack
from lumberjack.helpers.models import LJMessage


class Cleanup(Lumberjack.Cog):
    def __init__(self, *args):
        self.cleanup_old_log_messages.start()
        super().__init__(*args)

    @tasks.loop(minutes=1)
    async def cleanup_old_log_messages(self):
        self.db.delete_old_db_messages()
        db_message: LJMessage = self.db.get_oldest_lumberjack_message()
        if not db_message:
            return
        channel: discord.TextChannel = self.bot.get_channel(db_message.channel_id)
        if channel:
            message: Optional[discord.Message] = None
            try:
                message = await channel.fetch_message(db_message.message_id)
            except discord.Forbidden or discord.NotFound:
                pass
            if message:
                try:
                    await message.delete()
                except discord.Forbidden or discord.NotFound:
                    pass
        self.db.delete_lumberjack_messages_from_db(db_message.message_id)


async def setup(bot):
    await bot.add_cog(Cleanup(bot))
