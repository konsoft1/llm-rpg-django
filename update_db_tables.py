import sqlite3

def update_character_table():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Add columns to the game_character table
    try:
        cursor.execute("ALTER TABLE game_character ADD COLUMN level INTEGER")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' not in str(e):
            raise

    try:
        cursor.execute("ALTER TABLE game_character ADD COLUMN xp INTEGER")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' not in str(e):
            raise

    try:
        cursor.execute("ALTER TABLE game_character ADD COLUMN starting_zone_id INTEGER")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' not in str(e):
            raise

    try:
        cursor.execute("ALTER TABLE game_character ADD COLUMN starting_subzone_id INTEGER")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' not in str(e):
            raise

    try:
        cursor.execute("ALTER TABLE game_character ADD COLUMN location_id INTEGER")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' not in str(e):
            raise

    conn.commit()
    conn.close()

def update_zone_table():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Ensure columns match the current model
    cursor.execute("PRAGMA table_info(game_zone)")
    columns = [info[1] for info in cursor.fetchall()]

    if 'name' not in columns:
        cursor.execute("ALTER TABLE game_zone ADD COLUMN name TEXT")
    if 'description' not in columns:
        cursor.execute("ALTER TABLE game_zone ADD COLUMN description TEXT")
    if 'primary_races' not in columns:
        cursor.execute("ALTER TABLE game_zone ADD COLUMN primary_races TEXT")
    if 'primary_classes' not in columns:
        cursor.execute("ALTER TABLE game_zone ADD COLUMN primary_classes TEXT")
    if 'zone_type' not in columns:
        cursor.execute("ALTER TABLE game_zone ADD COLUMN zone_type TEXT")
    if 'last_updated' not in columns:
        cursor.execute("ALTER TABLE game_zone ADD COLUMN last_updated NUM")
    if 'version' not in columns:
        cursor.execute("ALTER TABLE game_zone ADD COLUMN version INTEGER")

    conn.commit()
    conn.close()

def update_subzone_table():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Ensure columns match the current model
    cursor.execute("PRAGMA table_info(game_subzone)")
    columns = [info[1] for info in cursor.fetchall()]

    if 'name' not in columns:
        cursor.execute("ALTER TABLE game_subzone ADD COLUMN name TEXT")
    if 'description' not in columns:
        cursor.execute("ALTER TABLE game_subzone ADD COLUMN description TEXT")
    if 'primary_races' not in columns:
        cursor.execute("ALTER TABLE game_subzone ADD COLUMN primary_races TEXT")
    if 'primary_classes' not in columns:
        cursor.execute("ALTER TABLE game_subzone ADD COLUMN primary_classes TEXT")
    if 'zone_type' not in columns:
        cursor.execute("ALTER TABLE game_subzone ADD COLUMN zone_type TEXT")
    if 'zone_id' not in columns:
        cursor.execute("ALTER TABLE game_subzone ADD COLUMN zone_id INTEGER")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_character_table()
    update_zone_table()
    update_subzone_table()
