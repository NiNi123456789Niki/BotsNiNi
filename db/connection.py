from bot.config import DATABASE_URL
import threading
import logging
import psycopg2

# Lock for thread-safe database connection handling
_db_connection_lock = threading.Lock()

def execute_query(query, params=(), fetchone=False, fetchall=False):
    """
    Executes an SQL query on the database.

    Args:
        query (str): The SQL query to execute.
        params (tuple, optional): Parameters to be passed to the query. Defaults to ().
        fetchone (bool, optional): If True, fetches and returns only the first row. Defaults to False.
        fetchall (bool, optional): If True, fetches and returns all rows. Defaults to False.

    Returns:
        fetchone=True: Returns a single row as a tuple, or None if no row is found.
        fetchall=True: Returns a list of tuples, where each tuple represents a row, or an empty list if no rows are found.
        fetchone=False and fetchall=False: Returns None.

    Raises:
        psycopg2.Error: If there is any error during database operation, the error is logged, the transaction is rolled back, and the exception is re-raised.
        ValueError: If DATABASE_URL is not set.
    """
    connection = get_db_connection() # Get a database connection
    try:
        cursor = connection.cursor() # Create a database cursor
        cursor.execute(query, params) # Execute the query with parameters
        if fetchone:
            return cursor.fetchone() # Fetch and return the first row
        if fetchall:
            return cursor.fetchall() # Fetch and return all rows
        connection.commit() # Commit the transaction if it's not a fetch operation
    except psycopg2.Error as e:
        logging.error(f"Database error: {e}") # Log database errors
        connection.rollback() # Rollback the transaction in case of error
        raise # Re-raise the exception to be handled by the caller
    finally:
        if connection: # Ensure connection and cursor are closed even if errors occur
            cursor.close() # Close the cursor
            connection.close() # Close the database connection

def get_db_connection():
    """
    Establishes and returns a PostgreSQL database connection.

    Uses a lock to ensure thread-safe connection retrieval, especially important in threaded environments.
    Reads the database connection URL from the DATABASE_URL environment variable.

    Returns:
        psycopg2.extensions.connection: A psycopg2 database connection object.

    Raises:
        psycopg2.Error: If there is an error during connection to the PostgreSQL database.
        ValueError: If the DATABASE_URL environment variable is not set.
    """
    with _db_connection_lock: # Acquire lock to ensure thread-safe connection
        try:
            if not DATABASE_URL:
                raise ValueError("DATABASE_URL environment variable not set.") # Raise error if DATABASE_URL is not configured
            conn = psycopg2.connect(DATABASE_URL) # Establish connection to the database using DATABASE_URL
            return conn # Return the database connection object
        except psycopg2.Error as e:
            logging.error(f"Error connecting to PostgreSQL: {e}") # Log PostgreSQL connection errors
            raise # Re-raise the exception
        except ValueError as e:
            logging.error(e) # Log ValueError exceptions (DATABASE_URL not set)
            raise # Re-raise the exception