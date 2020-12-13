# Lumberjack
Discord Logging bot
To run you need python and discord.py

https://github.com/Rapptz/discord.py

Add your bot token to the empty token file, and you are ready to launch the bot

once launched to change the logging channels use

lum.log (log type) (here or Channel ID/mention)

here indicates to make the channel the command is issued in the log channel.

To disable a log use

lum.clear (log type) 

You need manage server permissions to issue commands.

Valid log types are as following.
Join, Leave, Delete, Bulk_Delete, Edit, Username, Nickname, Avatar, or Stats

to track a specific users messages use 

lum.track (user mention/id) (time in D, H, M) (log channel mention/id)

The bot will need "send message" and "send embed" permissions in the logging channel.

The bot will need "read permissions" of any channel you want logged.

The bot will need "manage guild" and "manage channels" to track which invite was used when a new member joins.


