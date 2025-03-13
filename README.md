# Nostr Util Functions

A comprehensive Python toolkit that bridges Nostr protocol functionality with Bitcoin wallet management. This library provides a seamless experience for developers looking to integrate decentralized social networking with cryptocurrency capabilities.
## NIPS [0,1,3,4,7]
## 🌟 Features

- **Identity Management**
  - Generate cryptographic keys and wallets from mnemonic seed phrases
  - Derive Nostr keys and Bitcoin wallets from the same seed
  - Convert between different key formats (hex, npub, nsec)

- **Nostr Protocol Integration**
  - Create and manage user profiles
  - Publish text notes and content
  - Send encrypted direct messages
  - React to posts and add comments
  - Follow/unfollow other users
  - Delete events

- **Bitcoin Wallet Functions**
  - Generate Bitcoin wallets
  - Create and manage addresses

- **Event Handling**
  - Fetch and filter events by kind
  - Deduplicate events from multiple relays
  - Process user interactions
  - Organize messaging 

## 📋 Requirements

- Python 3.7+
- Required packages:
  - `binascii`
  - `hashlib`
  - `uuid`
  - `bech32`
  - `bitcoinlib`
  - `nostr`
  - `pynostr`

## ⚙️ Installation

```bash
# Clone the repository
git clone http://greentruth.koala-ide.ts.net:3002/GreenTruth/nostr_util_functions
cd nostr_util_functions

# Install required packages
pip install -r requirements.txt
```

## 🚀 Quick Start

```python

# Generate a new seed phrase
seed_phrase = generate_passphrase()
print(f"Seed Phrase: {seed_phrase}")

# Derive a seed from the mnemonic
seed = derive_seed_from_mnemonic(seed_phrase)

# Generate Nostr key
nostr_private_key = generate_nostr_key(seed)
print(f"Nostr Private Key: {nostr_private_key.bech32()}")
print(f"Nostr Public Key: {nostr_private_key.public_key.bech32()}")

# Create Bitcoin wallet
wallet_name, bitcoin_address, bitcoin_key = create_wallet(seed)
print(f"Bitcoin Address: {bitcoin_address}")

# Initialize relay manager
relay_manager = RelayManager()
relay_manager.add_relay("wss://relay.damus.io")
relay_manager.open_connections()

# Publish a note
note_content = "Hello, Nostr! This is my first note."
publish_note(relay_manager, nostr_private_key, nostr_private_key.public_key, note_content)
```

## 📝 Usage Examples

### Profile Management

```python
# Create or update a profile
create_profile(
    relay_manager,
    private_key,
    public_key,
    lightning_address,
    display_name,
    about_text,
    profile_picture_url,
    background_image_url
)
```

### Social Interactions

```python
# Publish a note
publish_note(relay_manager, private_key, public_key, "This is my first note!")

# React to a note
reaction_note(relay_manager, private_key, event_id, "+")  # Like

# Reply to a note
reply_to_note(relay_manager, private_key, event_id, "Great post!")

# Follow a user
existing_follows = fetch_existing_follows(relay_manager, public_key.hex())
update_follow_list(existing_follows, relay_manager, relay_urls, private_key, public_key, user_to_follow)
```

### Messaging

```python
# Send an encrypted direct message
receiver_pubkey = decode_npub("npub...")
send_message(relay_manager, private_key, public_key, receiver_pubkey, "Hello!")

# Get organized chat messages
sent_msgs = fetch_events_by_kind(relay_manager, filters_sent, relay_urls)
received_msgs = fetch_events_by_kind(relay_manager, filters_received, relay_urls)
rooms = organize_chat_messages(sent_msgs, received_msgs, private_key, convert_hex_to_npub, decrypt_msg)
```

### Event Management

```python
# Fetch events of a specific kind with additional filtering (limit, since, until)
filters = Filters(
    authors=[public_key.hex()],
    limit=100,               # Limit the number of results
    kinds=[1],               # Text notes
    since=1633024800,        # Fetch events starting from this UNIX timestamp (optional)
    until=1633111200         # Fetch events until this UNIX timestamp (optional)
)
events = fetch_events_by_kind(relay_manager, filters, relay_urls)


# Explanation of Additional Filters:
limit: Restricts the number of events returned (e.g., limit=100 returns at most 100 events).
since: Filters events that were created after a specific UNIX timestamp.
until: Filters events that were created before a specific UNIX timestamp.


# Delete an event
delete_event(relay_manager, private_key, event_id)


```

## 📘 API Reference

### Key Generation Functions

| Function | Description |
|----------|-------------|
| `generate_passphrase()` | Generates a random mnemonic passphrase |
| `derive_seed_from_mnemonic(mnemonic)` | Derives a seed from a mnemonic phrase |
| `generate_nostr_key(seed)` | Generates a Nostr private key from a seed |
| `create_wallet(seed)` | Creates a Bitcoin wallet from a seed |

### Format Conversion Functions

| Function | Description |
|----------|-------------|
| `convert_hex_to_npub(hex_pubkey)` | Converts a hex public key to npub format |
| `decode_npub(npub)` | Decodes an npub public key to hex format |
| `convert_timestamp(timestamp)` | Converts a Unix timestamp to human-readable format |

### Nostr Event Functions

| Function | Description |
|----------|-------------|
| `create_profile(...)` | Creates/updates a Nostr user profile |
| `publish_note(...)` | Publishes a text note |
| `reaction_note(...)` | Sends a reaction to a note |
| `reply_to_note(...)` | Replies to a note |
| `send_message(...)` | Sends an encrypted direct message |
| `delete_event(...)` | Deletes an event |

### Message and Event Management

| Function | Description |
|----------|-------------|
| `decrypt_msg(...)` | Decrypts an encrypted message |
| `fetch_events_by_kind(...)` | Fetches events of a specific kind |
| `organize_chat_messages(...)` | Organizes chat messages by public key |
| `get_chat_for_pubkey(...)` | Gets chat messages with a specific user |
| `fetch_existing_follows(...)` | Fetches the current contact list |
| `update_follow_list(...)` | Updates the follow/unfollow list |


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ⚠️ Security Considerations

- Always keep your seed phrases and private keys secure
- Never share private keys in public repositories
- Consider using environment variables for sensitive information
- Test thoroughly before using in production environments
