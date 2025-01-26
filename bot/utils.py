import json
import os

def load_subscriptions():
    """
    Loads subscription data from the subscriptions.json file.
    Creates the file if it does not exist.

    Returns:
        dict: A dictionary representing user subscriptions, or an empty dictionary if no subscriptions exist.
    """
    if not os.path.exists('db/subscriptions.json'):
        with open('db/subscriptions.json', 'w') as file:
            json.dump({}, file)

    with open('db/subscriptions.json', 'r') as file:
        return json.load(file)

def save_subscriptions(subscriptions):
    """
    Saves subscription data to the subscriptions.json file.

    Args:
        subscriptions (dict): A dictionary containing user subscriptions to be saved.
    """
    with open('db/subscriptions.json', 'w') as file:
        json.dump(subscriptions, file)