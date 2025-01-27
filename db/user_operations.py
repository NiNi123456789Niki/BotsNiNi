from db.connection import execute_query
import encrypter
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def check_for_user(username, tid):
    """
    Checks if a user exists in the database based on their telegram ID.
    If the user does not exist, it creates a new user.

    Args:
        username (str): The username of the user.
        tid (str): The telegram ID of the user.

    Returns:
        bool: True if the user exists (or was just created), False otherwise (though in current logic always returns True).

    Queries the 'Users' table to check if a user with the given telegram ID exists.
    If a user is found (count is not None), it returns True.
    If no user is found, it calls create_user to add a new user and implicitly returns True.
    """
    count = execute_query('SELECT "USERTELEGRAMID" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)
    if count:
        return True
    create_user(username, tid)
    return True # Added return True to ensure consistent return after user creation


def create_user(username, tid):
    """
    Creates a new user in the database.

    Args:
        username (str): The username of the new user.
        tid (str): The telegram ID of the new user.

    Encodes the username and telegram ID and inserts a new row into the 'Users' table
    with the provided username and telegram ID.
    """
    execute_query('INSERT INTO "Users" ("USERNAME", "USERTELEGRAMID") VALUES (%s, %s)', (encrypter.encode(username), encrypter.encode(tid)))


def check_for_block(tid):
    """
    Checks if a user is blocked (banned) based on their telegram ID.

    Args:
        tid (str): The telegram ID of the user to check.

    Returns:
        bool: True if the user is banned, False otherwise. Returns False if user is not found and logs an error.

    Queries the 'Users' table to retrieve the 'BANNED' status for the user with the given telegram ID.
    Returns True if the 'BANNED' status is 1 (representing banned), False otherwise.
    Logs an error if the user is not found in the database.
    """
    result = execute_query('SELECT "BANNED" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)
    if result is None:
        logger.error(f"Cannot find user with tid {tid}")
        return False
    return str(result[0]) == str(1)


def check_for_edits(tid):
    """
    Checks if a user has remaining edits available based on their telegram ID.

    Args:
        tid (str): The telegram ID of the user to check.

    Returns:
        bool: True if the user has edits available (EDITS > 0), False otherwise. Returns False if user is not found.

    Queries the 'Users' table to retrieve the 'EDITS' count for the user with the given telegram ID.
    Returns True if the 'EDITS' count is 1, False otherwise. Returns False if user is not found.
    """
    result = execute_query('SELECT "EDITS" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)
    if result is None:
        return False # Return False when user not found
    return result[0] == 1


def edit(tid):
    """
    Decrements the 'EDITS' count for a user if they have edits available.

    Args:
        tid (str): The telegram ID of the user to decrement edits for.

    Returns:
        bool: False if the user has no edits available before this function call or user not found,
              implicitly returns None otherwise after decrementing edit count.

    First, checks if the user has edits available using check_for_edits(tid). If no edits, returns False.
    Then, retrieves the current 'EDITS' count, decrements it by 1, and updates the 'Users' table.
    Returns False if no edits are available initially, or user is not found.
    """
    edits = check_for_edits(tid)
    if not edits: # Changed to if not edits for better readability - checks if edits is False
        return False

    result = execute_query('SELECT "EDITS" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)
    if result is None:
        return False

    current_edits = result[0]
    execute_query('UPDATE "Users" SET "EDITS" = %s WHERE "USERTELEGRAMID" = %s', (current_edits - 1, encrypter.encode(tid)))
    return None # Explicitly return None after successful edit


def subscribe(tid):
    """
    Subscribes a user, granting them 'BOTDILLER' status, a high 'ORDERS' limit, and 'EDITS'.

    Args:
        tid (str): The telegram ID of the user to subscribe.

    Updates the 'Users' table for the given user:
    - Sets 'BOTDILLER' to 1 (representing subscribed).
    - Sets 'ORDERS' to 9999 (a high order limit).
    - Sets 'EDITS' to 15.
    """
    execute_query('UPDATE "Users" SET "BOTDILLER" = 1 WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),))
    execute_query('UPDATE "Users" SET "ORDERS" = 9999 WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),))
    execute_query('UPDATE "Users" SET "EDITS" = 15 WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),))


def unsubscribe(tid):
    """
    Unsubscribes a user, removing their 'BOTDILLER' status.

    Args:
        tid (str): The telegram ID of the user to unsubscribe.

    Updates the 'Users' table for the given user, setting 'BOTDILLER' to 0 (representing unsubscribed).
    """
    execute_query('UPDATE "Users" SET "BOTDILLER" = 0 WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),))


def ban_user(tid):
    """
    Bans a user, setting their 'BANNED' status to 1.

    Args:
        tid (str): The telegram ID of the user to ban.

    Updates the 'Users' table for the given user, setting 'BANNED' to 1.
    """
    execute_query('UPDATE "Users" SET "BANNED" = 1 WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),))


def reset_user(tid):
    """
    Resets a user's 'ORDERS' and 'EDITS' count to default values.

    Args:
        tid (str): The telegram ID of the user to reset.

    Updates the 'Users' table for the given user:
    - Sets 'ORDERS' to 1.
    - Sets 'EDITS' to 2.
    """
    execute_query('UPDATE "Users" SET "ORDERS" = %s WHERE "USERTELEGRAMID" = %s', (1, encrypter.encode(tid)))
    execute_query('UPDATE "Users" SET "EDITS" = %s WHERE "USERTELEGRAMID" = %s', (2, encrypter.encode(tid)))


def reset():
    """
    Resets 'ORDERS' and 'EDITS' count for all non-'BOTDILLER' users to default values.

    Updates the 'Users' table for all users where 'BOTDILLER' is 0:
    - Sets 'ORDERS' to 1.
    - Sets 'EDITS' to 1.
    """
    execute_query('UPDATE "Users" SET "ORDERS" = %s WHERE "BOTDILLER" = %s', (1, 0))
    execute_query('UPDATE "Users" SET "EDITS" = %s WHERE "BOTDILLER" = %s', (1, 0))


def get_username(tid):
    """
    Retrieves the username of a user based on their telegram ID.

    Args:
        tid (str): The telegram ID of the user.

    Returns:
        str: The username of the user, or None if the user is not found or username is null.

    Queries the 'Users' table to retrieve the 'USERNAME' for the user with the given telegram ID.
    Decodes the retrieved username before returning it.
    Returns None if the user is not found or if the username in the database is None.
    """
    result = execute_query('SELECT "USERNAME" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)
    if result is None or result[0] is None:
        return None
    return encrypter.decode(result[0])