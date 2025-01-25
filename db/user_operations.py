from db.connection import execute_query
import encrypter
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def check_for_user(username, tid):
    count = execute_query('SELECT "USERTELEGRAMID" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)
    if count:
        return True
    create_user(username, tid)


def create_user(username, tid):
    execute_query('INSERT INTO "Users" ("USERNAME", "USERTELEGRAMID") VALUES (%s, %s)', (encrypter.encode(username), encrypter.encode(tid)))


def check_for_block(tid):
    result = execute_query('SELECT "BANNED" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)
    if result is None:
        logger.error(f"Cannot find user with tid {tid}")
        return False
    return result[0] == 1


def check_for_edits(tid):
    result = execute_query('SELECT "EDITS" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)
    if result is None:
        return False
    return result[0] == 1


def edit(tid):
    edits = check_for_edits(tid)
    if edits:
        return False

    result = execute_query('SELECT "EDITS" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)
    if result is None:
        return False

    current_edits = result[0]
    execute_query('UPDATE "Users" SET "EDITS" = %s WHERE "USERTELEGRAMID" = %s', (current_edits - 1, encrypter.encode(tid)))


def subscribe(tid):
    execute_query('UPDATE "Users" SET "BOTDILLER" = 1 WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),))
    execute_query('UPDATE "Users" SET "ORDERS" = 9999 WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),))
    execute_query('UPDATE "Users" SET "EDITS" = 15 WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),))


def unsubscribe(tid):
    execute_query('UPDATE "Users" SET "BOTDILLER" = 0 WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),))


def ban_user(tid):
    execute_query('UPDATE "Users" SET "BANNED" = 1 WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),))


def reset_user(tid):
    execute_query('UPDATE "Users" SET "ORDERS" = %s WHERE "USERTELEGRAMID" = %s', (1, encrypter.encode(tid)))
    execute_query('UPDATE "Users" SET "EDITS" = %s WHERE "USERTELEGRAMID" = %s', (2, encrypter.encode(tid)))


def reset():
    execute_query('UPDATE "Users" SET "ORDERS" = %s WHERE "BOTDILLER" = %s', (1, 0))
    execute_query('UPDATE "Users" SET "EDITS" = %s WHERE "BOTDILLER" = %s', (1, 0))


def get_username(tid):
    result = execute_query('SELECT "USERNAME" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)
    if result is None or result[0] is None:
        return None
    return encrypter.decode(result[0])