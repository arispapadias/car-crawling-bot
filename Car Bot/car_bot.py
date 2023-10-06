import time
import mysql.connector
import requests
import re

from mysql.connector import Error
from time import sleep
from selenium import webdriver
from bs4 import BeautifulSoup, NavigableString, Tag
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located



class CarBot():

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-notifications')
        self.driver = webdriver.Chrome(options=options)

      

    def open_page(self):
        self.driver.get("https://www.nissan.gr/vehicles/new-vehicles.html")
        self.driver.find_element(By.CSS_SELECTOR, ".burger").click()
        self.driver.find_element(By.XPATH, "//a[contains(text(),\'ΟΧΗΜΑΤΑ\')]").click()
        #self.driver.find_element(By.XPATH, "//button[@id=\'onetrust-accept-btn-handler\']").click()
        time.sleep(1)

    # εισάγουμε στην βάση τις κατηγορίες των αυτοκινήτων
    def category_db_insert(self):
        page = self.driver.page_source
        soup = BeautifulSoup(page, "html.parser")
        types = soup.find_all('ul', class_='categories')

        web_cat = []
        for j in soup.find_all('div', class_='vehicles-container'):
            if j is not None:
                x = (j.attrs['data-tabname'])
                y = str(x)
                web_cat.append(y)

        try:
        #Σύνδεση με βάση
            connection = mysql.connector.connect(host='localhost',
                                             database='nissan',
                                             user='root',
                                             password='')
            cursor = connection.cursor()
            names_of_cat = []

            for record in types:
                temp = str(record.text)
                temp = re.split('\n|\n\n', temp)
                temp = [x for x in temp if x!= ""]
                names_of_cat += temp
            #print(names_of_cat)

            for i in range(len(names_of_cat)):
                num_id = i+1                 
                name_of_cat = names_of_cat[i]
                web_categories = web_cat[i]                 
                url = "null"
                descr = "null"
                mySql_insert_query = """INSERT INTO car_categories (id, name, web_categories, url, Description) 
                                                VALUES (%s, %s, %s, %s, %s) """

                cursor.execute(mySql_insert_query, (num_id, name_of_cat, web_categories,  url, descr))
            
            connection.commit()
            print("Τα στοιχεία καταγράφηκαν επιτυχώς")

        except mysql.connector.Error as error:
            print("Τα στοιχεία ΔΕΝ καταγράφηκαν {}".format(error))
        finally:
            if (connection.is_connected()):
                cursor.close()
                connection.close()
                print("Το MySQL έκλεισε")

        sleep(3)
        return web_cat

    #παίρνουμε τo URL των αυτοκινήτων
    def car_urls(self):
        page = self.driver.page_source
        soup = BeautifulSoup(page, "html.parser")
        car_url = soup.find_all('a', class_='vehicle-block', href=True)
        cars_url = []
        new_cars_url = []
        for a in car_url:
            for z in a.get_attribute_list('href'):
                temp = str('https://www.nissan.gr'+ z)
                temp = re.split('\n|\n\n', temp)
                temp = [x for x in temp if x!= ""]
                for i in temp:
                    if i not in cars_url:
                        cars_url += temp
        return cars_url

    #παιρνουμε την τιμη των αυτοκινήτων
    def car_price(self, cars_url):   
        price = []
        for i in range(len(cars_url)):
            with requests.Session() as session:
                post = session.post(cars_url[i])
                r = session.get(cars_url[i])
            soup = BeautifulSoup(r.content, "html.parser")
            sleep(2)

            price_soup = soup.select_one("#individualVehiclePriceJSON")
            if price_soup is None:
                price.append("null")
            else:
                record = price_soup.text
                record = record.strip()
                index = record.find("modelPrice")
                chars_to_skip = len("modelPrice") + 3
                temp = record[index + chars_to_skip : ]
                temp = temp.split("\",\"")
                temp = temp[0]
                temp = str(temp)
                price.append(temp)

        return price

    # Παίρνουμε το όνομα των αυτοκινήτων
    def cars_Insert(self):       
        page = self.driver.page_source
        soup = BeautifulSoup(page, "html.parser")
        cars = soup.find_all('a', class_='vehicle-block')     
        cars_names = []
        for x in cars:
            for z in x.find_all('label'):                
                temp = str(z.text)
                temp = re.split('\n|\n\n', temp)
                temp = [y for y in temp if x!= ""]
                for i in temp:
                    if i not in cars_names:
                        cars_names += temp

        return cars_names
  
    # Παίρνουμε την φώτο των αυτοκινήτων
    def car_imgs(self):
        page = self.driver.page_source
        soup = BeautifulSoup(page, "html.parser")
        car_img = []
        for cars_images in soup.findAll('div', {"class": "vehicle-block-wrapper"}):
                for x in cars_images.findAll('a', {'class': 'vehicle-block'}):
                    for img in x.findAll('img',src=True):
                        temp = str(img['src'])
                        temp = re.split('\n|\n\n', temp)
                        temp = [x for x in temp if x!= ""]
                        for i in temp:
                            if i not in car_img:
                                car_img += temp

        #print(len(car_img))
        #print(car_img)

        return car_img

    # Παίρνουμε την περιγραφή των αυτοκινήτων
    def car_description(self, cars_names):
        REQUEST_URL = f"https://www.nissan.gr/vehicles/new-vehicles.html"
        with requests.Session() as session:
            post = session.post(REQUEST_URL)
            r = session.get(REQUEST_URL)
        soup = BeautifulSoup(r.content, "html.parser")

        description = []
        for x in soup.find_all("p", class_="vehicle-strapline"):
            record = x.find_all("a"):
            description.append(record.text)
        for i in range(0,6):
            description.append("δεν υπάρχει περιγραφή")

        return description
        
    # Παίρνουμε την κατηγορία κάθε αυτοκινήτου
    def category_for_cars(self, cars_names):
        web_cat = []
        car_i =[]
        car_names_per_category = {}
        car_fst = []

        page = self.driver.page_source
        soup = BeautifulSoup(page, "html.parser")
        # Loop over categories
        for j in soup.find_all('div', class_='vehicles-container'):
            if j is not None:
                x = (j.attrs['data-tabname'])
                cat_str = str(x)
                web_cat.append(cat_str)
                car_names_per_category[cat_str] = []

            
            for cars in j.find_all('a', class_='vehicle-block'):
                car_label = cars.find_all('label')[0]
                temp = str(car_label.text)
                temp = re.split('\n|\n\n', temp)
                temp = [y for y in temp if y!= ""]
                car_name = temp
                car_name = car_name[0]
                car_names_per_category[cat_str].append(car_name)

        for i in range(len(cars_names)):
            for key in car_names_per_category:
                if cars_names[i] in format(car_names_per_category[key]):
                    car_fst.append(key)
                else:
                    pass

            if len(car_fst) == 2:
                p = car_fst[0] + ", " + car_fst[1]
                car_i.append(p)
            else:
                p = car_fst[0]
                car_i.append(p)
            
            car_fst = []

        return car_i

    # εισάγουμε στην βάση τα στοιχεία των αυτοκινήτων
    def insert_cars_in_db(self, cars_names, car_img, cars_url, description, price, car_i):

        try:
        #Σύνδεση με βάση
            connection = mysql.connector.connect(host='localhost',
                                             database='nissan',
                                             user='root',
                                             password='')
            
            cursor = connection.cursor()
            car_name = []
            cars_imgs =[]
            car_url = []
            cars_description = []
            c_price = []
            web_categories = []

            for i in range(len(cars_names)):
                car_id = i+1                
                car_name = cars_names[i]
                cars_imgs = car_img[i] 
                car_url = cars_url[i]              
                c_price = price[i]
                web_categories = car_i[i]
                cars_description = description[i]
                mySql_insert_query = """INSERT INTO car (Id, Name, web_categories, image, Url, price, Description) 
                                                VALUES (%s, '%s', '%s', '%s', '%s', %s, '%s') """

                cursor.execute(mySql_insert_query%(car_id, car_name, web_categories, cars_imgs, car_url, c_price, cars_description))

            
            connection.commit()
            print("Τα στοιχεία καταγράφηκαν επιτυχώς")

        except mysql.connector.Error as error:
            print("Τα στοιχεία ΔΕΝ καταγράφηκαν {}".format(error))
        finally:
            if (connection.is_connected()):
                cursor.close()
                connection.close()
                print("Το MySQL έκλεισε")


bot = CarBot()

open_page = bot.open_page()
web_cat = bot.category_db_insert()
cars_names = bot.cars_Insert()
car_img = bot.car_imgs()
cars_url = bot.car_urls()
description = bot.car_description(cars_names)
price = bot.car_price(cars_url)
car_i = bot.category_for_cars(cars_names)
insert_cars_in_db = bot.insert_cars_in_db(cars_names,car_img,cars_url,description,price,car_i)

