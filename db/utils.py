from db.connection import execute_query


def alter_table():
    """
    Alters the data type of specific columns in database tables.

    This function is used for database schema migration or updates, specifically changing the type of:
    - "user_id" column in the 'questions' table to TEXT.
    - "USERID" column in the 'ORDERS' table to TEXT.
    - "USERTELEGRAMID" column in the 'Users' table to TEXT.
    - "PRICE" column in the 'ORDERS' table to TEXT.

    This is useful if the initial data type was incorrect or needs to be changed for application requirements.
    """
    execute_query('ALTER TABLE questions ALTER COLUMN "user_id" TYPE TEXT')
    execute_query('ALTER TABLE "ORDERS" ALTER COLUMN "USERID" TYPE TEXT')
    execute_query('ALTER TABLE "Users" ALTER COLUMN "USERTELEGRAMID" TYPE TEXT')
    execute_query('ALTER TABLE "ORDERS" ALTER COLUMN "PRICE" TYPE TEXT')

def create_table():
    """
    Creates necessary database tables if they do not already exist.

    This function sets up the database schema by creating the following tables if they are not present:
    - 'questions': Stores user questions with 'id', 'user_id', and 'message' columns.
    - 'ORDERS': Stores order information with 'USERID', 'DESCRIPTION', 'ORDERID', 'STATUS', and 'PRICE' columns.
    - 'Users': Stores user details with 'USERNAME', 'USERTELEGRAMID', 'USERID', 'BOTDILLER', 'BANNED', 'ORDERS', and 'EDITS' columns.

    Using "IF NOT EXISTS" ensures that the function can be run multiple times without causing errors if the tables are already created.
    """
    execute_query('CREATE TABLE IF NOT EXISTS questions (id SERIAL PRIMARY KEY, user_id TEXT, message TEXT)')
    execute_query('CREATE TABLE IF NOT EXISTS "ORDERS" ("USERID" TEXT NOT NULL UNIQUE, "DESCRIPTION" TEXT NOT NULL, "ORDERID" SERIAL PRIMARY KEY, "STATUS" TEXT NOT NULL, "PRICE" TEXT);') # PRICE changed to TEXT as per alter_table, removed UNIQUE constraint which is not needed and potentially problematic
    execute_query('CREATE TABLE IF NOT EXISTS "Users" ("USERNAME" TEXT NOT NULL, "USERTELEGRAMID" TEXT NOT NULL UNIQUE, "USERID" SERIAL UNIQUE, "BOTDILLER" INTEGER NOT NULL DEFAULT 0, "BANNED" INTEGER NOT NULL DEFAULT 0, "ORDERS" INTEGER DEFAULT 1, "EDITS" INTEGER DEFAULT 2);')