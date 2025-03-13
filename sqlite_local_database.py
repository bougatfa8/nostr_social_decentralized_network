import sqlite3


# Enhanced database initialization function for Nostr
def initialize_database(db_path="nostr_events.db"):
    """Create database tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Last Update table (keep tracking updates)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS last_update (
            id TEXT PRIMARY KEY,
            entity TEXT,
            profile_id TEXT,
            followers_id TEXT,
            room_messages_id TEXT,
            notes_id TEXT,
            timestamp INTEGER,
            refreshed_tables TEXT,
            FOREIGN KEY (profile_id) REFERENCES profiles (pubkey),
            FOREIGN KEY (followers_id) REFERENCES followers (id),
            FOREIGN KEY (room_messages_id) REFERENCES room_messages (id),
            FOREIGN KEY (notes_id) REFERENCES notes (id)
        )
    ''')

    # Create table for relays with profile reference
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relays (
            id TEXT PRIMARY KEY,
            relay_name TEXT,
            relay_url TEXT UNIQUE,
            status INTEGER,  -- 1 for active, 0 for inactive
            description TEXT,
            timestamp INTEGER,
            owner_pubkey TEXT,  -- Added field to link to the profile
            FOREIGN KEY (owner_pubkey) REFERENCES profiles (pubkey)  -- Added foreign key constraint
        )
    ''')

    # Create table for secret
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS secret (
            id TEXT PRIMARY KEY,
            profile_id TEXT,
            nostr_sec TEXT,
            nostr_pub TEXT,
            FOREIGN KEY (profile_id) REFERENCES profiles (pubkey)
        )
    ''')

    # Create table for profiles (metadata kind 0)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            pubkey TEXT PRIMARY KEY,
            name TEXT,
            about TEXT,
            picture TEXT,
            banner TEXT,
            website TEXT,
            lud06 TEXT,
            lud16 TEXT,
            display_name TEXT,
            timestamp INTEGER
        )
    ''')

    # Create table for direct messages (kind 4)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS direct_messages (
            id TEXT PRIMARY KEY,
            sender_pubkey TEXT,
            recipient_pubkey TEXT,
            encrypted_content TEXT,
            decrypted_content TEXT,
            timestamp INTEGER,
            FOREIGN KEY (sender_pubkey) REFERENCES profiles (pubkey),
            FOREIGN KEY (recipient_pubkey) REFERENCES profiles (pubkey)
        )
    ''')

    # Create table for rooms with profile reference
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id TEXT PRIMARY KEY,
            owner_pubkey TEXT,  -- Added field to link to the profile
            direct_message_ids TEXT,
            timestamp INTEGER,
            FOREIGN KEY (owner_pubkey) REFERENCES profiles (pubkey)  -- Added foreign key constraint
        )
    ''')

    # Create table for main notes (notes, kind 1)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,  
            pubkey TEXT,
            content TEXT,
            tags TEXT,
            kind INTEGER,
            timestamp INTEGER,
            FOREIGN KEY (pubkey) REFERENCES profiles (pubkey)  -- Link to the profile's pubkey
        )
    ''')

    # Create table for comments(  kind 1 )
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            pubkey TEXT,
            content TEXT,
            timestamp INTEGER,
            event_id TEXT,  -- Link to the notes (event)
            FOREIGN KEY (pubkey) REFERENCES profiles (pubkey),  -- Link to the profile's pubkey
            FOREIGN KEY (event_id) REFERENCES notes (id)  -- Link to the notes (event)
        )
    ''')

    # Create table for reactions( kind 7 likes content ="+" )
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reactions (
            id TEXT PRIMARY KEY,
            event_id TEXT,  -- event_id references the ID in notes table
            reaction_data TEXT,
            timestamp INTEGER,
            pubkey TEXT,  -- Link to the profile's pubkey
            content TEXT,
            FOREIGN KEY (event_id) REFERENCES notes (id),  -- Link to the notes (event)
            FOREIGN KEY (pubkey) REFERENCES profiles (pubkey)  -- Link to the profile's pubkey
        )
    ''')

    # Create table for followers (kind 3)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS followers (
            id TEXT PRIMARY KEY,
            pubkey TEXT,  -- Link to the profile's pubkey (user)
            follower_pubkey TEXT,  -- Link to the follower's pubkey
            timestamp INTEGER,
            event_id TEXT,  -- Link to the event
            UNIQUE(pubkey, follower_pubkey),  -- Ensure unique relationship
            FOREIGN KEY (pubkey) REFERENCES profiles (pubkey),  -- Link to the profile's pubkey
            FOREIGN KEY (follower_pubkey) REFERENCES profiles (pubkey),  -- Link to the follower's pubkey
            FOREIGN KEY (event_id) REFERENCES notes (id)  -- Link to the notes (event)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")
    return db_path


# Just One function to retrieve data for any table
def fetch_profiles(db_path, table_name):
    """
    Fetches all records from the specified table in the SQLite database.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the query to retrieve all data from the specified table
        cursor.execute(f"SELECT * FROM {table_name}")

        # Fetch all rows
        rows = cursor.fetchall()

        # Close the connection
        conn.close()

        return rows

    except sqlite3.Error as e:
        print(f"Error while connecting to SQLite: {e}")
        return []


# Functions to save data into each table with a single connection


def save_last_update(cursor, id, entity, timestamp, refreshed_tables, profile_id):
    """Save a new record for the last update with the tables that were refreshed."""
    cursor.execute('''
        INSERT INTO last_update (id, entity, timestamp, refreshed_tables, profile_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (id, entity, timestamp, refreshed_tables, profile_id))


def save_relay(cursor, id, relay_url, status, relay_name, description, timestamp, owner_pubkey):
    """Save a new relay to the database."""
    cursor.execute('''
        INSERT INTO relays (id, relay_url, status, relay_name, description, timestamp, owner_pubkey)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (id, relay_url, status, relay_name, description, timestamp, owner_pubkey))


def save_profile(cursor, pubkey, name, about, picture, banner, website, lud06, lud16, display_name, timestamp):
    """Save a new profile to the database."""
    cursor.execute('''
        INSERT INTO profiles (pubkey, name, about, picture, banner, website, lud06, lud16, display_name, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (pubkey, name, about, picture, banner, website, lud06, lud16, display_name, timestamp))


def save_note(cursor, id, pubkey, content, tags, kind, timestamp):
    """Save a new note to the database."""
    cursor.execute('''
        INSERT INTO notes (id, pubkey, content, tags, kind, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (id, pubkey, content, tags, kind, timestamp))


def save_comment(cursor, id, pubkey, content, timestamp, event_id):
    """Save a new comment to the database."""
    cursor.execute('''
        INSERT INTO comments (id, pubkey, content, timestamp, event_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (id, pubkey, content, timestamp, event_id))


def save_reaction(cursor, id, event_id, reaction_data, timestamp, pubkey, content):
    """Save a new reaction to the database."""
    cursor.execute('''
        INSERT INTO reactions (id, event_id, reaction_data, timestamp, pubkey, content)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (id, event_id, reaction_data, timestamp, pubkey, content))


def save_follower(cursor, id, pubkey, follower_pubkey, timestamp, event_id):
    """Save a new follower relationship to the database."""
    cursor.execute('''
        INSERT INTO followers (id, pubkey, follower_pubkey, timestamp, event_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (id, pubkey, follower_pubkey, timestamp, event_id))


def save_direct_message(cursor, id, sender_pubkey, recipient_pubkey, encrypted_content, decrypted_content, timestamp):
    """Save a new direct message to the database."""
    cursor.execute('''
        INSERT INTO direct_messages (id, sender_pubkey, recipient_pubkey, encrypted_content, decrypted_content, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (id, sender_pubkey, recipient_pubkey, encrypted_content, decrypted_content, timestamp))


def save_room(cursor, id, owner_pubkey, direct_message_ids, timestamp):
    """Save a new room to the database."""
    cursor.execute('''
        INSERT INTO rooms (id, owner_pubkey, direct_message_ids, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (id, owner_pubkey, direct_message_ids, timestamp))


# Update functions
def update_last_update(cursor, id, entity, timestamp, refreshed_tables, profile_id):
    """Update the last update record for a specific entity."""
    cursor.execute('''
        UPDATE last_update
        SET entity = ?, timestamp = ?, refreshed_tables = ?, profile_id = ?
        WHERE id = ?
    ''', (entity, timestamp, refreshed_tables, profile_id, id))


def update_relay(cursor, id, relay_url, status, relay_name, description, timestamp, owner_pubkey):
    """Update an existing relay in the database."""
    cursor.execute('''
        UPDATE relays
        SET relay_url = ?, status = ?, relay_name = ?, description = ?, timestamp = ?, owner_pubkey = ?
        WHERE id = ?
    ''', (relay_url, status, relay_name, description, timestamp, owner_pubkey, id))


def update_profile(cursor, pubkey, name, about, picture, banner, website, lud06, lud16, display_name, timestamp):
    """Update an existing profile in the database."""
    cursor.execute('''
        UPDATE profiles
        SET name = ?, about = ?, picture = ?, banner = ?, website = ?, lud06 = ?, lud16 = ?, display_name = ?, timestamp = ?
        WHERE pubkey = ?
    ''', (name, about, picture, banner, website, lud06, lud16, display_name, timestamp, pubkey))


def update_room(cursor, id, owner_pubkey, direct_message_ids, timestamp):
    """Update an existing room in the database."""
    cursor.execute('''
        UPDATE rooms
        SET owner_pubkey = ?, direct_message_ids = ?, timestamp = ?
        WHERE id = ?
    ''', (owner_pubkey, direct_message_ids, timestamp, id))


# Delete functions
def delete_last_update(cursor, id):
    """Delete the last update record by ID."""
    cursor.execute('''
        DELETE FROM last_update WHERE id = ?
    ''', (id,))


def delete_relay(cursor, id):
    """Delete a relay from the database by ID."""
    cursor.execute('''
        DELETE FROM relays WHERE id = ?
    ''', (id,))


def delete_profile(cursor, pubkey):
    """Delete a profile from the database by pubkey."""
    cursor.execute("DELETE FROM profiles WHERE pubkey = ?", (pubkey,))


def delete_note(cursor, id):
    """Delete a note from the database by ID."""
    cursor.execute("DELETE FROM notes WHERE id = ?", (id,))


def delete_comment(cursor, id):
    """Delete a comment from the database by ID."""
    cursor.execute("DELETE FROM comments WHERE id = ?", (id,))


def delete_reaction(cursor, id):
    """Delete a reaction from the database by ID."""
    cursor.execute("DELETE FROM reactions WHERE id = ?", (id,))


def delete_follower(cursor, id):
    """Delete a follower relationship from the database by ID."""
    cursor.execute("DELETE FROM followers WHERE id = ?", (id,))


def delete_direct_message(cursor, id):
    """Delete a direct message from the database by ID."""
    cursor.execute("DELETE FROM direct_messages WHERE id = ?", (id,))


def delete_room(cursor, id):
    """Delete a room from the database by ID."""
    cursor.execute("DELETE FROM rooms WHERE id = ?", (id,))


