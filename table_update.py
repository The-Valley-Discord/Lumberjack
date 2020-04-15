import sqlite3

conn = sqlite3.connect("log.db")

c = conn.cursor()

c.execute(
    """ ALTER TABLE log_channels
           ADD COLUMN ljid integer
            """
)
conn.close()
