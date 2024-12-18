import os
import time
import socket
import requests
import logging
import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

load_dotenv()

OPTIONS = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('DB_HOST', 'database')
}

HEADERS = {"User-Agent": os.getenv("USER_AGENT")}

URL = "https://mammamiachel.ru/prices"

def parse_service_data():
    all_services = []

    try:
        logging.info("Начинаем парсинг данных...")
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        data_blocks = soup.find_all('div', class_='t431')
        for block in data_blocks:
            part1 = block.find('div', class_='t431__data-part1')
            part2 = block.find('div', class_='t431__data-part2')

            if part1 and part2:
                prices = part2.text.split('\n')
                for price_line in prices:
                    if price_line.strip():
                        parts = price_line.split(';')
                        if len(parts) == 3:  
                            name = parts[0].strip()
                            master1_price = parts[1].replace('₽', '').strip()
                            master2_price = parts[2].replace('₽', '').strip()
                        elif len(parts) == 2:  
                            name = parts[0].strip()
                            master1_price = master2_price = parts[1].replace('₽', '').strip()
                        elif 'от' in price_line and 'до' in price_line:  
                            name, price_range = price_line.split(';', 1)
                            master1_price = master2_price = price_range.strip()
                        else:
                            logging.warning(f"Неизвестный формат строки: {price_line}")
                            continue

                        all_services.append((name, master1_price, master2_price))
            else:
                logging.warning(f"part1 или part2 отсутствуют в блоке: {block}")
    except Exception as e:
        logging.error(f"Ошибка парсинга данных: {e}")
    
    logging.info(f"Парсинг завершён. Найдено услуг: {len(all_services)}.")
    return all_services


def insert_services_to_db(all_services):
    try:
        with psycopg2.connect(**OPTIONS) as conn:
            with conn.cursor() as cursor:
                for service in all_services:
                    name, master1_price, master2_price = service
                    query = '''
                        INSERT INTO services (name, master1_price, master2_price)
                        VALUES (%s, %s, %s);
                    '''
                    cursor.execute(query, (name, master1_price, master2_price))
                    conn.commit()
    except Exception as e:
        logging.error(f"Ошибка сохранения данных в базу: {e}")

def wait_for_db():
    logging.info("Ожидание подключения к базе данных...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            s.connect(('database', 5432))
            s.close()
            logging.info("Соединение с базой данных установлено.")
            break
        except socket.error:
            time.sleep(0.1)

if __name__ == '__main__':
    wait_for_db()
    while True:
        try:
            services = parse_service_data()
            if services:
                insert_services_to_db(services)
                logging.info("Данные успешно сохранены.")
            else:
                logging.warning("Услуги не найдены.")
            time.sleep(24 * 60 * 60)
        except psycopg2.OperationalError as e:
            logging.error(f"Ошибка базы данных: {e}")
            time.sleep(1)
