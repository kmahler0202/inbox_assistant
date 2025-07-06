import os

def load_last_history_id():
    try:
        with open("hid.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_last_history_id(history_id):
    with open("hid.txt", "w") as f:
        f.write(str(history_id))
