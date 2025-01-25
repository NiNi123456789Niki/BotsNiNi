from db.connection import execute_query
import json
import psycopg2
import encrypter
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_tid(ord_id):
    tid = execute_query('SELECT "USERID" FROM "ORDERS" WHERE "ORDERID" = %s', (ord_id,), fetchone=True)
    return encrypter.decode(tid[0])

def create_order(tid, desc):
    orders = execute_query('SELECT "ORDERS" FROM "Users" WHERE "USERTELEGRAMID" = %s', (encrypter.encode(tid),), fetchone=True)[0]
    if orders <= 0:
        return False
    orders -= 1
    execute_query('UPDATE "Users" SET "ORDERS" = %s WHERE "USERTELEGRAMID" = %s', (orders, encrypter.encode(tid)))
    execute_query('INSERT INTO "ORDERS" ("USERID", "DESCRIPTION","STATUS", "PRICE") VALUES (%s, %s, %s, %s)',(encrypter.encode(tid), encrypter.encode(desc), "CHECKING", "None"))
    return True

def change_status(new_status, order_id):
    execute_query('UPDATE "ORDERS" SET "STATUS" = %s WHERE "ORDERID" = %s', (new_status, order_id))

def set_price(order_id, price):
    try:
        execute_query('UPDATE "ORDERS" SET "PRICE" = %s WHERE "ORDERID" = %s', (price, order_id))
        return True
    except Exception as e:
        logging.error(f"Error updating price: {e}")
        return False

def get_orders(status):
    try:
        rows = execute_query('SELECT "USERID", "DESCRIPTION", "ORDERID", "STATUS", "PRICE" FROM "ORDERS" WHERE "STATUS" = %s', (status,), fetchall=True)
        json_data = []
        for row in rows:
            try:
                userid = encrypter.decode(row[0])
                description = encrypter.decode(row[1])
                order_id = str(row[2])
                status = str(row[3])
                price = row[4]
                if price in ["", None, "None"]:
                    price = "Не установлена"
                else:
                    price = str(price)
                order_data = {"userid": userid, "description": description, "order_id": order_id, "status": status, "price": price}
                json_data.append(order_data)
            except Exception as e:
                logger.error(f"Ошибка при обработке заказа: {e}")
                continue
        return json.dumps(json_data, ensure_ascii=False)
    except psycopg2.Error as error:
        logger.error(f"Ошибка при получении информации: {error}")
        return "[]"

def get_order_from_tid(tid):
    try:
        orders = execute_query('SELECT "ORDERID", "DESCRIPTION", "STATUS", "PRICE" FROM "ORDERS" WHERE "USERID" = %s', (encrypter.encode(tid),), fetchone=True)
        if orders:
            return (orders[0], encrypter.decode(orders[1]), orders[2], orders[3])
        return None
    except psycopg2.Error as e:
        logger.error(f"Ошибка при получении заказов: {e}")
        return None

def get_order(ord_id):
    result = execute_query('SELECT "USERID", "DESCRIPTION", "STATUS", "PRICE" FROM "ORDERS" WHERE "ORDERID" = %s', (ord_id,), fetchone=True)
    if result:
        return (encrypter.decode(result[0]), encrypter.decode(result[1]), result[2], result[3])
    return None

def delete_order(ord_id):
    execute_query('DELETE FROM "ORDERS" WHERE "ORDERID" = %s', (ord_id,))

def add_to_desc(ord_id, desc):
    description = execute_query('SELECT "DESCRIPTION" FROM "ORDERS" WHERE "ORDERID" = %s', (ord_id,), fetchone=True)
    if description and description[0]:
        current_desc = encrypter.decode(description[0])
        new_desc = f"{current_desc}. {desc}"
        execute_query('UPDATE "ORDERS" SET "DESCRIPTION" = %s WHERE "ORDERID" = %s', (encrypter.encode(new_desc), ord_id))







