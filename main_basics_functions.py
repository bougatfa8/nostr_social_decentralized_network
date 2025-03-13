import binascii
import hashlib
import json
import time
import uuid
import bech32

from collections import defaultdict
from datetime import datetime
from bitcoinlib.keys import HDKey
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.wallets import Wallet
from nostr.event import Event, EventKind
from nostr.key import PrivateKey
from nostr.relay_manager import RelayManager
from pynostr.filters import Filters, FiltersList
from pynostr.relay_manager import RelayManager as PyRelayManager


def generate_passphrase():
    """Generate a random mnemonic passphrase.

    Returns:
        str: A randomly generated mnemonic phrase.
    """
    mnemo = Mnemonic()
    return mnemo.generate()


def derive_seed_from_mnemonic(mnemonic):
    """Derive a seed from a mnemonic phrase.

    Args:
        mnemonic: The mnemonic phrase to derive the seed from.

    Returns:
        bytes: The derived seed.
    """
    mnemo = Mnemonic()
    return mnemo.to_seed(mnemonic)


def generate_nostr_key(seed):
    """Generate a Nostr private key from a seed.

    Args:
        seed: The seed bytes to derive the key from.

    Returns:
        PrivateKey: The generated Nostr private key.
    """
    private_key_bytes = hashlib.sha256(seed).digest()  # 32-byte key derivation
    return PrivateKey(private_key_bytes)


def create_wallet(seed):
    """Create a Bitcoin wallet from a seed.

    Args:
        seed: The seed bytes to create the wallet from.

    Returns:
        tuple: (wallet_name, bitcoin_address, wif_key).
    """
    random_name = str(uuid.uuid4())
    wallet = Wallet.create(random_name, seed)
    address = wallet.addresslist()[0]
    key = wallet.wif()
    return wallet.name, address, key


def convert_hex_to_npub(hex_pubkey):
    """Convert a hexadecimal public key to npub format.

    Args:
        hex_pubkey: The hexadecimal public key to convert.

    Returns:
        str: The npub-encoded public key.

    Raises:
        ValueError: If conversion fails due to invalid input.
        binascii.Error: If hex decoding fails.
    """
    try:
        pubkey_bytes = binascii.unhexlify(hex_pubkey)
        hrp = "npub"
        five_bit_r = bech32.convertbits(pubkey_bytes, 8, 5)
        return bech32.bech32_encode(hrp, five_bit_r)
    except binascii.Error as e:
        raise ValueError(f"Invalid hex public key: {e}")
    except Exception as e:
        raise ValueError(f"Error converting to npub: {e}")


def decode_npub(npub):
    """Decode an npub public key to hexadecimal format.

    Args:
        npub: The npub-encoded public key.

    Returns:
        str: The hexadecimal public key.

    Raises:
        ValueError: If decoding fails or format is invalid.
    """
    try:
        hrp, data = bech32.bech32_decode(npub)
        if hrp != "npub" or data is None:
            raise ValueError("Invalid npub format")
        decoded_bytes = bech32.convertbits(data, 5, 8, False)
        return binascii.hexlify(bytearray(decoded_bytes)).decode()
    except ValueError as e:
        raise ValueError(f"Error decoding npub: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected error decoding npub: {e}")


def convert_timestamp(timestamp):
    """Convert a Unix timestamp to a human-readable UTC string.

    Args:
        timestamp: Unix timestamp in seconds.

    Returns:
        str: Formatted date-time string in UTC (e.g., '2023-01-01 12:00:00 UTC').

    Raises:
        ValueError: If timestamp conversion fails.
    """
    try:
        return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError as e:
        raise ValueError(f"Invalid timestamp: {e}")


def create_profile(relay_manager, private_key, public_key, lud06, name, about, picture, background_image):
    """Create and publish a Nostr user profile with metadata.

    Args:
        relay_manager: The RelayManager instance for publishing events.
        private_key: The PrivateKey object for signing events.
        public_key: The public key object of the Nostr account.
        lud06: The Lightning URL data (LUD06) for the profile.
        name: The display name of the user.
        about: A brief description of the user.
        picture: URL to the user's profile picture.
        background_image: URL to the user's background image.

    Raises:
        ValueError: If profile data is invalid or malformed.
        Exception: If publishing to the relay fails.
    """
    profile_data = {
        "lud06": lud06,
        "name": name,
        "about": about,
        "picture": picture,
        "banner": background_image,
    }
    profile_event = Event(
        public_key=public_key.hex(),
        content=json.dumps(profile_data),
        kind=EventKind.SET_METADATA,
    )
    private_key.sign_event(profile_event)

    try:
        relay_manager.publish_event(profile_event)
        print(f"Profile created: {name}")
    except ValueError as e:
        raise ValueError(f"Invalid profile data: {e}")
    except Exception as e:
        raise Exception(f"Error publishing profile: {e}")


def publish_note(relay_manager, private_key, public_key, content):
    """Publish a text note to Nostr relays.

    Args:
        relay_manager: The RelayManager instance for publishing events.
        private_key: The PrivateKey object for signing events.
        public_key: The public key object of the Nostr account.
        content: The text content of the note.

    Raises:
        ValueError: If content is invalid.
        Exception: If publishing to the relay fails.
    """
    try:
        note_event = Event(
            public_key=public_key.hex(),
            content=content,
            kind=EventKind.TEXT_NOTE,
        )
        private_key.sign_event(note_event)
        relay_manager.publish_event(note_event)
        print(f"Note published: {content} {note_event.id}")
    except ValueError as e:
        raise ValueError(f"Invalid note content: {e}")
    except Exception as e:
        raise Exception(f"Error publishing note: {e}")


def reaction_note(relay_manager, private_key, event_id, reaction):
    """Send a reaction (e.g., like or dislike) to a Nostr event.

    Args:
        relay_manager: The RelayManager instance for publishing events.
        private_key: The PrivateKey object for signing events.
        event_id: The ID of the event to react to.
        reaction: The reaction content (e.g., '+' for like, '-' for dislike).

    Raises:
        ValueError: If reaction or event_id is invalid.
        Exception: If publishing to the relay fails.
    """
    try:
        reaction_event = Event(
            public_key=private_key.public_key.hex(),
            content=reaction,
            kind=7,
            tags=[["e", event_id]],
        )
        private_key.sign_event(reaction_event)
        relay_manager.publish_event(reaction_event)
        print(f"Reaction '{reaction}' sent for event {event_id}")
    except ValueError as e:
        raise ValueError(f"Invalid reaction or event ID: {e}")
    except Exception as e:
        raise Exception(f"Error sending reaction: {e}")


def reply_to_note(relay_manager, private_key, event_id, reply_content):
    """Send a reply to a Nostr event.

    Args:
        relay_manager: The RelayManager instance for publishing events.
        private_key: The PrivateKey object for signing events.
        event_id: The ID of the event to reply to.
        reply_content: The text content of the reply.

    Raises:
        ValueError: If reply_content or event_id is invalid.
        Exception: If publishing to the relay fails.
    """
    try:
        reply_event = Event(
            public_key=private_key.public_key.hex(),
            content=reply_content,
            kind=EventKind.TEXT_NOTE,
            tags=[["e", event_id]],
        )
        private_key.sign_event(reply_event)
        relay_manager.publish_event(reply_event)
        print(f"Reply sent to event {event_id}: {reply_content}")
    except ValueError as e:
        raise ValueError(f"Invalid reply content or event ID: {e}")
    except Exception as e:
        raise Exception(f"Error sending reply: {e}")


def send_message(relay_manager, private_key, public_key, receiver_pubkey, message):
    """Send an encrypted direct message to another Nostr user.

    Args:
        relay_manager: The RelayManager instance used to manage Nostr relays.
        private_key: The PrivateKey object of the sender.
        public_key: The public key object of the sender.
        receiver_pubkey: The public key of the recipient in hex format.
        message: The plaintext message to be sent.
    """
    try:
        encrypted_message = private_key.encrypt_message(message=message, public_key_hex=receiver_pubkey)
        message_event = Event(
            public_key=public_key.hex(),
            content=encrypted_message,
            kind=EventKind.ENCRYPTED_DIRECT_MESSAGE,
            tags=[["p", receiver_pubkey]],
        )
        private_key.sign_event(message_event)
        relay_manager.publish_event(message_event)
        print(f"Message sent to {receiver_pubkey}: {message}")
    except Exception as e:
        print(f"Error sending message: {e}")


def decrypt_msg(private_key, encrypted_message, pubkey_hex):
    """Decrypt a message using the recipient's private key and sender's public key.

    Args:
        private_key: The private key object for decryption.
        encrypted_message: The encrypted message to decrypt.
        pubkey_hex: The sender's public key in hexadecimal format.

    Returns:
        str: Decrypted plaintext message or error message if decryption fails.
    """
    try:
        plaintext = private_key.decrypt_message(
            encoded_message=encrypted_message,
            public_key_hex=pubkey_hex,
        )
        return plaintext
    except Exception as e:
        print(f"Error during decryption: {e}")
        return str(e)


def fetch_events_by_kind(relay_manager, filters, relay_urls):
    """Fetch events of a specific kind from multiple relays without duplication.

    This function retrieves Nostr events matching the provided filters from
    specified relays. It ensures no duplicate events by tracking event IDs in a
    set. Steps:
    1. Create a subscription with the given filters.
    2. Assign a unique ID and subscribe to each relay.
    3. Run the relay manager synchronously to collect events.
    4. Process events, avoiding duplicates by checking against seen IDs.
    5. Return a list of unique event data dictionaries.

    Args:
        relay_manager: The relay manager instance for managing connections.
        filters: A Filters object specifying event criteria (e.g., kinds, authors).
        relay_urls: A list of relay URLs to fetch events from.

    Returns:
        list: List of event data dictionaries, each containing event details.

    Raises:
        Exception: If event fetching fails, returns an empty list with an error message.
    """
    try:
        # Step 1: Wrap filters in a FiltersList for subscription
        subscription_filters = FiltersList([filters])

        # Step 2: Generate a unique subscription ID and subscribe to relays
        subscription_id = str(uuid.uuid4())
        for url in relay_urls:
            relay_manager.add_subscription_on_relay(
                id=subscription_id,
                filters=subscription_filters,
                url=url,
            )

        # Step 3: Synchronously run the relay manager to gather events
        relay_manager.run_sync()

        # Step 4: Collect unique events, avoiding duplication
        events = []
        seen_event_ids = set()  # Tracks IDs to prevent duplicates
        while relay_manager.message_pool.has_events():
            event_msg = relay_manager.message_pool.get_event()
            event_id = event_msg.event.id

            # Only process if event ID hasn't been seen before
            if event_id not in seen_event_ids:
                seen_event_ids.add(event_id)  # Mark as seen
                event_data = {
                    "Event ID": event_id,
                    "Pubkey": event_msg.event.pubkey,
                    "Content": event_msg.event.content,
                    "Kind": event_msg.event.kind,
                    "Tags": event_msg.event.tags,
                    "Created at": convert_timestamp(event_msg.event.created_at),
                }
                events.append(event_data)

        # Step 5: Return the list of unique events
        return events

    except Exception as e:
        # Handle any errors and return an empty list
        print(f"Error fetching events: {e}")
        return []


def organize_chat_messages(sent_msgs, received_msgs, private_key, convert_hex_to_npub_fn, decrypt_msg_fn):
    """Organize and display chat messages (sent and received) by public key.

    Args:
        sent_msgs: List of messages sent by the user.
        received_msgs: List of messages received by the user.
        private_key: The private key for decrypting messages.
        convert_hex_to_npub_fn: Function to convert hex public key to npub.
        decrypt_msg_fn: Function to decrypt encrypted messages.

    Returns:
        dict: Dictionary of rooms with message lists.
    """
    try:
        all_msgs = [{'type': 'sent', **msg} for msg in sent_msgs] + [{'type': 'received', **msg} for msg in received_msgs]

        def get_other_pubkey(msg):
            if msg['type'] == 'sent':
                return next(tag[1] for tag in msg['Tags'] if tag[0] == 'p')
            return msg['Pubkey']

        rooms = defaultdict(list)
        for msg in all_msgs:
            other_pubkey = get_other_pubkey(msg)
            rooms[other_pubkey].append(msg)

        for room in rooms:
            rooms[room].sort(key=lambda x: datetime.strptime(x['Created at'], '%Y-%m-%d %H:%M:%S UTC'))

        for room, messages in rooms.items():
            print(f"Chat with {convert_hex_to_npub_fn(room)}:")
            for msg in messages:
                direction = "Received" if msg['type'] == 'sent' else "Sent"
                print(f"{direction} at {msg['Created at']}: {decrypt_msg_fn(private_key, msg['Content'], room)}")
            print("\n-------------------------------------------------\n")

        return rooms
    except Exception as e:
        print(f"Error organizing chat messages: {e}")
        return {}


def get_chat_for_pubkey(rooms, target_pubkey, convert_hex_to_npub_fn, decrypt_msg_fn, private_key):
    """Fetch chat messages with a specific user identified by their public key.

    Args:
        rooms: Dictionary of chat rooms.
        target_pubkey: The npub public key of the user.
        convert_hex_to_npub_fn: Function to convert hex to npub.
        decrypt_msg_fn: Function to decrypt messages.
        private_key: The private key for decryption.

    Returns:
        dict: Chat data or error message.
    """
    try:
        target_raw_pubkey = decode_npub(target_pubkey)
        if target_raw_pubkey in rooms:
            room_data = {"chat_with": target_pubkey, "messages": []}
            for msg in rooms[target_raw_pubkey]:
                direction = "Received" if msg['type'] == 'sent' else "Sent"
                message_data = {
                    "direction": direction,
                    "timestamp": msg['Created at'],
                    "content": decrypt_msg_fn(private_key, msg['Content'], target_raw_pubkey),
                }
                room_data["messages"].append(message_data)
            return room_data
        return {"error": "No chat found with the specified public key."}
    except Exception as e:
        print(f"Error retrieving chat for {target_pubkey}: {e}")
        return {"error": f"An error occurred while retrieving the chat: {e}"}


def fetch_existing_follows(relay_manager, public_key):
    """Fetch the current contact list (Kind 3) from relays.

    Args:
        relay_manager: The RelayManager instance for managing relays.
        public_key: The public key of the user whose follows are fetched.

    Returns:
        list or dict: List of followed users' public keys or error dict.
    """
    try:
        filters = Filters(authors=[public_key], kinds=[3])
        subscription_id = str(uuid.uuid4())
        subscription_filters = FiltersList([filters])
        relay_manager.add_subscription_on_relay(
            id=subscription_id,
            filters=subscription_filters,
            url="wss://relay.damus.io",
        )
        followed_users = set()
        relay_manager.run_sync()
        while relay_manager.message_pool.has_events():
            event_msg = relay_manager.message_pool.get_event()
            if event_msg.event.kind == 3:
                for tag in event_msg.event.tags:
                    if tag[0] == "p":
                        followed_users.add(tag[1])
        return list(followed_users)
    except Exception as e:
        print(f"Error fetching followed users: {e}")
        return {"error": f"An error occurred while fetching followed users: {e}"}


def update_follow_list(existing_follows, relay_manager, relay_urls, private_key, public_key, pubkey_to_toggle):
    """Toggle follow/unfollow for a given public key.

    Args:
        existing_follows: List of currently followed users' public keys.
        relay_manager: The RelayManager instance for managing relays.
        relay_urls: List of relay URLs to publish the update.
        private_key: The PrivateKey object for signing.
        public_key: The public key of the user performing the action.
        pubkey_to_toggle: The public key to follow or unfollow.
    """
    try:
        if pubkey_to_toggle in existing_follows:
            existing_follows.remove(pubkey_to_toggle)
            print(f"❌ Unfollowing {pubkey_to_toggle}")
        else:
            existing_follows.append(pubkey_to_toggle)
            print(f"✅ Following {pubkey_to_toggle}")
        contact_event = Event(
            public_key=public_key.hex(),
            kind=EventKind.CONTACTS,
            content="",
            created_at=int(time.time()),
            tags=[["p", pk] for pk in existing_follows],
        )
        private_key.sign_event(contact_event)
        for url in relay_urls:
            try:
                relay_manager.publish_event(contact_event)
                print(f"✅📢 Updated contact list successfully on {url}")
            except Exception as e:
                print(f"❌📢 Error updating contact list on {url}: {e}")
    except Exception as e:
        print(f"❌ Error updating the follow list: {e}")

def delete_event(relay_manager, private_key, event_id):
    """Delete a specific event by publishing a delete event.

    Args:
        relay_manager: The RelayManager instance for publishing events.
        private_key: The PrivateKey object for signing.
        event_id: The ID of the event to delete.

    Returns:
        bool or dict: True if successful, error dict otherwise.
    """
    try:
        delete_event_obj = Event(
            public_key=private_key.public_key.hex(),
            kind=EventKind.DELETE,
            content=f"Delete event with ID: {event_id}",
            created_at=int(time.time()),
            tags=[['e', event_id]],
        )
        private_key.sign_event(delete_event_obj)
        relay_manager.publish_event(delete_event_obj)
        print(f"Delete event published for event ID: {event_id}")
        return True
    except Exception as e:
        print(f"Error deleting event with ID {event_id}: {e}")
        return {"error": f"An error occurred while deleting the event: {e}"}




def main():
    """Main function to demonstrate Nostr and Bitcoin wallet functionality."""
    # Step 1: Generate a random seed phrase
    seed_phrase = generate_passphrase()
    print(f"Seed Phrase: {seed_phrase}")

    # Step 2: Derive the seed from the seed phrase
    seed = derive_seed_from_mnemonic(seed_phrase)

    # Step 3: Generate Nostr nsec key
    nostr_private_key = generate_nostr_key(seed)
    print(f"Nostr Private Key (nsec): {nostr_private_key.bech32()}")
    print(f"Nostr Public Key: {nostr_private_key.public_key.bech32()}")

    # Step 4: Generate Bitcoin wallet
    wallet_name, bitcoin_address, bitcoin_key = create_wallet(seed)
    print(f"Bitcoin Wallet Name: {wallet_name}")
    print(f"Bitcoin Address: {bitcoin_address}")
    print(f"Bitcoin WIF Key (ZPUB): {bitcoin_key}")

    # Initialize RelayManager and add relays
    relay_urls = [
        "wss://strfry.iris.to",
        "wss://relay.damus.io",
        "wss://relay.nostr.band",
        "wss://relay.snort.social",
    ]
    nostr_relay_manager = RelayManager()

    for url in relay_urls:
        nostr_relay_manager.add_relay(url)

    nostr_relay_manager.open_connections()
    time.sleep(1.25)  # Allow time for connections to establish

    # Using a private key to generate the corresponding public key
    private_key = PrivateKey.from_nsec("nsec1ksv944t63jemxx8hxc69mclgfea4qpcaw3y8rvhtra0apta85k4sx4pnga")
    # private_key = PrivateKey.from_nsec(nostr_private_key.bech32())
    public_key = private_key.public_key
    print(f"Public Key (npub): {public_key.bech32()}")

    # Create/update profile
    create_profile(
        nostr_relay_manager,
        private_key,
        public_key,
        bitcoin_address,
        wallet_name,
        "bitcoin_key.address()",
        "https://thumbs.dreamstime.com/b/childish-sweet-dreams-silhouette-happy-little-boy-jumping-to-sky-catch-moon-131106224.jpg",
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRilZ_RB4C_i6s1WJp927F0dMHCnwYK6ByuAg&s"
    )
    # Publish a note
    note_content = "Ahmed Testing, Nostr! This is my first note."
    # publish_note(nostr_relay_manager, private_key, public_key, note_content)

    # React to a note
    event_id = "32cf229e5e46e47a1d3b4eb90b7058c6bef8f8ae6ac32c1ccdb741a815d37c40"
    # reaction_note(nostr_relay_manager, private_key, event_id, "+️")

    # Reply to a note
    reply_content = "Hi this is my comment, that's a great post!"
    # reply_to_note(nostr_relay_manager, private_key, event_id, reply_content)


    # Send a direct message
    receiver_pubkey = decode_npub("npub19pu67y0rllpwtrh6dvd90tvfhsh3a2ys460edqvrlfssxyk55q5sk9rwdw")
    message = "coucou"
    # send_message(nostr_relay_manager, private_key, public_key, receiver_pubkey, message)

    # Decrypt message
    encrypted_message = "EXAMPLE/hash_data"
    message = decrypt_msg(private_key, encrypted_message, public_key.hex())


    # Initialize PyNostr RelayManager for additional functionality
    pynostr_relay_manager = PyRelayManager()
    for url in relay_urls:
        pynostr_relay_manager.add_relay(url)

    # Retrieve profile metadata
    filters = Filters(
        authors=[decode_npub("npub19pu67y0rllpwtrh6dvd90tvfhsh3a2ys460edqvrlfssxyk55q5sk9rwdw")],
        # since = int(time.time()) - 3600 * 24 * 30  # (OPTIONAL) Timestamp for the last 30 days
        # until = int(time.time()) - 3600 * 24 * 10,  # (OPTIONAL) Timestamp for the last 10 days
        limit=100,
        kinds=[0]
    )
    # events = fetch_events_by_kind(pynostr_relay_manager, filters, relay_urls)
    # print(f"Metadata {events}")

    # Retrieve profile Notes
    filters = Filters(
        authors=[decode_npub("npub19pu67y0rllpwtrh6dvd90tvfhsh3a2ys460edqvrlfssxyk55q5sk9rwdw")],
        limit=100,
        kinds=[1]
    )
    # events = fetch_events_by_kind(pynostr_relay_manager, filters, relay_urls)
    # print(f"Notes {events}")

    # Retrieve comments and reactions for a note by its ID
    note_events_id= "note_Id"
    filters = Filters(
        kinds=[1, 7],  # Comments (1) and reactions (7)
        event_refs=note_events_id,
    )
    # event_notes = fetch_events_by_kind(pynostr_relay_manager, filters, relay_urls)
    # print(f"Found {len(event_notes)} comments/reactions for notes.")

    # Retrieve sent and received messages
    filters_sent = Filters(
        authors=[public_key.hex()],
        since=int(time.time()) - 3600 * 24 * 30,
        limit=100,
        kinds=[4]
    )
    sent_msgs = fetch_events_by_kind(pynostr_relay_manager, filters_sent, relay_urls)

    filters_received = Filters(
        pubkey_refs=[public_key.hex()],
        since=int(time.time()) - 3600 * 24 * 30,
        limit=100,
        kinds=[4]
    )
    received_msgs = fetch_events_by_kind(pynostr_relay_manager, filters_received, relay_urls)

    # Organize chats
    # rooms = organize_chat_messages(sent_msgs, received_msgs, private_key, convert_hex_to_npub, decrypt_msg)

    # Get chat for specific user
    # target_pubkey = "npub1kl708ucvrkwxlzvkxv03aue4r5auvxw828y5fgg6759exxq032esqmt7ul"
    # chat_data = get_chat_for_pubkey(rooms, target_pubkey, decode_npub, decrypt_msg, private_key)
    # print(f"Chat Data: {chat_data}")

    # Fetch and display followed users
    existing_follows = fetch_existing_follows(pynostr_relay_manager, public_key.hex())
    print(f"Existing follows: {existing_follows}")
    if public_key in existing_follows:
        existing_follows.remove(public_key)

    # Count and display followers
    total = 0
    for i in existing_follows:
        total += 1
        print(f"{i}")
    print(f"Total follows: {total}")

    # follow/unfollow a user
    new_follow_pubkey = decode_npub("npub17u5dneh8qjp43ecfxr6u5e9sjamsmxyuekrg2nlxrrk6nj9rsyrqywt4tp")
    # update_follow_list(existing_follows, nostr_relay_manager, relay_urls, private_key, public_key, new_follow_pubkey)

    # delete an event
    event_id = "35f828c671b0d928f7e2e946cace31983c3de7e006621106f952271ac3126576"
    # delete_event(relay_manager, private_key, event_id)



if __name__ == "__main__":
    main()
