import logging
import unittest
from unittest.mock import Mock

import aiounittest
import discord
from discord.ext import commands
from mock import AsyncMock

from lumberjack.cogs.logger import Logger
from lumberjack.helpers.database import Database

if __name__ == "__main__":
    unittest.main()


class MyTestCase(aiounittest.AsyncTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bot = Mock(discord.client)
        cls.logs = logging.getLogger("Testing")
        cls.db = Mock(Database)
        cls.db.set_log_channel.return_value = "Join"
        cls.logger = Logger(cls.bot, cls.logs, cls.db)

    async def test_log_command(self):
        context = AsyncMock(commands.context.Context)
        context.channel = Mock(discord.TextChannel)
        context.channel.id = 4
        context.channel.mention = "test_mention"
        context.guild = Mock(discord.Guild)
        context.guild.id = 5
        context.send = AsyncMock(return_value=Mock(discord.Message))
        await self.logger.log(self, context, "Join", "here")
        self.assertTrue(context.send.called)
        self.assertTrue(self.db.set_log_channel.called)

    async def test_correct_error_when_bad_channel_is_called(self):
        context = AsyncMock(commands.context.Context)
        context.channel = Mock(discord.TextChannel)
        context.channel.id = 4
        context.channel.mention = "test_mention"
        context.guild = Mock(discord.Guild)
        context.guild.id = 5
        context.send = AsyncMock(return_value=Mock(discord.Message))
        with self.assertRaises(commands.BadArgument):
            await self.logger.log(self, context, "Join", "test")
        self.assertFalse(context.send.called)

    async def test_clear_command(self):
        context = AsyncMock(commands.context.Context)
        context.guild = Mock(discord.Guild)
        context.guild.id = 5
        context.send = AsyncMock(return_value=Mock(discord.Message))
        await self.logger.clear(self, context, "Join")
        self.assertTrue(context.send.called)
        self.assertTrue(self.db.set_log_channel.called)

    async def test_on_message(self):
        message = Mock(discord.Message)
        await self.logger.on_message(message)
        self.assertTrue(self.db.add_message.called)
