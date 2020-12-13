import logging
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from Helpers.database import Database
from Helpers.helpers import message_splitter, has_permissions
from Helpers.models import Tracking


class Tracker(commands.Cog):
    def __init__(self, bot: discord.Client, logs: logging, db: Database):
        self.bot = bot
        self.logs = logs
        self.db = db
        self._last_member = None

    @commands.command()
    @commands.check_any(has_permissions())
    async def track(
        self, ctx, user: discord.Member, time, channel: discord.TextChannel
    ):
        tracking_time = 0
        if time[-1].lower() == "d":
            time_limit = timedelta(days=int(time[:-1]))
            tracking_time = datetime.utcnow() + time_limit
        elif time[-1].lower() == "h":
            time_limit = timedelta(hours=int(time[:-1]))
            tracking_time = datetime.utcnow() + time_limit
        elif time[-1].lower() == "m":
            time_limit = timedelta(minutes=int(time[:-1]))
            tracking_time = datetime.utcnow() + time_limit
        else:
            pass
        if user.guild_permissions.manage_guild:
            await ctx.send(f"<\_<\n>\_>\nI can't track a mod.\n Try someone else")
        elif channel.guild != ctx.guild:
            await ctx.send(
                f"<\_<\n>\_>\nThat channel is not on this server.\n Try a different one."
            )
        else:
            username = f"{user.name}#{user.discriminator}"
            modname = f"{ctx.author.name}#{ctx.author.discriminator}"

            gld = self.db.get_log_by_id(ctx.guild.id)
            logs = self.bot.get_channel(gld.lj_id)
            self.db.add_tracker(
                Tracking(
                    user.id,
                    username,
                    ctx.guild.id,
                    channel.id,
                    tracking_time,
                    ctx.author.id,
                    modname,
                )
            )
            await ctx.send(f"A Tracker has been placed on {username} for {time}")
            await logs.send(f"{modname} placed a tracker on {user.mention} for {time}")

    @track.error
    async def track_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                "A Valid User or channel was not entered\nFormat is lum.track (user mention/id) (time in d or h) "
                "(log channel mention/id)"
            )

    @commands.command()
    @commands.check_any(has_permissions())
    async def untrack(self, ctx, user: discord.Member):
        modname = f"{ctx.author.name}#{ctx.author.discriminator}"
        username = f"{user.name}#{user.discriminator}"
        self.db.remove_tracker(ctx.guild.id, user.id)
        await ctx.send(f"{username} is no longer being tracked")
        gld = self.db.get_log_by_id(ctx.guild.id)
        logs = self.bot.get_channel(gld.lj_id)
        await logs.send(f"{modname} removed the tracker on {username}")

    @untrack.error
    async def untrack_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                f"A Valid User was not entered\nFormat is lum.untrack (user mention/id)"
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        tracker = self.db.get_tracked_by_id(message.guild.id, message.author.id)
        if tracker is None:
            pass
        else:
            attachments = [
                f"{attachment.proxy_url}" for attachment in message.attachments
            ]
            end_time = datetime.strptime(tracker.end_time, "%Y-%m-%d %H:%M:%S.%f")
            channel = self.bot.get_channel(tracker.channel_id)
            if end_time < datetime.utcnow():
                self.db.remove_tracker(message.guild.id, message.author.id)
                embed = discord.Embed(
                    description=f"""Tracker on {tracker.username} has expired""",
                    color=0xFFF1D7,
                )
                embed.set_author(name="Tracker Expired")
                embed.timestamp = datetime.utcnow()
                gld = self.db.get_log_by_id(message.channel.guild.id)
                logs = self.bot.get_channel(gld.lj_id)
                await logs.send(embed=embed)
                await channel.send(embed=embed)
            else:
                try:
                    message_split = message_splitter(message.clean_content, 1900)
                except ValueError:
                    message_split = ["`blank`"]
                embed = discord.Embed(
                    description=f"**[Jump URL]({message.jump_url})**\n{message_split[0]}",
                    color=0xFFF1D7,
                )
                embed.set_footer(
                    text=f"{tracker.username}\t({tracker.user_id})\nMessage sent",
                    icon_url=f"{message.author.avatar_url}",
                )
                embed.set_author(name=f"#{message.channel.name}")
                embed.timestamp = datetime.utcnow()
                if len(message.clean_content) > 1900:
                    embed.add_field(name=f"Continued", value=f"{message_split[1]}")
                if len(attachments) > 0:
                    attachments_str = " ".join(attachments)
                    embed.add_field(
                        name=f"**Attachments**",
                        value=f"{attachments_str}",
                        inline=False,
                    )
                    embed.set_image(url=attachments[0])
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        before = self.db.get_msg_by_id(payload.message_id)
        author = self.bot.get_user(before.author.id)
        tracker = self.db.get_tracked_by_id(channel.guild.id, before.author.id)
        if "content" not in payload.data:
            payload.data["content"] = ""
        if tracker is None:
            pass
        else:
            channel = self.bot.get_channel(tracker.channel_id)
            embed = discord.Embed(
                description=f"**[Jump Url](https://discordapp.com/channels/"
                f"{channel.guild.id}/{payload.channel_id}/{payload.message_id})**",
                color=0xFFF1D7,
            )
            embed.set_author(name=f"#{channel.name}")
            embed.set_footer(
                text=f"{tracker.username}\t({tracker.user_id})\nMessage sent",
                icon_url=author.avatar_url,
            )
            embed.timestamp = datetime.utcnow()
            if len(before.clean_content) == 0:
                embed.add_field(name=f"**Before**", value=f"`Blank`", inline=False)
            elif len(before.clean_content) <= 1024:
                embed.add_field(
                    name=f"**Before**", value=f"{before.clean_content} ", inline=False
                )
            else:
                prts = before.clean_content
                prt_1 = prts[:1024]
                prt_2 = prts[1024:]
                embed.add_field(name=f"**Before**", value=f"{prt_1}", inline=False)
                embed.add_field(name=f"Continued", value=f"{prt_2}")
            if len(payload.data["content"]) == 0:
                embed.add_field(name=f"**After**", value=f"`Blank`", inline=False)
            elif len(payload.data["content"]) <= 1024:
                embed.add_field(
                    name=f"**After**", value=f"{payload.data['content']} ", inline=False
                )
            else:
                prts = payload.data["content"]
                prt_1 = prts[:1024]
                prt_2 = prts[1024:]
                embed.add_field(name=f"**After**", value=f"{prt_1}", inline=False)
                embed.add_field(name=f"Continued", value=f"{prt_2}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        tracker = self.db.get_tracked_by_id(member.guild.id, member.id)
        if tracker is None:
            pass
        else:
            channel = self.bot.get_channel(tracker.channel_id)
            if before.channel == after.channel:
                pass
            elif tracker is None:
                pass
            elif before.channel is None:
                embed = discord.Embed(
                    description=f"**channel:** {after.channel.name}", color=0xFF0080
                )
                embed.set_author(name="Joined Voice Channel")
                embed.set_footer(
                    text=f"{tracker.username}\n({member.id}) ",
                    icon_url=member.avatar_url,
                )
                embed.timestamp = datetime.utcnow()
                await channel.send(embed=embed)
            elif after.channel is None:
                embed = discord.Embed(
                    description=f"**channel:** {before.channel.name}", color=0xFF0080
                )
                embed.set_author(name="Left Voice Channel")
                embed.set_footer(
                    text=f"{tracker.username}\n({member.id})",
                    icon_url=member.avatar_url,
                )
                embed.timestamp = datetime.utcnow()
                await channel.send(embed=embed)
            elif after.channel != before.channel:
                embed = discord.Embed(
                    description=f"**From:** {before.channel.name}\n"
                    f"**To:** {after.channel.name}",
                    color=0xFF0080,
                )
                embed.set_author(name="Moved Voice Channels")
                embed.set_footer(
                    text=f"{tracker.username}\n({member.id})",
                    icon_url=member.avatar_url,
                )
                embed.timestamp = datetime.utcnow()
                await channel.send(embed=embed)
            else:
                await channel.send("There was an error on VC log")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        tracker = self.db.get_tracked_by_id(after.guild.id, after.id)
        if tracker is None:
            pass
        else:
            channel = self.bot.get_channel(tracker.channel_id)
            if before.nick == after.nick:
                pass
            elif channel is None:
                pass
            else:
                embed = discord.Embed(
                    description=f"**Before:** {before.nick}\n**After:** {after.nick}",
                    color=0x22FFC2,
                )
                embed.set_author(name=f"{after.name}#{after.discriminator}")
                embed.set_footer(text=f"{after.id}")
                embed.timestamp = datetime.utcnow()
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        for guild in self.bot.guilds:
            tracker = self.db.get_tracked_by_id(guild.id, after.id)
            if tracker is None:
                pass
            else:
                if (
                    before.name != after.name
                    or before.discriminator != after.discriminator
                ):
                    channel = self.bot.get_channel(tracker.channel_id)
                    if channel is None:
                        pass
                    else:
                        embed = discord.Embed(
                            description=(
                                f"**Before:** {before.name}#{before.discriminator}\n"
                                f"**After:** {after.name}#{after.discriminator}"
                            ),
                            color=0x22FFC2,
                        )
                        embed.set_author(name=f"{after.name}#{after.discriminator}")
                        embed.set_footer(text=f"{after.id}")
                        embed.timestamp = datetime.utcnow()
                        await channel.send(embed=embed)
                if before.avatar != after.avatar:
                    channel = self.bot.get_channel(tracker.channel_id)
                    if channel is None:
                        pass
                    else:
                        embed = discord.Embed(description=f"New avatar", color=0x8000FF)
                        embed.set_author(name=f"{after.name}#{after.discriminator}")
                        embed.set_footer(text=f"{after.id}")
                        embed.set_thumbnail(url=after.avatar_url)
                        embed.timestamp = datetime.utcnow()
                        await channel.send(embed=embed)
