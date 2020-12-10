import time
import pika
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException

HOST = 'https://auth.dodopizza.ru/Authenticate/LogOn'

def init_connection():
    credentials = pika.PlainCredentials('admin', 'admin')
    connection = pika.BlockingConnection(pika.ConnectionParameters('95.181.230.223',
                                                               5672,
                                                               '/',
                                                               credentials))
    return connection 

def init_driver():
    # chrome_options = webdriver.ChromeOptions() если запускать в контейнере
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--disable-gpu')
    # driver = webdriver.Chrome(options=chrome_options)
    # driver.wait = WebDriverWait(driver, 5)
    driver = webdriver.Chrome('C:\chromedriver') #если запускать с локальной машины
    return driver
 
 
def lookup(driver, query, auth, host, channel):
    driver.get(host)
    channel.basic_publish(exchange='', routing_key='parser_clear_data', body='')
    try:
        if (auth):
            login = driver.find_element_by_name('login')
            login.send_keys('u.kostin')
            passwd = driver.find_element_by_name('password')
            passwd.send_keys('ukos18')
            driver.find_element_by_id("logon").click()
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-test-id='Cashier']"))).click()
            time.sleep(5)
            driver.find_element_by_class_name("sc-gtssRu").click()
            time.sleep(5)
            alert = driver.switch_to.alert.accept()
            time.sleep(5)
            driver.find_element_by_class_name("sc-jSFkmK").click()
        while True:
            print("FIND ELEMENTS")
            orders = []
            for block in driver.find_elements_by_class_name('sc-gtssRu'):
                id_order = block.find_element_by_class_name('sc-hxyAyv jRezsW')
                status = block.find_element_by_class_name('sc-iTVIwl')
                time_order = block.find_element_by_class_name('sc-eYKbNw')
                print('GET INFORMATION')
                order = {}
                order['order'] = id_order.text
                order['time'] = time_order.text
                print(id_order.text)
                status_text = status.text
                if (status_text == 'Принят'):
                    order['status'] = "1"
                elif (status_text == 'В процессе'):
                    order['status'] = "2"
                elif (status_text == 'Готов'):
                    order['status'] = "3"
                else:
                    order['status'] = ""
                print(status.text)
                order['rfid'] = ""
                order['number'] = ""
                orders.append(order)
            massage = json.dumps(orders)
            channel.basic_publish(exchange='', routing_key='parser_data', body=massage)
            time.sleep(30)
    except TimeoutException:
        print("error")

if __name__ == "__main__":
    driver = init_driver()
    print("INIT DRIVER")
    connection = init_connection()
    channel = connection.channel()
    channel.queue_declare(queue='parser_data')
    channel.queue_declare(queue='parser_clear_data')
    print("INIT CHANNEL, QUERE")
    lookup(driver, "Selenium", auth = True, host = HOST, channel = channel)
    time.sleep(5)
    driver.quit()
    connection.close()