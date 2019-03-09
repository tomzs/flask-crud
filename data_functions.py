import pymongo
import datetime
import json

from datetime import date

with open("db_conn.json") as dbi:
    db_info = json.load(dbi)

db_user = db_info["username"]
db_pass = db_info["password"]
db_cluster = db_info["cluster"]

client = pymongo.MongoClient(f"mongodb+srv://{db_user}:{db_pass}@{db_cluster}")
db = client.learning

# Get the current date
today = date.today()

# Format date
date = today.strftime("%d/%m/%Y")


# Check if user exists, used for login, registration.
def check_user(username):
    users = db.users
    user_exists = users.find_one({'username': username})
    client.close()
    if user_exists is None:
        print(f"Check for user: Does not exist")
        return True
    else:
        print(f"Check for user: Exists")
        return False


# Creates a new User, does not check for existing users.
def register_user(name, email, username, password):
    users = db.users
    users.insert({
        'name': name,
        'username': username,
        'email': email,
        'password': password
    })
    print(f"User {username} registered")
    client.close()


# Returns user's stored hash
def get_password_hash(username):
    users = db.users
    spec_user = users.find_one({"username": username})
    client.close()
    hashed = ""
    for key, val in spec_user.items():
        if 'password' in key:
            hashed = val
    return hashed


# Make post and and update user with
def create_post(author, title, body):

    posts = db.posts
    post = posts.insert({
        'author': author,
        'title': title,
        'body': body,
        'date': datetime.datetime.utcnow()
    })
    updated_user = db.users.find_one_and_update(
        {"username": author},
        {
            "$push": {"posts": post}
        }
    )
    print(f"Post {post} by {author} added")
    client.close()
    return True


# Get the user specific posts

def get_user_posts(username):
    users = db.users
    posts = db.posts

    spec_user = users.find_one({'username': username})
    user_post_ids = []
    for key, val in spec_user.items():
        if key == 'posts':
            user_post_ids = val
    user_posts = posts.find({"_id": {"$in": user_post_ids}})

    return user_posts

# ToDo: Merge get_all_posts and get_user_posts together
# with username being an optional parameter


# Get all posts
def get_all_posts():
    posts = db.posts
    all_posts = posts.find({})
    client.close()
    return all_posts
