import logging

import aiohttp
from discord.ext import commands
from lumberjack.helpers.database import Database


class Lumberjack(commands.Bot):
    def __init__(self, command_prefix, database, **kwargs):
        super().__init__(command_prefix=command_prefix, **kwargs)
        self.logs = logging.getLogger("Lumberjack")
        self.initial_extensions = [
            "lumberjack.cogs.cleanup",
            "lumberjack.cogs.logger",
            "lumberjack.cogs.member_log",
            "lumberjack.cogs.tracker",
        ]
        self.session = None
        self.db: Database = database

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        for ext in self.initial_extensions:
            await self.load_extension(ext)

    async def close(self):
        await super().close()
        await self.session.close()

    class Cog(commands.Cog):
        """
        A cog with a logger attached to it.
        """

        def __init__(self, bot):
            self.bot: Lumberjack = bot
            self.logs = bot.logs.getChild(self.__class__.__name__)

        @property
        def db(self) -> Database:
            return self.bot.db
