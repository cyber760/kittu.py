import json
import os
import hashlib

FILE = "users.json"

# Create file if not exists
if not os.path.exists(FILE):
    with open(FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register():
    users = load_users()
    username = input("Enter username: ")

    if username in users:
        print(" User already exists!")
        return

    password = input("Enter password: ")
    users[username] = hash_password(password)

    save_users(users)
    print(" Registration successful!")

def login():
    users = load_users()
    username = input("Enter username: ")
    password = input("Enter password: ")

    if username in users and users[username] == hash_password(password):
        print(" Login successful!")
    else:
        print(" Invalid username or password!")

# Main menu
while True:
    print("\n Login System")
    print("1. Register")
    print("2. Login")
    print("3. Exit")

    choice = input("Choose: ")

    if choice == '1':
        register()
    elif choice == '2':
        login()
    elif choice == '3':
        print("Goodbye ")
        break
    else:
        print(" Invalid choice")