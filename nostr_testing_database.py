import sqlite3
import random
import uuid
from faker import Faker
import time
import json
import os
from datetime import datetime
import pytest

# Add these fixture definitions at the top of your file
@pytest.fixture
def conn():
    """Fixture to provide a database connection."""
    conn, _ = setup_test_db()
    yield conn
    conn.close()

@pytest.fixture
def cursor(conn):
    """Fixture to provide a database cursor."""
    return conn.cursor()
# Import your database functions
from sqlite_local_database import (
    initialize_database,
    save_last_update, update_last_update, delete_last_update,
    save_relay, update_relay, delete_relay,
    save_profile, update_profile, delete_profile,
    save_note, delete_note,
    save_comment, delete_comment,
    save_reaction, delete_reaction,
    save_follower, delete_follower,
    save_direct_message, delete_direct_message,
    save_room, update_room, delete_room
)

# Initialize Faker
fake = Faker()

# Create a test database path
TEST_DB_PATH = "nostr_test.db"

def setup_test_db():
    """Set up a test database and return the connection and cursor."""
    # Remove test database if it exists
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # Initialize the database
    initialize_database(TEST_DB_PATH)

    # Connect to the database
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()

    return conn, cursor

def generate_fake_pubkey():
    """Generate a fake Nostr public key."""
    return f"npub1{fake.sha256()[:58]}"

def run_all_tests():
    """Run all tests for the database tables."""
    # Set up test database
    conn, cursor = setup_test_db()

    try:
        # Run tests for all tables
        test_profiles(conn, cursor)
        test_relays(conn, cursor)
        test_notes(conn, cursor)
        test_comments(conn, cursor)
        test_reactions(conn, cursor)
        test_followers(conn, cursor)
        test_direct_messages(conn, cursor)
        test_rooms(conn, cursor)
        test_last_update(conn, cursor)

        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")

    finally:
        # Close connection
        conn.close()

def test_profiles(conn, cursor):
    """Test CRUD operations for profiles table."""
    print("\n🧪 Testing profiles table...")

    # Generate fake profile data
    pubkey = generate_fake_pubkey()
    name = fake.user_name()
    about = fake.text(max_nb_chars=200)
    picture = fake.image_url()
    banner = fake.image_url()
    website = fake.url()
    lud06 = fake.sha256()[:56]
    lud16 = f"{fake.user_name()}@{fake.domain_name()}"
    display_name = fake.name()
    timestamp = int(time.time())

    # Test CREATE
    save_profile(cursor, pubkey, name, about, picture, banner, website, lud06, lud16, display_name, timestamp)
    conn.commit()

    # Test READ
    cursor.execute("SELECT * FROM profiles WHERE pubkey = ?", (pubkey,))
    profile = cursor.fetchone()

    assert profile is not None, "Profile not found after creation"
    assert profile[0] == pubkey, "Profile pubkey doesn't match"
    assert profile[1] == name, "Profile name doesn't match"

    print("  ✓ CREATE and READ operations passed for profiles")

    # Test UPDATE
    new_name = fake.user_name()
    new_about = fake.text(max_nb_chars=200)
    new_timestamp = int(time.time())

    update_profile(cursor, pubkey, new_name, new_about, picture, banner, website, lud06, lud16, display_name, new_timestamp)
    conn.commit()

    cursor.execute("SELECT name, about FROM profiles WHERE pubkey = ?", (pubkey,))
    updated_profile = cursor.fetchone()

    assert updated_profile[0] == new_name, "Profile name wasn't updated"
    assert updated_profile[1] == new_about, "Profile about wasn't updated"

    print("  ✓ UPDATE operation passed for profiles")

    # Test DELETE
    delete_profile(cursor, pubkey)
    conn.commit()

    cursor.execute("SELECT * FROM profiles WHERE pubkey = ?", (pubkey,))
    deleted_profile = cursor.fetchone()

    assert deleted_profile is None, "Profile wasn't deleted"

    print("  ✓ DELETE operation passed for profiles")

def test_relays(conn, cursor):
    """Test CRUD operations for relays table."""
    print("\n🧪 Testing relays table...")

    # First create a profile for foreign key constraint
    profile_pubkey = generate_fake_pubkey()
    save_profile(cursor, profile_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    # Generate fake relay data
    relay_id = str(uuid.uuid4())
    relay_url = f"wss://{fake.domain_name()}"
    status = 1
    relay_name = fake.company()
    description = fake.text(max_nb_chars=200)
    timestamp = int(time.time())

    # Test CREATE
    save_relay(cursor, relay_id, relay_url, status, relay_name, description, timestamp, profile_pubkey)
    conn.commit()

    # Test READ
    cursor.execute("SELECT * FROM relays WHERE id = ?", (relay_id,))
    relay = cursor.fetchone()

    assert relay is not None, "Relay not found after creation"
    assert relay[0] == relay_id, "Relay ID doesn't match"
    assert relay[1] == relay_name, "Relay name doesn't match"
    assert relay[2] == relay_url, "Relay URL doesn't match"

    print("  ✓ CREATE and READ operations passed for relays")

    # Test UPDATE
    new_relay_name = fake.company()
    new_description = fake.text(max_nb_chars=200)
    new_timestamp = int(time.time())

    update_relay(cursor, relay_id, relay_url, status, new_relay_name, new_description, new_timestamp, profile_pubkey)
    conn.commit()

    cursor.execute("SELECT relay_name, description FROM relays WHERE id = ?", (relay_id,))
    updated_relay = cursor.fetchone()

    assert updated_relay[0] == new_relay_name, "Relay name wasn't updated"
    assert updated_relay[1] == new_description, "Relay description wasn't updated"

    print("  ✓ UPDATE operation passed for relays")

    # Test DELETE
    delete_relay(cursor, relay_id)
    conn.commit()

    cursor.execute("SELECT * FROM relays WHERE id = ?", (relay_id,))
    deleted_relay = cursor.fetchone()

    assert deleted_relay is None, "Relay wasn't deleted"

    print("  ✓ DELETE operation passed for relays")

def test_notes(conn, cursor):
    """Test CRUD operations for notes table."""
    print("\n🧪 Testing notes table...")

    # First create a profile for foreign key constraint
    profile_pubkey = generate_fake_pubkey()
    save_profile(cursor, profile_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    # Generate fake note data
    note_id = str(uuid.uuid4())
    content = fake.text(max_nb_chars=280)
    tags = json.dumps([["t", fake.word()], ["t", fake.word()]])
    kind = 1
    timestamp = int(time.time())

    # Test CREATE
    save_note(cursor, note_id, profile_pubkey, content, tags, kind, timestamp)
    conn.commit()

    # Test READ
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()

    assert note is not None, "Note not found after creation"
    assert note[0] == note_id, "Note ID doesn't match"
    assert note[1] == profile_pubkey, "Note pubkey doesn't match"
    assert note[2] == content, "Note content doesn't match"

    print("  ✓ CREATE and READ operations passed for notes")

    # Test DELETE
    delete_note(cursor, note_id)
    conn.commit()

    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    deleted_note = cursor.fetchone()

    assert deleted_note is None, "Note wasn't deleted"

    print("  ✓ DELETE operation passed for notes")

def test_comments(conn, cursor):
    """Test CRUD operations for comments table."""
    print("\n🧪 Testing comments table...")

    # First create a profile and a note for foreign key constraints
    profile_pubkey = generate_fake_pubkey()
    save_profile(cursor, profile_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    note_id = str(uuid.uuid4())
    save_note(cursor, note_id, profile_pubkey, fake.text(), json.dumps([]), 1, int(time.time()))

    # Generate fake comment data
    comment_id = str(uuid.uuid4())
    content = fake.text(max_nb_chars=280)
    timestamp = int(time.time())

    # Test CREATE
    save_comment(cursor, comment_id, profile_pubkey, content, timestamp, note_id)
    conn.commit()

    # Test READ
    cursor.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
    comment = cursor.fetchone()

    assert comment is not None, "Comment not found after creation"
    assert comment[0] == comment_id, "Comment ID doesn't match"
    assert comment[1] == profile_pubkey, "Comment pubkey doesn't match"
    assert comment[2] == content, "Comment content doesn't match"
    assert comment[4] == note_id, "Comment event_id doesn't match"

    print("  ✓ CREATE and READ operations passed for comments")

    # Test DELETE
    delete_comment(cursor, comment_id)
    conn.commit()

    cursor.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
    deleted_comment = cursor.fetchone()

    assert deleted_comment is None, "Comment wasn't deleted"

    print("  ✓ DELETE operation passed for comments")

def test_reactions(conn, cursor):
    """Test CRUD operations for reactions table."""
    print("\n🧪 Testing reactions table...")

    # First create a profile and a note for foreign key constraints
    profile_pubkey = generate_fake_pubkey()
    save_profile(cursor, profile_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    note_id = str(uuid.uuid4())
    save_note(cursor, note_id, profile_pubkey, fake.text(), json.dumps([]), 1, int(time.time()))

    # Generate fake reaction data
    reaction_id = str(uuid.uuid4())
    reaction_data = json.dumps({"type": "like"})
    timestamp = int(time.time())
    content = "+"  # Like

    # Test CREATE
    save_reaction(cursor, reaction_id, note_id, reaction_data, timestamp, profile_pubkey, content)
    conn.commit()

    # Test READ
    cursor.execute("SELECT * FROM reactions WHERE id = ?", (reaction_id,))
    reaction = cursor.fetchone()

    assert reaction is not None, "Reaction not found after creation"
    assert reaction[0] == reaction_id, "Reaction ID doesn't match"
    assert reaction[1] == note_id, "Reaction event_id doesn't match"

    print("  ✓ CREATE and READ operations passed for reactions")

    # Test DELETE
    delete_reaction(cursor, reaction_id)
    conn.commit()

    cursor.execute("SELECT * FROM reactions WHERE id = ?", (reaction_id,))
    deleted_reaction = cursor.fetchone()

    assert deleted_reaction is None, "Reaction wasn't deleted"

    print("  ✓ DELETE operation passed for reactions")

def test_followers(conn, cursor):
    """Test CRUD operations for followers table."""
    print("\n🧪 Testing followers table...")

    # First create two profiles and a note for foreign key constraints
    profile_pubkey = generate_fake_pubkey()
    follower_pubkey = generate_fake_pubkey()

    save_profile(cursor, profile_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    save_profile(cursor, follower_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    note_id = str(uuid.uuid4())
    save_note(cursor, note_id, profile_pubkey, fake.text(), json.dumps([]), 3, int(time.time()))

    # Generate fake follower data
    follower_id = str(uuid.uuid4())
    timestamp = int(time.time())

    # Test CREATE
    save_follower(cursor, follower_id, profile_pubkey, follower_pubkey, timestamp, note_id)
    conn.commit()

    # Test READ
    cursor.execute("SELECT * FROM followers WHERE id = ?", (follower_id,))
    follower = cursor.fetchone()

    assert follower is not None, "Follower not found after creation"
    assert follower[0] == follower_id, "Follower ID doesn't match"
    assert follower[1] == profile_pubkey, "Follower pubkey doesn't match"
    assert follower[2] == follower_pubkey, "Follower follower_pubkey doesn't match"

    print("  ✓ CREATE and READ operations passed for followers")

    # Test DELETE
    delete_follower(cursor, follower_id)
    conn.commit()

    cursor.execute("SELECT * FROM followers WHERE id = ?", (follower_id,))
    deleted_follower = cursor.fetchone()

    assert deleted_follower is None, "Follower wasn't deleted"

    print("  ✓ DELETE operation passed for followers")

def test_direct_messages(conn, cursor):
    """Test CRUD operations for direct_messages table."""
    print("\n🧪 Testing direct_messages table...")

    # First create two profiles for foreign key constraints
    sender_pubkey = generate_fake_pubkey()
    recipient_pubkey = generate_fake_pubkey()

    save_profile(cursor, sender_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    save_profile(cursor, recipient_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    # Generate fake direct message data
    dm_id = str(uuid.uuid4())
    encrypted_content = fake.sha256()
    decrypted_content = fake.text(max_nb_chars=280)
    timestamp = int(time.time())

    # Test CREATE
    save_direct_message(cursor, dm_id, sender_pubkey, recipient_pubkey, encrypted_content, decrypted_content, timestamp)
    conn.commit()

    # Test READ
    cursor.execute("SELECT * FROM direct_messages WHERE id = ?", (dm_id,))
    dm = cursor.fetchone()

    assert dm is not None, "Direct message not found after creation"
    assert dm[0] == dm_id, "Direct message ID doesn't match"
    assert dm[1] == sender_pubkey, "Direct message sender_pubkey doesn't match"
    assert dm[2] == recipient_pubkey, "Direct message recipient_pubkey doesn't match"

    print("  ✓ CREATE and READ operations passed for direct_messages")

    # Test DELETE
    delete_direct_message(cursor, dm_id)
    conn.commit()

    cursor.execute("SELECT * FROM direct_messages WHERE id = ?", (dm_id,))
    deleted_dm = cursor.fetchone()

    assert deleted_dm is None, "Direct message wasn't deleted"

    print("  ✓ DELETE operation passed for direct_messages")

def test_rooms(conn, cursor):
    """Test CRUD operations for rooms table."""
    print("\n🧪 Testing rooms table...")

    # First create a profile for foreign key constraint
    profile_pubkey = generate_fake_pubkey()
    save_profile(cursor, profile_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    # Generate fake room data
    room_id = str(uuid.uuid4())
    direct_message_ids = json.dumps([str(uuid.uuid4()), str(uuid.uuid4())])
    timestamp = int(time.time())

    # Test CREATE
    save_room(cursor, room_id, profile_pubkey, direct_message_ids, timestamp)
    conn.commit()

    # Test READ
    cursor.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    room = cursor.fetchone()

    assert room is not None, "Room not found after creation"
    assert room[0] == room_id, "Room ID doesn't match"
    assert room[1] == profile_pubkey, "Room owner_pubkey doesn't match"

    print("  ✓ CREATE and READ operations passed for rooms")

    # Test UPDATE
    new_direct_message_ids = json.dumps([str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())])
    new_timestamp = int(time.time())

    update_room(cursor, room_id, profile_pubkey, new_direct_message_ids, new_timestamp)
    conn.commit()

    cursor.execute("SELECT direct_message_ids FROM rooms WHERE id = ?", (room_id,))
    updated_room = cursor.fetchone()

    assert updated_room[0] == new_direct_message_ids, "Room direct_message_ids wasn't updated"

    print("  ✓ UPDATE operation passed for rooms")

    # Test DELETE
    delete_room(cursor, room_id)
    conn.commit()

    cursor.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    deleted_room = cursor.fetchone()

    assert deleted_room is None, "Room wasn't deleted"

    print("  ✓ DELETE operation passed for rooms")

def test_last_update(conn, cursor):
    """Test CRUD operations for last_update table."""
    print("\n🧪 Testing last_update table...")

    # First create a profile for foreign key constraint
    profile_pubkey = generate_fake_pubkey()
    save_profile(cursor, profile_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    # Generate fake last_update data
    update_id = str(uuid.uuid4())
    entity = "profiles"
    timestamp = int(time.time())
    refreshed_tables = json.dumps(["profiles", "followers"])

    # Test CREATE
    save_last_update(cursor, update_id, entity, timestamp, refreshed_tables, profile_pubkey)
    conn.commit()

    # Test READ
    cursor.execute("SELECT * FROM last_update WHERE id = ?", (update_id,))
    last_update = cursor.fetchone()

    assert last_update is not None, "Last update not found after creation"
    assert last_update[0] == update_id, "Last update ID doesn't match"
    assert last_update[1] == entity, "Last update entity doesn't match"

    print("  ✓ CREATE and READ operations passed for last_update")

    # Test UPDATE
    new_entity = "notes"
    new_timestamp = int(time.time())
    new_refreshed_tables = json.dumps(["notes", "comments"])

    update_last_update(cursor, update_id, new_entity, new_timestamp, new_refreshed_tables, profile_pubkey)
    conn.commit()

    cursor.execute("SELECT entity, refreshed_tables FROM last_update WHERE id = ?", (update_id,))
    updated_last_update = cursor.fetchone()

    assert updated_last_update[0] == new_entity, "Last update entity wasn't updated"
    assert updated_last_update[1] == new_refreshed_tables, "Last update refreshed_tables wasn't updated"

    print("  ✓ UPDATE operation passed for last_update")

    # Test DELETE
    delete_last_update(cursor, update_id)
    conn.commit()

    cursor.execute("SELECT * FROM last_update WHERE id = ?", (update_id,))
    deleted_last_update = cursor.fetchone()

    assert deleted_last_update is None, "Last update wasn't deleted"

    print("  ✓ DELETE operation passed for last_update")

def print_test_records():
    """Print example records for each table."""
    print("\n📊 Sample Test Records:")

    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()

    # Generate sample data for all tables
    run_sample_data_generation(conn, cursor)

    # Print records from each table
    tables = [
        "profiles", "relays", "notes", "comments",
        "reactions", "followers", "direct_messages",
        "rooms", "last_update"
    ]

    for table in tables:
        cursor.execute(f"SELECT * FROM {table} LIMIT 1")
        record = cursor.fetchone()
        if record:
            print(f"\n{table.upper()} RECORD:")
            # Get column names
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]

            # Print each column with its value
            for i, col in enumerate(columns):
                if i < len(record):
                    print(f"  {col}: {record[i]}")
        else:
            print(f"\n{table.upper()} - No records found")

    conn.close()

def run_sample_data_generation(conn, cursor):
    """Generate sample data for all tables."""
    # Create profiles
    profile1_pubkey = generate_fake_pubkey()
    profile2_pubkey = generate_fake_pubkey()

    save_profile(cursor, profile1_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    save_profile(cursor, profile2_pubkey, fake.user_name(), fake.text(), fake.image_url(),
                fake.image_url(), fake.url(), fake.sha256()[:56],
                f"{fake.user_name()}@{fake.domain_name()}", fake.name(), int(time.time()))

    # Create a relay
    relay_id = str(uuid.uuid4())
    save_relay(cursor, relay_id, f"wss://{fake.domain_name()}", 1,
              fake.company(), fake.text(max_nb_chars=200), int(time.time()), profile1_pubkey)

    # Create a note
    note_id = str(uuid.uuid4())
    save_note(cursor, note_id, profile1_pubkey, fake.text(max_nb_chars=280),
             json.dumps([["t", fake.word()]]), 1, int(time.time()))

    # Create a comment
    comment_id = str(uuid.uuid4())
    save_comment(cursor, comment_id, profile2_pubkey, fake.text(max_nb_chars=280),
                int(time.time()), note_id)

    # Create a reaction
    reaction_id = str(uuid.uuid4())
    save_reaction(cursor, reaction_id, note_id, json.dumps({"type": "like"}),
                 int(time.time()), profile2_pubkey, "+")

    # Create a follower
    follower_id = str(uuid.uuid4())
    follower_note_id = str(uuid.uuid4())
    save_note(cursor, follower_note_id, profile2_pubkey, "", json.dumps([]), 3, int(time.time()))
    save_follower(cursor, follower_id, profile1_pubkey, profile2_pubkey,
                 int(time.time()), follower_note_id)

    # Create a direct message
    dm_id = str(uuid.uuid4())
    save_direct_message(cursor, dm_id, profile1_pubkey, profile2_pubkey,
                       fake.sha256(), fake.text(max_nb_chars=280), int(time.time()))

    # Create a room
    room_id = str(uuid.uuid4())
    save_room(cursor, room_id, profile1_pubkey, json.dumps([dm_id]), int(time.time()))

    # Create a last_update
    update_id = str(uuid.uuid4())
    save_last_update(cursor, update_id, "profiles", int(time.time()),
                    json.dumps(["profiles"]), profile1_pubkey)

    conn.commit()

if __name__ == "__main__":
    # Run all tests
    run_all_tests()

    # Print sample records
    print_test_records()

    print("\n✨ Test script completed! Check the results above.")
