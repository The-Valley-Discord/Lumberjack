import logging
from datetime import datetime

import discord
from discord.ext import commands

from Helpers.database import Database
from Helpers.helpers import get_invite, update_invite, format_date
from Helpers.models import BetterDateTime, DBGuild


class MemberLog(commands.Cog):
    def __init__(self, bot: discord.Client, logs: logging, db: Database):
        self.bot: discord.Client = bot
        self.logs: logging = logs
        self.db: Database = db
        self._last_member = None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        gld: DBGuild = self.db.get_log_by_id(member.guild.id)
        logs: discord.TextChannel = self.bot.get_channel(gld.join_id)
        account_age = BetterDateTime.utcnow() - BetterDateTime.from_datetime(
            member.created_at
        )
        invite_used = "Unknown Invite"
        invite_uses = ""
        inviter = ""
        for invite in await member.guild.invites():
            before_invite: discord.Invite = get_invite(invite.id)
            if before_invite.uses != invite.uses:
                invite_used = invite.url
                invite_uses = f"({invite.uses} uses)"
                inviter = invite.inviter
                update_invite(invite)
        if account_age.days < 7:
            color = 0xFFC704
        else:
            color = 0x008000
        if logs is None:
            pass
        else:
            embed = discord.Embed(
                title=f"**User Joined**",
                description=(
                    f"**Name:** {member.mention}\n"
                    f"**Created on:** {member.created_at.strftime(format_date)}\n"
                    f"**Account age:** {account_age.days} days old\n"
                    f"**Invite used:** {invite_used} {invite_uses}\n"
                    f"**Created By:** {inviter}"
                ),
                color=color,
            )
            if account_age.days < 7:
                embed.add_field(
                    name="**New Account**",
                    value=f"Created {account_age}ago",
                    inline=False,
                )
            embed.set_author(name=f"{member.name}#{member.discriminator} ({member.id})")
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_footer(text=f"Total Members: {member.guild.member_count}")
            embed.timestamp = datetime.utcnow()
            await logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        gld: DBGuild = self.db.get_log_by_id(member.guild.id)
        logs: discord.TextChannel = self.bot.get_channel(gld.leave_id)
        if logs is None:
            pass
        else:
            account_age = datetime.utcnow() - member.created_at
            time_on_server = datetime.utcnow() - member.joined_at
            embed = discord.Embed(
                title=f"**User Left**",
                description=(
                    f"**Name:** {member.mention}\n"
                    f"**Created on:** {member.created_at.strftime(format_date)}\n"
                    f"**Account age:** {account_age.days} days old\n"
                    f"**Joined on:** {member.joined_at.strftime(format_date)} ({time_on_server.days} days ago)"
                ),
                color=0xD90000,
            )
            embed.set_author(name=f"{member.name}#{member.discriminator} ({member.id})")
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_footer(text=f"Total Members: {member.guild.member_count}")
            embed.timestamp = datetime.utcnow()
            roles = [f"<@&{role.id}>" for role in member.roles[1:]]
            roles_str = " ".join(roles)
            if len(roles) < 1:
                embed.add_field(
                    name=f"**Roles[{len(roles)}]**", value="None", inline=False
                )
            else:
                embed.add_field(
                    name=f"**Roles[{len(roles)}]**", value=f"{roles_str}", inline=False
                )
            await logs.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        gld: DBGuild = self.db.get_log_by_id(after.guild.id)
        logs: discord.TextChannel = self.bot.get_channel(gld.nickname)
        if before.nick == after.nick:
            pass
        elif logs is None:
            pass
        else:
            embed = discord.Embed(
                title=f"**User Nickname Updated**",
                description=(
                    f"**User:** <@!{after.id}>\n\n"
                    f"**Before:** {before.nick}\n"
                    f"**After:** {after.nick}"
                ),
                color=0x22FFC2,
            )
            embed.set_author(name=f"{after.name}#{after.discriminator} ({after.id})")
            embed.set_thumbnail(url=after.avatar_url)
            embed.set_footer(text=f"")
            embed.timestamp = datetime.utcnow()
            self.db.add_lumberjack_message(await logs.send(embed=embed))

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        for guild in self.bot.guilds:
            if after in guild.members:
                gld: DBGuild = self.db.get_log_by_id(guild.id)
                if (
                    before.name != after.name
                    or before.discriminator != after.discriminator
                ):
                    logs: discord.TextChannel = self.bot.get_channel(gld.username)
                    if logs is None:
                        pass
                    else:
                        embed = discord.Embed(
                            title=f"**Username Updated**",
                            description=(
                                f"**User:** <@!{after.id}>\n\n"
                                f"**Before:** {before.name}#{before.discriminator}\n"
                                f"**After:** {after.name}#{after.discriminator}"
                            ),
                            color=0x22FFC2,
                        )
                        embed.set_author(
                            name=f"{after.name}#{after.discriminator} ({after.id})"
                        )
                        embed.set_thumbnail(url=after.avatar_url)
                        embed.set_footer(text=f"")
                        embed.timestamp = datetime.utcnow()
                        self.db.add_lumberjack_message(await logs.send(embed=embed))
                if before.avatar != after.avatar:
                    logs: discord.TextChannel = self.bot.get_channel(gld.avatar)
                    if logs is None:
                        pass
                    else:
                        embed = discord.Embed(
                            title=f"**User avatar Updated**",
                            description=(
                                f"**User:** <@!{after.id}>\n\n"
                                f"Old avatar in thumbnail. New avatar down below"
                            ),
                            color=0x8000FF,
                        )
                        embed.set_author(
                            name=f"{after.name}#{after.discriminator} ({after.id})"
                        )
                        embed.set_thumbnail(url=before.avatar_url)
                        embed.set_footer(text=f"")
                        embed.set_image(url=str(after.avatar_url_as(size=128)))
                        embed.timestamp = datetime.utcnow()
                        self.db.add_lumberjack_message(await logs.send(embed=embed))
