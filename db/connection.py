from bot.config import DATABASE_URL
import threading
import logging
import psycopg2 

_db_connection_lock = threading.Lock()

def execute_query(query, params=(), fetchone=False, fetchall=False):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
        connection.commit()
    except psycopg2.Error as e:
        logging.error(f"Database error: {e}")
        connection.rollback()
        raise 
    finally:
        if connection: 
            cursor.close()
            connection.close()

def get_db_connection():
    with _db_connection_lock:
        try:
            if not DATABASE_URL:
                raise ValueError("DATABASE_URL environment variable not set.")
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except psycopg2.Error as e:
            logging.error(f"Error connecting to PostgreSQL: {e}")
            raise
        except ValueError as e:
            logging.error(e)
            raise