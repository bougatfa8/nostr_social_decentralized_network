

"""
1. fetch the relay indos
2. pow
"""
import requests
# today by 10 / 11:50 mn
def get_relay_info(relay_url: str):
    headers = {'Accept': 'application/nostr+json'}
    try:
        response = requests.get(relay_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Failed to retrieve relay info. Status code: {response.status_code}"
    except requests.RequestException as e:
        return f"An error occurred: {e}"

# Example usage
relay_url = "https://relay.damus.io"  # The URL of the Damus relay
relay_url = "https://eden.nostr.land"  # Replace with your relay URL
relay_info = get_relay_info(relay_url)
print(relay_info)


import hashlib
import json
import time
# NIP-13 Proof of Work (PoW) Mining for Nostr

def count_leading_zero_bits(hex_string: str) -> int:
    binary_string = bin(int(hex_string, 16))[2:].zfill(256)
    return len(binary_string) - len(binary_string.lstrip('0'))

def mine_note(note: dict, difficulty: int) -> dict:
    nonce = 0
    while True:
        # Update nonce and created_at
        note['tags'] = [['nonce', str(nonce), str(difficulty)]]
        note['created_at'] = int(time.time())

        # Convert note to JSON and hash it
        note_json = json.dumps(note, separators=(',', ':'), sort_keys=True)
        note_id = hashlib.sha256(note_json.encode()).hexdigest()

        # Check if the difficulty condition is met
        if count_leading_zero_bits(note_id) >= difficulty:
            note['id'] = note_id
            return note

        nonce += 1

def main():
    note = {
        'pubkey': 'npub193jegpe9h0csh7al22mkcstqva2ygyny7ura8kwvrn4tsmtnl4lsrxny6k',
        'created_at': int(time.time()),
        'kind': 1,
        'tags': [],
        'content': "It's just me mining my own business"
    }

    difficulty = 20  # Target difficulty (number of leading zero bits)
    mined_note = mine_note(note, difficulty)

    print("Mined Note:")
    print(json.dumps(mined_note, indent=4))


if __name__ == "__main__":
    main()


"""
Kind 14 is a chat message. p tags identify one or more receivers of the message.
{
    "id": "<usual hash>",
    "pubkey": "<sender-pubkey>",
    "created_at": "<current-time>",
    "kind": 14,
    "tags": [
    ["p", "<receiver-1-pubkey>", "<relay-url>"],
    ["p", "<receiver-2-pubkey>", "<relay-url>"],
    ["e", "<kind-14-id>", "<relay-url>"] // if this is a reply
    ["subject", "<conversation-title>"],
// rest of tags...
],
    "content": "<message-in-plain-text>",
}
"""
