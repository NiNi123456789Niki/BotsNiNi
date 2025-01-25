import json
import os

def load_subscriptions():
    if not os.path.exists('db/subscriptions.json'):
        with open('db/subscriptions.json', 'w') as file:
            json.dump({}, file)

    with open('db/subscriptions.json', 'r') as file:
        return json.load(file)

def save_subscriptions(subscriptions):
    with open('db/subscriptions.json', 'w') as file:
        json.dump(subscriptions, file)
