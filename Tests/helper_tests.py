import logging
import sqlite3
import unittest
from datetime import datetime

from mock import AsyncMock

from Helpers.database import Database
from Helpers.helpers import *
import discord
from mockito import mock
import aiounittest

from Helpers.models import BetterTimeDelta, BetterDateTime


class TestHelperMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.invite = mock(discord.Invite)
        cls.invite.id = "12345"
        cls.invite.uses = 10
        cls.invite2 = mock(discord.Invite)
        cls.invite2.id = "12345"
        cls.invite2.uses = 20

    def test_add_invite(self):
        add_invite(self.invite)
        self.assertEqual(self.invite, get_invite("12345"))

    def test_update_invite(self):
        add_invite(self.invite)
        self.assertEqual(self.invite, get_invite("12345"))

        update_invite(self.invite2)
        self.assertEqual(self.invite2, get_invite("12345"))

    def test_remove_invite(self):
        add_invite(self.invite)
        self.assertEqual(self.invite, get_invite("12345"))
        remove_invite(self.invite)
        with self.assertRaises(Exception) as context:
            get_invite("12345")
        self.assertTrue("No Invite Found", context.exception)

    def test_remove_invite_if_invite_missing(self):
        with self.assertRaises(Exception) as context:
            remove_invite(self.invite)
        self.assertTrue("No Invite Found", context.exception)

    def test_message_splitter(self):
        self.assertEqual(["12", "3"], message_splitter("123", 2))

    def test_message_splitter_short(self):
        self.assertEqual(["123"], message_splitter("123", 3))

    def test_message_splitter_error(self):
        with self.assertRaises(ValueError) as context:
            message_splitter("", 3)
        self.assertTrue("Message has no contents", context.exception)


class TestAsyncHelperMethods(aiounittest.AsyncTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.bot = mock(discord.Client)
        cls.guild1 = AsyncMock(discord.Guild)
        cls.guild2 = AsyncMock(discord.Guild)
        cls.invite1 = mock(discord.Invite)
        cls.invite1.id = "1"
        cls.invite2 = mock(discord.Invite)
        cls.invite2.id = "2"
        cls.invite3 = mock(discord.Invite)
        cls.invite3.id = "3"
        cls.invite4 = mock(discord.Invite)
        cls.invite4.id = "4"
        cls.guild1.invites.return_value = [cls.invite1, cls.invite2]
        cls.guild2.invites.return_value = [cls.invite3, cls.invite4]
        cls.bot.guilds = [cls.guild1, cls.guild2]

    async def test_add_all_invites(self):

        await add_all_invites(self.bot)
        self.assertEqual(self.invite1, get_invite("1"))
        self.assertEqual(self.invite2, get_invite("2"))
        self.assertEqual(self.invite3, get_invite("3"))
        self.assertEqual(self.invite4, get_invite("4"))

    async def test_add_all_guild_invites(self):
        await add_all_guild_invites(self.guild1)
        self.assertEqual(self.invite1, get_invite("1"))
        self.assertEqual(self.invite2, get_invite("2"))

    async def test_remove_all_guild_invites(self):
        await add_all_guild_invites(self.guild1)
        self.assertEqual(self.invite1, get_invite("1"))
        self.assertEqual(self.invite2, get_invite("2"))

        await remove_all_guild_invites(self.guild1)

        with self.assertRaises(Exception) as context:
            get_invite("1")
        self.assertTrue("No Invite Found", context.exception)


class TestSetLogChannel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        test_log = logging.getLogger()
        with open("../schema.sql", "r") as schema_file:
            cls.db = Database(sqlite3.connect(":memory:"), test_log, schema_file)
        cls.guild = mock(discord.Guild)
        cls.guild.id = 1
        cls.db.add_guild(cls.guild)

    def test_join(self):
        self.assertEqual("Join", self.db.set_log_channel("join", 1, 2))
        self.assertEqual(2, self.db.get_log_by_id(1).join_id)

    def test_leave(self):
        self.assertEqual("Leave", self.db.set_log_channel("leave", 1, 2))
        self.assertEqual(2, self.db.get_log_by_id(1).leave_id)

    def test_delete(self):
        self.assertEqual("Delete", self.db.set_log_channel("delete", 1, 2))
        self.assertEqual(2, self.db.get_log_by_id(1).delete_id)

    def test_buik_delete(self):
        self.assertEqual("Bulk Delete", self.db.set_log_channel("bulk_delete", 1, 2))
        self.assertEqual(2, self.db.get_log_by_id(1).delete_bulk)

    def test_edit(self):
        self.assertEqual("Edit", self.db.set_log_channel("edit", 1, 2))
        self.assertEqual(2, self.db.get_log_by_id(1).edit)

    def test_username(self):
        self.assertEqual("Username", self.db.set_log_channel("username", 1, 2))
        self.assertEqual(2, self.db.get_log_by_id(1).username)

    def test_nickname(self):
        self.assertEqual("Nickname", self.db.set_log_channel("nickname", 1, 2))
        self.assertEqual(2, self.db.get_log_by_id(1).nickname)

    def test_avatar(self):
        self.assertEqual("Avatar", self.db.set_log_channel("avatar", 1, 2))
        self.assertEqual(2, self.db.get_log_by_id(1).avatar)

    def test_lj_log(self):
        self.assertEqual("Lumberjack Logs", self.db.set_log_channel("ljlog", 1, 2))
        self.assertEqual(2, self.db.get_log_by_id(1).lj_id)

    def test_error(self):
        with self.assertRaises(ValueError) as context:
            self.db.set_log_channel("test", 1, 2)
        self.assertTrue("No Invite Found", context.exception)


class BetterTimeDeltaTest(unittest.TestCase):
    def test_str_three_days(self):
        self.assertEqual(
            "3 days 1 hour 1 minute ", str(BetterTimeDelta(days=3, seconds=3663))
        )

    def test_str_one_day(self):
        self.assertEqual(
            "1 day 2 hours 41 minutes ", str(BetterTimeDelta(days=1, seconds=9663))
        )

    def test_str_three_seconds(self):
        self.assertEqual("3 seconds ", str(BetterTimeDelta(seconds=3)))

    def test_str_one_second(self):
        self.assertEqual("1 second ", str(BetterTimeDelta(seconds=1)))

    def test_time_delta_subtraction(self):
        self.assertEqual(
            "5 hours ",
            str(BetterDateTime.utcnow() - BetterDateTime.from_datetime(datetime.now())),
        )
