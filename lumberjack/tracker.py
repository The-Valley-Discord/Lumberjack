import datetime

import discord
from discord.ext import commands

from . import c, conn


class Tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Tracker message listener

        :param message: API Message Context
        """
        tracked = (message.guild.id, message.author.id)
        tracker = self.get_tracked_by_id(conn, tracked)

        attachments = [f"{attachment.proxy_url}" for attachment in message.attachments]
        if len(attachments) > 0:
            for attachment in attachments:
                c.execute("INSERT INTO attachment_urls VALUES (:message_id, :attachment)",
                          {'message_id': message.id, 'attachment': attachment})

        if tracker is None:
            pass
        else:
            end_time = datetime.strptime(tracker[4], '%Y-%m-%d %H:%M:%S.%f')
            if end_time < datetime.utcnow():
                self.remove_tracker(conn, tracked)
            else:
                channel = self.bot.get_channel(tracker[3])
                embed = discord.Embed(title=f'**Tracked User Message in {message.channel.name}**',
                                      description=f'''**{message.channel.mention} ({message.channel.id})**''',
                                      color=0xFFF1D7)
                embed.set_author(name=f'{tracker[1]}({tracker[0]})')
                embed.set_thumbnail(url=message.author.avatar_url)
                embed.set_footer(text=f'Tracer set by {tracker[6]} ({tracker[5]})')
                embed.timestamp = datetime.utcnow()
                if 0 < len(message.clean_content) <= 1024:
                    embed.add_field(name='**Message Content**',
                                    value=f'{message.clean_content}',
                                    inline=False)
                elif len(message.clean_content) > 1024:
                    prts = message.clean_content
                    prt_1 = prts[:1024]
                    prt_2 = prts[1024:]
                    embed.add_field(name=f'**Content**', value=f'{prt_1}', inline=False)
                    embed.add_field(name=f'Continued', value=f'{prt_2}')
                else:
                    pass
                if len(attachments) > 0:
                    attachments_str = " ".join(attachments)
                    embed.add_field(name=f'**Attachments**', value=f'{attachments_str}', inline=False)
                    embed.set_image(url=attachments[0])
                else:
                    pass
                await channel.send(embed=embed)

    @staticmethod
    def get_tracked_by_id(conn, tracked):
        """
        Get tracking entry with user ID

        :param conn: SQL Connection Object
        :param tracked: [guild ID, user ID]
        :return: (array) tracking information
        """
        # TODO: Change tracked array members to function parameters with default values
        sql = '''SELECT * FROM tracking WHERE guildid=? AND userid=?'''
        c.execute(sql, tracked)
        conn.commit()
        return c.fetchone()

    def add_tracker(self, conn, inttracker):
        """
        Add tracker to user

        :param conn:
        :param inttracker:
        :return:
        """
        # TODO: Change inttracker array members to function parameters with default values
        tracked = (inttracker[2], inttracker[0])
        tracker_check = self.get_tracked_by_id(conn, tracked)
        if tracker_check is None:
            sql = '''INSERT INTO tracking (userid,username,guildid,channelid,endtime,modid,modname) 
            VALUES(?,?,?,?,?,?,?) '''
            c.execute(sql, inttracker)
            conn.commit()
        else:
            c.execute("""UPDATE tracking SET endtime = :endtime,
                                 modid = :modid,
                                 modname = :modname
                                WHERE userid = :userid
                                AND guildid = :guildid""",
                      {'endtime': inttracker[4],
                       'modid': inttracker[5],
                       'modname': inttracker[6],
                       'userid': inttracker[0],
                       'guildid': inttracker[2]})
        return c.lastrowid

    @staticmethod
    def remove_tracker(conn, inttracker):
        """
        Remove tracker from user

        :param conn: SQL Connection Object
        :param inttracker: [guild ID, user ID]
        :return: (array) ID of removed user
        """
        # TODO: Change inttracker array members to function parameters with default values
        sql = """DELETE from tracking WHERE guildid = ? AND userid = ?"""
        c.execute(sql, inttracker)
        conn.commit()
        return c.lastrowid
