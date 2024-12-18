import os
import psycopg2
from dotenv import load_dotenv
import re

load_dotenv()

OPTIONS = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': "database"
}

try:
    with psycopg2.connect(**OPTIONS) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("Соединение с базой данных установлено")
except Exception as e:
    print(f"Ошибка подключения: {e}")

def brows():
    query = "SELECT name, master1_price, master2_price FROM services WHERE name ILIKE '%бровей%' OR name ILIKE '%волос%'"
    return execute_query(query)

def lashes():
    query = (
        "SELECT name, master1_price, master2_price FROM services WHERE (name ILIKE '%ресниц%' "
        "OR name ILIKE '%ботокс%') AND name NOT ILIKE '%бровей%'"
    )
    return execute_query(query)

def extra_services():
    query = "SELECT name, master1_price, master2_price FROM services WHERE name ILIKE '%1 ноготь%' OR name ILIKE '%1 штука%'"
    return execute_query(query)

def clarification(context):
    if context == 'leg':
        query = (
            "SELECT name, master1_price, master2_price FROM services WHERE "
            "(name ILIKE '%поднятие%' OR name ILIKE '%укрепление%' OR "
            "name ILIKE '%снятие%' OR name ILIKE '%однотонное%' OR "
            "name ILIKE '%ремонт%') AND "
            "(name NOT ILIKE '%маникюр%' AND name NOT ILIKE '%рук%')"
        )
    elif context == 'hand':
        query = (
            "SELECT name, master1_price, master2_price FROM services WHERE "
            "(name ILIKE '%поднятие%' OR name ILIKE '%укрепление%' OR "
            "name ILIKE '%снятие%' OR name ILIKE '%однотонное%' OR "
            "name ILIKE '%ремонт%') AND "
            "(name NOT ILIKE '%педикюр%' AND name NOT ILIKE '%ног%')"
        )
    return execute_query(query)

def nails(context):
    if context == 'leg':
        query = (
            "SELECT name, master1_price, master2_price FROM services WHERE "
            "name ILIKE '%педикюр%' OR name ILIKE '%ног%' OR "
            "name ILIKE '%стопы%' OR name ILIKE '%мозолей%'"
        )


    elif context == 'hand':
        query = (
            "SELECT name, master1_price, master2_price FROM services WHERE "
            "(name ILIKE '%маникюр%' OR name ILIKE '%классический%' OR "
            "name ILIKE '%наращивание%' OR name ILIKE '%нарощенных%') AND "
            "(name NOT ILIKE '%снятие%')"
        )
    return execute_query(query)

def get_cart_items(user_id):
    query = """
    SELECT service_name, MIN(min_price) AS min_price, MIN(max_price) AS max_price, COUNT(*) AS quantity
    FROM cart
    WHERE user_id = %s
    GROUP BY service_name
    """
    cart_items = execute_query(query, (user_id,))
    return cart_items

def add_to_cart(user_id, service_name, price):
    
    min_price, max_price, comment = parse_price(price)

    query = """
    INSERT INTO cart (user_id, service_name, min_price, max_price, comment)
    VALUES (%s, %s, %s, %s, %s)
    """
    try:
        execute_query(query, (user_id, service_name, min_price, max_price, comment))
        print(f"Услуга '{service_name}' добавлена в корзину для пользователя {user_id}")
        return True
    except Exception as e:
        print(f"Ошибка при добавлении услуги в корзину: {e}")
        return False


def delete_from_cart(user_id, service_name):
    query_check = """
    SELECT COUNT(*) AS quantity FROM cart
    WHERE user_id = %s AND service_name = %s
    """
    result = execute_query(query_check, (user_id, service_name))

    if result and result[0]['quantity'] > 1:
        
        query_delete_one = """
        DELETE FROM cart
        WHERE ctid IN (
            SELECT ctid FROM cart
            WHERE user_id = %s AND service_name = %s
            LIMIT 1
        )
        """
        execute_query(query_delete_one, (user_id, service_name))
        return service_name
    else:
        
        query_delete = """
        DELETE FROM cart WHERE user_id = %s AND service_name = %s
        """
        execute_query(query_delete, (user_id, service_name))
        return service_name


def calculate_total(user_id):
    query = """
    SELECT service_name, MIN(min_price) AS min_price, MIN(max_price) AS max_price, COUNT(*) AS quantity
    FROM cart
    WHERE user_id = %s
    GROUP BY service_name
    """
    cart_items = execute_query(query, (user_id,))

    if not cart_items:
        return "Корзина пуста."

    min_total = 0
    max_total = 0
    services_list = []

    for item in cart_items:
        service_name = item['service_name']
        quantity = item['quantity']
        min_price = item['min_price'] or 0
        max_price = item['max_price'] or 0

        total_min = min_price * quantity
        total_max = max_price * quantity

        if ((quantity > 1) & (min_price == max_price)) :
            services_list.append(f"{service_name}: {min_price}₽ × {quantity}шт")
        elif((quantity > 1) & (min_price != max_price)):
            services_list.append(f"{service_name}: от {min_price}₽ до {max_price}₽ × {quantity}шт")
        elif ((quantity <= 1) & (min_price != max_price)):
            services_list.append(f"{service_name}: от {min_price}₽ до {max_price}₽")
        else:
            services_list.append(f"{service_name}: {min_price}₽")

        min_total += total_min
        max_total += total_max

    if min_total == max_total:
        total_message = f"{min_total}₽"
    else:
        total_message = f"от {min_total} до {max_total}₽"

    cart_contents = "\n".join(services_list)
    return f"Содержимое корзины:\n{cart_contents}\n\nИтоговая стоимость: {total_message}"

def parse_price(price):
    
    price = price.replace("*", "").strip()
    price = re.sub(r'\s+', ' ', price)

    match_exact = re.match(r"^(\d+)$", price)  
    match_range = re.match(r"^от (\d+) до (\d+)$", price)  
    match_variable = re.match(r"^от (\d+) \((.+)\)$", price)  
    match_no_comment = re.match(r"^от (\d+)$", price)  

    if match_exact:
        return float(match_exact.group(1)), float(match_exact.group(1)), None
    elif match_range:
        return float(match_range.group(1)), float(match_range.group(2)), None
    elif match_variable:
        return float(match_variable.group(1)), float(match_variable.group(1)), match_variable.group(2)
    elif match_no_comment:
        return float(match_no_comment.group(1)), float(match_no_comment.group(1)), None
    else:
        raise ValueError(f"Неверный формат цены: {price}")

def execute_query(query, params=None):
    try:
        with psycopg2.connect(**OPTIONS) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params) if params else cursor.execute(query)
                conn.commit()  
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        return []
