from db.connection import execute_query
import json
import psycopg2
import encrypter # Assuming this is a module for encoding/decoding user IDs and descriptions
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_tid(ord_id):
    """
    Retrieves the Telegram User ID (tid) associated with a given Order ID.

    Fetches the encoded USERID from the ORDERS table and decodes it using the encrypter module.

    Args:
        ord_id (int): The Order ID to look up.

    Returns:
        str: The decoded Telegram User ID associated with the order, or None if not found (though the query should always return a value if order_id exists).
    """
    tid = execute_query('SELECT "USERID" FROM "ORDERS" WHERE "ORDERID" = %s', (ord_id,), fetchone=True)
    return encrypter.decode(tid[0]) # Decode the retrieved encoded User ID

def create_order(tid, desc):
    """
    Creates a new order in the database.

    Decrements the 'ORDERS' count for the user in the 'Users' table, if available.
    Inserts a new order into the 'ORDERS' table with status 'CHECKING' and price 'None'.

    Args:
        tid (str): Telegram User ID of the user placing the order.
        desc (str): Description of the order.

    Returns:
        bool: True if the order creation was successful, False if the user has no orders left.
    """
    orders_left_result = execute_query('SELECT "ORDERS" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)
    if not orders_left_result: # Handle case where user is not found in Users table
        logger.warning(f"User with tid {tid} not found in Users table during order creation.")
        return False # Or raise an exception depending on desired behavior

    orders_left = orders_left_result[0]

    if orders_left <= 0:
        return False # User has no orders left

    orders_left -= 1
    execute_query('UPDATE "Users" SET "ORDERS" = %s WHERE "USERTELEGRAMID" = %s', (orders_left, encrypter.encode(tid))) # Update remaining order count
    execute_query('INSERT INTO "ORDERS" ("USERID", "DESCRIPTION","STATUS", "PRICE") VALUES (%s, %s, %s, %s)',(encrypter.encode(tid), encrypter.encode(desc), "CHECKING", "None")) # Insert new order with encoded data
    return True

def change_status(new_status, order_id):
    """
    Updates the status of an existing order.

    Args:
        new_status (str): The new status to set for the order.
        order_id (int): The ID of the order to update.
    """
    execute_query('UPDATE "ORDERS" SET "STATUS" = %s WHERE "ORDERID" = %s', (new_status, order_id))

def set_price(order_id, price):
    """
    Sets the price for an order.

    Args:
        order_id (int): The ID of the order to update.
        price (str): The price to set for the order.

    Returns:
        bool: True if the price was updated successfully, False otherwise.
    """
    try:
        execute_query('UPDATE "ORDERS" SET "PRICE" = %s WHERE "ORDERID" = %s', (price, order_id))
        return True
    except Exception as e:
        logging.error(f"Error updating price: {e}") # Log errors during price update
        return False

def get_orders(status):
    """
    Retrieves orders with a specific status and formats them as a JSON string.

    Fetches orders from the 'ORDERS' table based on the provided status.
    Decodes 'USERID' and 'DESCRIPTION' from the database results.
    Formats the data into a JSON string.

    Args:
        status (str): The status of orders to retrieve.

    Returns:
        str: JSON string representing a list of orders with the specified status. Returns "[]" in case of error or no orders found.
    """
    try:
        rows = execute_query('SELECT "USERID", "DESCRIPTION", "ORDERID", "STATUS", "PRICE" FROM "ORDERS" WHERE "STATUS" = %s', (status,), fetchall=True)
        json_data = []
        for row in rows: # Iterate through each order row retrieved
            try:
                userid = encrypter.decode(row[0]) # Decode User ID
                description = encrypter.decode(row[1]) # Decode Description
                order_id = str(row[2])
                status = str(row[3])
                price = row[4]
                if price in ["", None, "None"]: # Handle cases where price is not set or is "None" string
                    price = "Не установлена"
                else:
                    price = str(price)
                order_data = {"userid": userid, "description": description, "order_id": order_id, "status": status, "price": price} # Create order data dictionary
                json_data.append(order_data) # Add order data to the list
            except Exception as e:
                logger.error(f"Ошибка при обработке заказа: {e}") # Log errors during order data processing
                continue # Continue to the next order even if one fails
        return json.dumps(json_data, ensure_ascii=False) # Convert order data to JSON string, ensuring non-ASCII characters are handled correctly
    except psycopg2.Error as error:
        logger.error(f"Ошибка при получении информации: {error}") # Log database query errors
        return "[]" # Return empty JSON array string in case of error

def get_order_from_tid(tid):
    """
    Retrieves an order associated with a specific Telegram User ID (tid).

    Fetches the first order found for the given User ID from the 'ORDERS' table.
    Decodes the 'DESCRIPTION' from the database result.

    Args:
        tid (str): Telegram User ID to look up orders for.

    Returns:
        tuple: A tuple containing (ORDERID, decoded DESCRIPTION, STATUS, PRICE) of the order, or None if no order is found for the given User ID.
    """
    try:
        orders = execute_query('SELECT "ORDERID", "DESCRIPTION", "STATUS", "PRICE" FROM "ORDERS" WHERE "USERID" = %s', (encrypter.encode(tid),), fetchone=True)
        if orders:
            return (orders[0], encrypter.decode(orders[1]), orders[2], orders[3]) # Decode description before returning
        return None
    except psycopg2.Error as e:
        logger.error(f"Ошибка при получении заказов: {e}") # Log database query errors
        return None

def get_order(ord_id):
    """
    Retrieves an order based on its Order ID.

    Fetches an order from the 'ORDERS' table using the provided Order ID.
    Decodes 'USERID' and 'DESCRIPTION' from the database result.

    Args:
        ord_id (int): The Order ID to retrieve.

    Returns:
        tuple: A tuple containing (decoded USERID, decoded DESCRIPTION, STATUS, PRICE) of the order, or None if no order is found for the given Order ID.
    """
    result = execute_query('SELECT "USERID", "DESCRIPTION", "STATUS", "PRICE" FROM "ORDERS" WHERE "ORDERID" = %s', (ord_id,), fetchone=True)
    if result:
        return (encrypter.decode(result[0]), encrypter.decode(result[1]), result[2], result[3]) # Decode USERID and DESCRIPTION
    return None

def delete_order(ord_id):
    """
    Deletes an order from the 'ORDERS' table based on its Order ID.

    Args:
        ord_id (int): The Order ID of the order to delete.
    """
    execute_query('DELETE FROM "ORDERS" WHERE "ORDERID" = %s', (ord_id,))

def add_to_desc(ord_id, desc):
    """
    Appends additional description to an existing order.

    Retrieves the current description, decodes it, appends the new description, encodes the combined description, and updates the order in the database.

    Args:
        ord_id (int): The Order ID to update.
        desc (str): The additional description to append.
    """
    description_result = execute_query('SELECT "DESCRIPTION" FROM "ORDERS" WHERE "ORDERID" = %s', (ord_id,), fetchone=True)
    if description_result and description_result[0]:
        current_desc = encrypter.decode(description_result[0]) # Decode current description
        new_desc = f"{current_desc}. {desc}" # Append new description
        execute_query('UPDATE "ORDERS" SET "DESCRIPTION" = %s WHERE "ORDERID" = %s', (encrypter.encode(new_desc), ord_id)) # Encode and update the combined description