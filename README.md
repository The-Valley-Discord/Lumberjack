# Lumberjack

This bot is designed to be a robust discord logging bot. It can track who joins and leaves your server, deleted and
edited messages, and user profile changes.

### Setup

To run you need python and discord.py

https://github.com/Rapptz/discord.py

### Server Setup

Add your bot token to the empty token file, and you are ready to launch the bot

once launched to change the logging channels use

`lum.log (log type) (here or Channel ID/mention)`

here indicates to make the channel the command is issued in the log channel.

To disable a log use

`lum.clear (log type) `

You need server wide manage message permissions to issue commands.

Valid log types are as following.

1. Join: Member Joins
2. Leave: Member Leaves
3. Delete: Deleted messages
4. Bulk_Delete: Messages that were deleted in bulk. (Think like dyno's ?purge command)
5. Edit: Messages that have been edited and their previous contents.
6. Username: User updates their username
7. Nickname: User updates their server nickname
8. Avatar: User updates their avatar
9. LJ_Log: Lumberjack Log channel. Currently, it is only used for logging when a Tracker is placed on a member.

#### Tracking

The bot can repost any messages sent by a tracked user into a specified channel using the following command.

`lum.track (user name/id) (time in D, H, M) (log channel name/id)`

To remove a tracker use

`lum.untrack (username/id)`

#### Permissions Needed

1. "send message" and "send embed" permissions in the logging channel.
2. "read permissions" of any channel you want logged.
3. "manage guild" and "manage channels" to track which invite was used when a new member joins.


