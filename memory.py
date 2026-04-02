import os
import json

MEMORY_FILE = "memory.json"

# Load memory from file
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

# Save memory to file
def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Store info to memory
def remember(key, value):
    data = load_memory()
    data[key] = value
    save_memory(data)

# Retrieve info for a key
def recall(key):
    data = load_memory()
    return data.get(key, None)