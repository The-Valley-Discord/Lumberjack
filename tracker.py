from datetime import datetime, timedelta

import discord
from discord.ext import commands

from database import (
    get_tracked_by_id,
    remove_tracker,
    get_log_by_id,
    add_tracker,
    get_msg_by_id,
)
from helpers import message_splitter, has_permissions


class Tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    @commands.check_any(has_permissions())
    async def track(self, ctx, user: discord.Member, time, channel: discord.TextChannel):
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
            new_tracker = (
                user.id,
                username,
                ctx.guild.id,
                channel.id,
                tracking_time,
                ctx.author.id,
                modname,
            )
            gld = get_log_by_id(ctx.guild.id)
            logs = self.bot.get_channel(gld[10])
            add_tracker(new_tracker)
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
        tracker_to_remove = (ctx.guild.id, user.id)
        modname = f"{ctx.author.name}#{ctx.author.discriminator}"
        username = f"{user.name}#{user.discriminator}"
        remove_tracker(tracker_to_remove)
        await ctx.send(f"{username} is no longer being tracked")
        gld = get_log_by_id(ctx.guild.id)
        logs = self.bot.get_channel(gld[10])
        await logs.send(f"{modname} removed the tracker on {username}")

    @untrack.error
    async def untrack_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                f"A Valid User was not entered\nFormat is lum.untrack (user mention/id)"
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        tracked = (message.guild.id, message.author.id)
        tracker = get_tracked_by_id(tracked)
        if tracker is None:
            pass
        else:
            attachments = [
                f"{attachment.proxy_url}" for attachment in message.attachments
            ]
            end_time = datetime.strptime(tracker[4], "%Y-%m-%d %H:%M:%S.%f")
            channel = self.bot.get_channel(tracker[3])
            if end_time < datetime.utcnow():
                remove_tracker(tracked)
                embed = discord.Embed(
                    description=f"""Tracker on {tracker[1]} has expired""",
                    color=0xFFF1D7,
                )
                embed.set_author(name="Tracker Expired")
                embed.timestamp = datetime.utcnow()
                gld = get_log_by_id(message.channel.guild.id)
                logs = self.bot.get_channel(gld[10])
                await logs.send(embed=embed)
                await channel.send(embed=embed)
            else:
                message_split = message_splitter(message.clean_content, 1900)
                embed = discord.Embed(
                    description=f"**[Jump URL]({message.jump_url})**\n{message_split[0]}",
                    color=0xFFF1D7,
                )
                embed.set_footer(
                    text=f"{tracker[1]}\t({tracker[0]})\nMessage sent",
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
        before = get_msg_by_id(payload.message_id)
        after = await channel.fetch_message(payload.message_id)
        tracked = (after.guild.id, after.author.id)
        tracker = get_tracked_by_id(tracked)
        if tracker is None:
            pass
        else:
            channel = self.bot.get_channel(tracker[3])
            embed = discord.Embed(
                description=f"**[Jump Url]({after.jump_url})**", color=0xFFF1D7,
            )
            embed.set_author(name=f"#{after.channel.name}")
            embed.set_footer(
                text=f"{tracker[1]}\t({tracker[0]})\nMessage sent",
                icon_url=after.author.avatar_url,
            )
            embed.timestamp = datetime.utcnow()
            if len(before[7]) == 0:
                embed.add_field(name=f"**Before**", value=f"`Blank`", inline=False)
            elif len(before[7]) <= 1024:
                embed.add_field(name=f"**Before**", value=f"{before[7]} ", inline=False)
            else:
                prts = before[7]
                prt_1 = prts[:1024]
                prt_2 = prts[1024:]
                embed.add_field(name=f"**Before**", value=f"{prt_1}", inline=False)
                embed.add_field(name=f"Continued", value=f"{prt_2}")
            if len(after.content) == 0:
                embed.add_field(name=f"**After**", value=f"`Blank`", inline=False)
            elif len(after.content) <= 1024:
                embed.add_field(
                    name=f"**After**", value=f"{after.content} ", inline=False
                )
            else:
                prts = after.content
                prt_1 = prts[:1024]
                prt_2 = prts[1024:]
                embed.add_field(name=f"**After**", value=f"{prt_1}", inline=False)
                embed.add_field(name=f"Continued", value=f"{prt_2}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        tracked = (member.guild.id, member.id)
        tracker = get_tracked_by_id(tracked)
        if tracker is None:
            pass
        else:
            channel = self.bot.get_channel(tracker[3])
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
                    text=f"{tracker[1]}\n({member.id}) ", icon_url=member.avatar_url
                )
                embed.timestamp = datetime.utcnow()
                await channel.send(embed=embed)
            elif after.channel is None:
                embed = discord.Embed(
                    description=f"**channel:** {before.channel.name}", color=0xFF0080
                )
                embed.set_author(name="Left Voice Channel")
                embed.set_footer(
                    text=f"{tracker[1]}\n({member.id})", icon_url=member.avatar_url
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
                    text=f"{tracker[1]}\n({member.id})", icon_url=member.avatar_url
                )
                embed.timestamp = datetime.utcnow()
                await channel.send(embed=embed)
            else:
                await channel.send("There was an error on VC log")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        tracked = (after.guild.id, after.id)
        tracker = get_tracked_by_id(tracked)
        if tracker is None:
            pass
        else:
            channel = self.bot.get_channel(tracker[3])
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
            tracked = (guild.id, after.id)
            tracker = get_tracked_by_id(tracked)
            if tracker is None:
                pass
            else:
                if (
                    before.name != after.name
                    or before.discriminator != after.discriminator
                ):
                    channel = self.bot.get_channel(tracker[3])
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
                    channel = self.bot.get_channel(tracker[3])
                    if channel is None:
                        pass
                    else:
                        embed = discord.Embed(description=f"New avatar", color=0x8000FF)
                        embed.set_author(name=f"{after.name}#{after.discriminator}")
                        embed.set_footer(text=f"{after.id}")
                        embed.set_thumbnail(url=after.avatar_url)
                        embed.timestamp = datetime.utcnow()
                        await channel.send(embed=embed)
