CREATE TABLE IF NOT EXISTS messages (
            id integer PRIMARY KEY,
            author integer NOT NULL,
            authorname text,
            authordisplayname text,
            channelid integer,
            channelname text,
            guildid integer,
            clean_content text,
            created_at timestamp,
            pfp text,
            attachments integer
          );

CREATE TABLE IF NOT EXISTS attachment_urls (
            message_id integer,
            attachment text
          );

CREATE TABLE IF NOT EXISTS log_channels (
            guildid integer Primary Key,
            joinid integer,
            leaveid integer,
            deleteid integer,
            delete_bulk integer,
            edit integer,
            username integer,
            nickname integer,
            avatar integer,
            stat_member integer,
            ljid integer
          );

CREATE TABLE IF NOT EXISTS tracking (
            userid integer,
            username text,
            guildid integer,
            channelid integer,
            endtime timestamp,
            modid integer,
            modname text
          );

CREATE TABLE IF NOT EXISTS lumberjack_messages (
          message_id integer primary key,
          created_at timestamp
        )