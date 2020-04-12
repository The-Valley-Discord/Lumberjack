-- Stores messages
CREATE TABLE IF NOT EXISTS messages (
  id integer PRIMARY KEY,
  author integer NOT NULL,
  authorname text,
  authordisplayname text,
  channelid integer,
  channelname text,
  guildid integer,
  clean_content text, -- TODO: What is this?
  created_at timestamp,
  pfp text,
  attachments integer -- RELATIONSHIP: attachment_urls
);

-- URLs of attachments in messages
CREATE TABLE IF NOT EXISTS attachment_urls (
  message_id integer,
  attachment text
);

-- Logging channel IDs for each guild
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
  stat_member integer
);

-- User tracking to track suss users
CREATE TABLE IF NOT EXISTS tracking (
  userid integer Primary Key,
  username text,
  guildid integer,
  channelid integer,
  endtime timestamp,
  modid integer,
  modname text
);