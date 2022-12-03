import logging
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import discord

from lumberjack.helpers.database import Database
from lumberjack.helpers.models import DBGuild, DBMessage, Tracking

if __name__ == "__main__":
    unittest.main()

logs = logging.getLogger("Testing")


class TestDatabaseMessageMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open("../lumberjack/migrations/schema.sql", "r") as schema_file:
            cls.db = Database(sqlite3.connect(":memory:"), logs, schema_file)
        cls.message = Mock(discord.Message)
        cls.message.id = 1
        cls.message.created_at = datetime.now(timezone.utc)
        cls.message.clean_content = "Test_Content"

        cls.author = Mock(discord.Member)
        cls.author.id = 5
        cls.author.display_name = "Test_User"
        cls.author.avatar.url = "Test_Avatar_URL"
        cls.author.name = "Test_name"
        cls.author.discriminator = "0001"

        cls.channel = Mock(discord.TextChannel)
        cls.channel.id = 2
        cls.channel.name = "Test_Channel"

        cls.guild = Mock(discord.Guild)
        cls.guild.id = 3

        cls.attachment = Mock(discord.Attachment)
        cls.attachment.proxy_url = "Test_Attachment"

        cls.message.author = cls.author
        cls.message.channel = cls.channel
        cls.message.guild = cls.guild
        cls.message.attachments = [cls.attachment]

        cls.db.add_message(cls.message)
        cls.db.add_guild(cls.guild)

    def test_add_message(self):
        retrieved_message = self.db.get_msg_by_id(1)

        self.assertIsInstance(retrieved_message, DBMessage)
        self.assertEqual(self.message.clean_content, retrieved_message.clean_content)
        self.assertEqual(self.attachment.proxy_url, retrieved_message.attachments[0])

    def test_get_message_retrieves_guild_settings(self):
        retrieved_message = self.db.get_msg_by_id(1)

        self.assertIsInstance(retrieved_message.guild, DBGuild)
        self.assertEqual(self.guild.id, retrieved_message.guild.id)

    def test_update_msg(self):
        message = self.message
        message.id = 2
        self.db.add_message(message)
        self.db.update_msg(self.message.id, "updated_content")
        retrieved_message = self.db.get_msg_by_id(2)
        self.assertEqual("updated_content", retrieved_message.clean_content)

    def test_delete_old_db_messages(self):
        message = self.message
        message.id = 3
        message.created_at = datetime.now(timezone.utc) - timedelta(days=35)
        self.db.add_message(message)
        self.db.delete_old_db_messages()

        with self.assertRaises(ValueError) as context:
            self.db.get_msg_by_id(3)
        self.assertEqual("Retrieved message not in database.", str(context.exception))


class TestSetLogChannel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        test_log = logging.getLogger()
        with open("../lumberjack/migrations/schema.sql", "r") as schema_file:
            cls.db = Database(sqlite3.connect(":memory:"), test_log, schema_file)
        cls.guild = Mock(discord.Guild)
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
        self.assertEqual("Log type not found.", str(context.exception))


class TestTracking(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open("../lumberjack/migrations/schema.sql", "r") as schema_file:
            cls.db = Database(
                sqlite3.connect(
                    ":memory:",
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                ),
                logs,
                schema_file,
            )

    def test_add_tracker(self):
        tracker = Tracking(
            1, "Test_user", 2, 3, datetime.now(timezone.utc), 4, "Test_Mod"
        )
        self.db.add_tracker(tracker)
        retrieved_tracker = self.db.get_tracked_by_id(2, 1)
        self.assertEqual(tracker, retrieved_tracker)

    def test_update_tracker(self):
        tracker = Tracking(
            1, "Test_user", 2, 3, datetime.now(timezone.utc), 4, "Test_Mod"
        )
        self.db.add_tracker(tracker)
        tracker2 = Tracking(
            1, "Test_user", 2, 3, datetime.now(timezone.utc), 4, "New_Test_Mod"
        )
        self.db.add_tracker(tracker2)
        retrieved_tracker = self.db.get_tracked_by_id(2, 1)
        self.assertEqual(tracker2, retrieved_tracker)

    def test_remove_tracker(self):
        tracker = Tracking(
            1, "Test_user", 2, 3, datetime.now(timezone.utc), 4, "Test_Mod"
        )
        self.db.add_tracker(tracker)
        self.db.remove_tracker(2, 1)
        with self.assertRaises(Exception) as context:
            self.db.get_tracked_by_id(2, 1)
        self.assertEqual("User not being tracked.", str(context.exception))


class TestLumberjackMessageStorage(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open("../lumberjack/migrations/schema.sql", "r") as schema_file:
            cls.db = Database(
                sqlite3.connect(
                    ":memory:",
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                ),
                logs,
                schema_file,
            )

    def test_add_lumberjack_message(self):
        message = Mock(discord.Message)
        message.id = 5
        message.channel = Mock(discord.TextChannel)
        message.channel.id = 6
        message.created_at = datetime.now(timezone.utc) - timedelta(days=36)
        self.db.add_lumberjack_message(message)
        retrieved_message = self.db.get_oldest_lumberjack_message()
        self.assertEqual(5, retrieved_message.message_id)
        self.assertEqual(6, retrieved_message.channel_id)
        self.assertEqual(message.created_at, retrieved_message.created_at)

    def test_delete_lumberjack_messages_from_db(self):
        message = Mock(discord.Message)
        message.id = 6
        message.channel = Mock(discord.TextChannel)
        message.channel.id = 6
        message.created_at = datetime.now(timezone.utc) - timedelta(days=36)
        self.db.add_lumberjack_message(message)
        self.db.delete_lumberjack_messages_from_db(6)
        self.db.delete_lumberjack_messages_from_db(5)
        message = self.db.get_oldest_lumberjack_message()
        self.assertTrue(message is None)
