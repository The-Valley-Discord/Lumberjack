import random
import string
import unittest
from datetime import datetime, timezone

import aiounittest
from mock import AsyncMock, Mock

from lumberjack.helpers.helpers import *
from lumberjack.helpers.models import BetterTimeDelta, BetterDateTime

if __name__ == "__main__":
    unittest.main()


class TestHelperMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.invite = Mock(discord.Invite)
        cls.invite.id = "12345"
        cls.invite.uses = 10
        cls.invite2 = Mock(discord.Invite)
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
        self.assertEqual("No Invite Found", str(context.exception))

    def test_remove_invite_if_invite_missing(self):
        with self.assertRaises(Exception) as context:
            remove_invite(self.invite)
        self.assertEqual("No Invite Found", str(context.exception))

    def test_message_splitter(self):
        self.assertEqual(["12", "3"], message_splitter("123", 2))

    def test_message_splitter_short(self):
        self.assertEqual(["123"], message_splitter("123", 3))

    def test_message_splitter_error(self):
        with self.assertRaises(ValueError) as context:
            message_splitter("", 3)
        self.assertEqual("Message has no contents", str(context.exception))

    def test_field_message_splitter(self):
        embed = discord.Embed()
        text = "".join(random.choices(string.ascii_uppercase + string.digits, k=1050))
        embed = field_message_splitter(embed, text, "Test")
        self.assertEqual("**Test**", embed.fields[0].name)
        self.assertEqual(f"{text[:1024]} ", embed.fields[0].value)
        self.assertEqual("Continued", embed.fields[1].name)
        self.assertEqual(text[1024:], embed.fields[1].value)


class TestAsyncHelperMethods(aiounittest.AsyncTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bot = Mock(discord.Client)
        cls.guild1 = AsyncMock(discord.Guild)
        cls.guild2 = AsyncMock(discord.Guild)
        cls.invite1 = Mock(discord.Invite)
        cls.invite1.id = "1"
        cls.invite2 = Mock(discord.Invite)
        cls.invite2.id = "2"
        cls.invite3 = Mock(discord.Invite)
        cls.invite3.id = "3"
        cls.invite4 = Mock(discord.Invite)
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
        self.assertEqual("No Invite Found", str(context.exception))


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
            str(
                BetterDateTime.now(timezone.utc)
                - BetterDateTime.from_datetime(datetime.now(timezone.utc))
            ),
        )
