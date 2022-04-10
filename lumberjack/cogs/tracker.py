import typing
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context

from lumberjack.helpers.helpers import (
    message_splitter,
    has_permissions,
    field_message_splitter,
)
from lumberjack.helpers.models import Tracking, DBGuild, DBMessage
from lumberjack.cusomizations import Lumberjack


class Tracker(Lumberjack.Cog):
    def __init__(self, *args):
        self.clear_expired_trackers.start()
        super().__init__(*args)

    @commands.command()
    @commands.check_any(has_permissions())
    async def track(
        self,
        ctx: Context,
        user: discord.Member,
        time: str,
        channel: typing.Union[discord.TextChannel, str] = "here",
    ):
        if isinstance(channel, str) and  channel.lower() == "here":
            channel = ctx.channel
        tracking_time: datetime = datetime.now(timezone.utc)
        if time[-1].lower() == "d":
            tracking_time += timedelta(days=int(time[:-1]))
        elif time[-1].lower() == "h":
            tracking_time += timedelta(hours=int(time[:-1]))
        elif time[-1].lower() == "m":
            tracking_time += timedelta(minutes=int(time[:-1]))
        else:
            raise commands.BadArgument
        if user.guild_permissions.manage_guild:
            await ctx.send(f"<\_<\n>\_>\nI can't track a mod.\n Try someone else")
        elif channel.guild != ctx.guild:
            await ctx.send(
                f"<\_<\n>\_>\nThat channel is not on this server.\n Try a different one."
            )
        else:
            username = f"{user.name}#{user.discriminator}"
            modname = f"{ctx.author.name}#{ctx.author.discriminator}"

            gld: DBGuild = self.db.get_log_by_id(ctx.guild.id)
            logs: discord.TextChannel = self.bot.get_channel(gld.lj_id)
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
    async def track_error(self, ctx: Context, error: Exception):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                "A Valid User or channel was not entered\nFormat is `lum.track (user mention/id) (time in d h or m)` "
                "(<optional> log channel mention/id)"
            )
        elif not isinstance(error, commands.CheckAnyFailure):
            await ctx.send(
                "Format is `lum.track (user mention/id) (time in d h or m) (<optional> log channel mention/id)`"
            )

    @commands.command()
    @commands.check_any(has_permissions())
    async def untrack(self, ctx: Context, user: discord.Member):
        modname = f"{ctx.author.name}#{ctx.author.discriminator}"
        username = f"{user.name}#{user.discriminator}"
        self.db.remove_tracker(ctx.guild.id, user.id)
        await ctx.send(f"{username} is no longer being tracked")
        gld: DBGuild = self.db.get_log_by_id(ctx.guild.id)
        logs: discord.TextChannel = self.bot.get_channel(gld.lj_id)
        await logs.send(f"{modname} removed the tracker on {username}")

    @untrack.error
    async def untrack_error(self, ctx: Context, error: Exception):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                "A Valid User was not entered\nFormat is `lum.untrack (user mention/id)`"
            )
        elif not isinstance(error, commands.CheckAnyFailure):
            await ctx.send("Format is `lum.untrack (user mention/id)`")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            tracker: Tracking = self.db.get_tracked_by_id(
                message.guild.id, message.author.id
            )
        except ValueError:
            pass
        else:
            attachments = [
                attachment.proxy_url for attachment in message.attachments
            ]
            channel = self.bot.get_channel(tracker.channel_id)
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
                icon_url=f"{message.author.display_avatar.url}",
            )
            embed.set_author(name=f"#{message.channel.name}")
            embed.timestamp = discord.utils.utcnow()
            if len(message.clean_content) > 1900:
                embed.add_field(name=f"Continued", value=f"{message_split[1]}")
            if len(attachments) > 0:
                attachments_str = " \n".join(attachments)
                embed.add_field(
                    name=f"**Attachments**",
                    value=f"{attachments_str}",
                    inline=False,
                )
                embed.set_image(url=attachments[0])
            await channel.send(embed=embed)

    @tasks.loop(seconds=0.5)
    async def clear_expired_trackers(self):
        trackers = self.db.get_all_expired_trackers()
        for tracker in trackers:
            self.db.remove_tracker(tracker.guild_id, tracker.user_id)
            embed = discord.Embed(
                description=f"""Tracker on {tracker.username} has expired""",
                color=0xFFF1D7,
            )
            embed.set_author(name="Tracker Expired")
            embed.timestamp = discord.utils.utcnow()
            gld: DBGuild = self.db.get_log_by_id(tracker.guild_id)
            logs: discord.TextChannel = self.bot.get_channel(gld.lj_id)
            channel: discord.TextChannel = self.bot.get_channel(tracker.channel_id)
            if logs:
                try:
                    await logs.send(embed=embed)
                except discord.HTTPException or discord.Forbidden:
                    pass
            if channel:
                try:
                    await channel.send(embed=embed)
                except discord.HTTPException or discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        try:
            before: DBMessage = self.db.get_msg_by_id(payload.message_id)
        except ValueError:
            return
        try:
            tracker = self.db.get_tracked_by_id(before.guild.id, before.author.id)
        except ValueError:
            pass
        else:
            author: discord.User = self.bot.get_user(before.author.id)
            if "content" not in payload.data:
                payload.data["content"] = ""
            channel: discord.TextChannel = self.bot.get_channel(tracker.channel_id)
            embed = discord.Embed(
                description=f"**[Jump Url](https://discordapp.com/channels/"
                f"{channel.guild.id}/{payload.channel_id}/{payload.message_id})**",
                color=0xFFF1D7,
            )
            embed.set_author(name=f"#{channel.name}")
            embed.set_footer(
                text=f"{tracker.username}\t({tracker.user_id})\nMessage sent",
                icon_url=author.display_avatar.url,
            )
            embed.timestamp = discord.utils.utcnow()
            embed = field_message_splitter(embed, before.clean_content, "Before")
            embed = field_message_splitter(embed, payload.data["content"], "After")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        try:
            tracker: Tracking = self.db.get_tracked_by_id(member.guild.id, member.id)
        except ValueError:
            pass
        else:
            channel: discord.TextChannel = self.bot.get_channel(tracker.channel_id)
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
                    icon_url=member.display_avatar.url,
                )
                embed.timestamp = discord.utils.utcnow()
                await channel.send(embed=embed)
            elif after.channel is None:
                embed = discord.Embed(
                    description=f"**channel:** {before.channel.name}", color=0xFF0080
                )
                embed.set_author(name="Left Voice Channel")
                embed.set_footer(
                    text=f"{tracker.username}\n({member.id})",
                    icon_url=member.display_avatar.url,
                )
                embed.timestamp = discord.utils.utcnow()
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
                    icon_url=member.display_avatar.url,
                )
                embed.timestamp = discord.utils.utcnow()
                await channel.send(embed=embed)
            else:
                await channel.send("There was an error on VC log")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        try:
            tracker: Tracking = self.db.get_tracked_by_id(after.guild.id, after.id)
        except ValueError:
            pass
        else:
            channel: discord.TextChannel = self.bot.get_channel(tracker.channel_id)
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
                embed.timestamp = discord.utils.utcnow()
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        for guild in self.bot.guilds:
            try:
                tracker: Tracking = self.db.get_tracked_by_id(guild.id, after.id)
            except ValueError:
                pass
            else:
                channel: discord.TextChannel = self.bot.get_channel(tracker.channel_id)
                if channel is None:
                    return
                if (
                    before.name != after.name
                    or before.discriminator != after.discriminator
                ):
                    embed = discord.Embed(
                        description=(
                            f"**Before:** {before.name}#{before.discriminator}\n"
                            f"**After:** {after.name}#{after.discriminator}"
                        ),
                        color=0x22FFC2,
                    )
                    embed.set_author(name=f"{after.name}#{after.discriminator}")
                    embed.set_footer(text=f"{after.id}")
                    embed.timestamp = discord.utils.utcnow()
                    await channel.send(embed=embed)
                if before.avatar != after.avatar:
                    embed = discord.Embed(description=f"New avatar", color=0x8000FF)
                    embed.set_author(name=f"{after.name}#{after.discriminator}")
                    embed.set_footer(text=f"{after.id}")
                    embed.set_thumbnail(url=after.display_avatar.url)
                    embed.timestamp = discord.utils.utcnow()
                    await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Tracker(bot))
