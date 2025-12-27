import json
import hashlib
import datetime

# 1. SETUP YOUR ADMIN CREDENTIALS HERE
ADMIN_USER = "admin"
ADMIN_PASS = "12345"  # <--- Change this to a strong password!

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# 2. LOAD DATABASE
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

# 3. ADD ADMIN
if ADMIN_USER in users:
    print(f"⚠️ User '{ADMIN_USER}' already exists! Updating password...")
else:
    print(f"✅ Creating new super-user '{ADMIN_USER}'...")

users[ADMIN_USER] = {
    "password": hash_password(ADMIN_PASS),
    "joined": str(datetime.date.today()),
    "role": "admin"
}

# 4. SAVE
with open("users.json", "w") as f:
    json.dump(users, f, indent=4)

print("🎉 Success! Admin account created/updated.")
print(f"Login with User: {ADMIN_USER} | Pass: {ADMIN_PASS}")