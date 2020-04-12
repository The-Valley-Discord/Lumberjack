from discord.ext import commands


def has_permissions():
    """
    Check if user has the permissions to manage the guild

    :return: (bool)
    """

    def predicate(ctx):
        return ctx.author.guild_permissions.manage_guild is True

    return commands.check(predicate)
