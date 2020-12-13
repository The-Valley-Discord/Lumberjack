import unittest

from mock import AsyncMock

from Helpers.helpers import *
import discord
from mockito import mock
import aiounittest


class TestHelperMethods(unittest.TestCase):
    def test_add_invite(self):
        invite = mock(discord.Invite)
        invite.id = "12345"
        add_invite(invite)
        self.assertEqual(invite, get_invite("12345"))

    def test_update_invite(self):
        invite = mock(discord.Invite)
        invite.id = "12345"
        invite.uses = 10
        add_invite(invite)
        self.assertEqual(invite, get_invite("12345"))

        invite2 = mock(discord.Invite)
        invite2.id = "12345"
        invite2.uses = 20
        update_invite(invite2)
        self.assertEqual(invite2, get_invite("12345"))

    def test_remove_invite(self):
        invite = mock(discord.Invite)
        invite.id = "12345"
        invite.uses = 10
        add_invite(invite)
        self.assertEqual(invite, get_invite("12345"))
        remove_invite(invite)
        with self.assertRaises(Exception) as context:
            get_invite("12345")
        self.assertTrue("No Invite Found", context.exception)

    def test_remove_invite_if_invite_missing(self):
        invite = mock(discord.Invite)
        invite.id = "12345"
        with self.assertRaises(Exception) as context:
            remove_invite(invite)
        self.assertTrue("No Invite Found", context.exception)


class TestAsyncHelperMethods(aiounittest.AsyncTestCase):
    async def test_add_all_invites(self):
        bot = mock(discord.Client)
        guild1 = AsyncMock(discord.Guild)
        guild2 = AsyncMock(discord.Guild)
        invite1 = mock(discord.Invite)
        invite1.id = "1"
        invite2 = mock(discord.Invite)
        invite2.id = "2"
        invite3 = mock(discord.Invite)
        invite3.id = "3"
        invite4 = mock(discord.Invite)
        invite4.id = "4"
        guild1.invites.return_value = [invite1, invite2]
        guild2.invites.return_value = [invite3, invite4]
        bot.guilds = [guild1, guild2]
        await add_all_invites(bot)
        self.assertEqual(invite1, get_invite("1"))
        self.assertEqual(invite2, get_invite("2"))
        self.assertEqual(invite3, get_invite("3"))
        self.assertEqual(invite4, get_invite("4"))

    async def test_add_all_guild_invites(self):
        guild1 = AsyncMock(discord.Guild)
        invite1 = mock(discord.Invite)
        invite1.id = "1"
        invite2 = mock(discord.Invite)
        invite2.id = "2"
        guild1.invites.return_value = [invite1, invite2]
        await add_all_guild_invites(guild1)
        self.assertEqual(invite1, get_invite("1"))
        self.assertEqual(invite2, get_invite("2"))

    async def test_remove_all_guild_invites(self):
        guild1 = AsyncMock(discord.Guild)
        invite1 = mock(discord.Invite)
        invite1.id = "1"
        invite2 = mock(discord.Invite)
        invite2.id = "2"
        guild1.invites.return_value = [invite1, invite2]
        await add_all_guild_invites(guild1)
        self.assertEqual(invite1, get_invite("1"))
        self.assertEqual(invite2, get_invite("2"))

        await remove_all_guild_invites(guild1)

        with self.assertRaises(Exception) as context:
            get_invite("1")
        self.assertTrue("No Invite Found", context.exception)
