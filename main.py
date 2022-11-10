import os
import time
import json

import pandas as pd
import openpyxl
import undetected_chromedriver
from selenium import webdriver
from openpyxl.utils.dataframe import dataframe_to_rows
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from bs4 import BeautifulSoup


UA = UserAgent(verify_ssl=False)

data_folder = os.path.join(os.getcwd(), 'data')

if not os.path.exists(data_folder):
    os.mkdir(data_folder)

options = webdriver.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument(f'--user-agent={UA.chrome}')
options.add_argument('start-maximized')
options.add_argument('--headless')
options.add_argument('--enable-javascript')


def modified_url(link, name, folder):
    with open(os.path.join(folder, 'city_params.json'), 'r') as doc:
        params = json.load(doc)
        for param in params:
            if name == param['name']:
                modified_link = link.replace('profi.ru', f'{param["hostname"]}')

    return modified_link


def to_excel(profile, url):
    table_name = url.split('/')
    result_table = os.path.join(data_folder, f'{"_".join(table_name[2:5])}.xlsx')

    df = pd.DataFrame.from_dict(profile, orient='index')
    df = df.transpose()

    if os.path.isfile(result_table):
        workbook = openpyxl.load_workbook(result_table)
        sheet = workbook['result']

        for row in dataframe_to_rows(df, header=False, index=False):
            sheet.append(row)
        workbook.save(result_table)
        workbook.close()
    else:
        with pd.ExcelWriter(path=result_table, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='result')


def get_and_modified_data(url, c_name, doc_folder):
    service = Service(f'{os.getcwd()}/chromedriver')
    driver = undetected_chromedriver.Chrome(service=service, options=options)
    timeout = 3

    mod_url = modified_url(link=url, name=c_name, folder=doc_folder)

    result_dict = dict()
    print(mod_url)

    try:
        driver.get(mod_url)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, 'lxml')

        count_specialist = int(soup.find_all('li', class_='ui_1PoLy')[2].
                               find('span', class_='ui_1TyQ_').
                               find('span').text.strip())
        print(count_specialist)
        count_pages = count_specialist / 20

        if count_pages >= 100:
            pages = 100
        elif count_pages < 100 and type(count_pages) is float:
            pages = round(count_pages) + 1
        else:
            pages = count_pages

        profile_count = 1
        page_count = 1

        for page in range(1, pages + 1):
            print(f'Scan page №{page_count}...')
            mod_url = modified_url(link=url, name=c_name, folder=doc_folder) + f'&p={page}'
            print(mod_url)
            driver.get(mod_url)
            time.sleep(1)

            spec_soup = BeautifulSoup(driver.page_source, 'lxml')

            links_profile = list()

            desktop_profiles = spec_soup.find_all('div', class_='desktop-profile')
            for profile in desktop_profiles:
                link_profile = f"https://profi.ru/{profile.find('div', class_='ui_BgNKw').find('a').get('href')}"
                links_profile.append(link_profile)

            for link in links_profile:
                print(f'Scan profile №{profile_count}...')
                driver.get(link)
                time.sleep(1)

                try:
                    descript_price = WebDriverWait(driver, timeout).\
                        until(EC.element_to_be_clickable((By.XPATH, '//span[@class="_1rykDeJ"]')))

                    if descript_price:
                        descript_price.click()
                except Exception as ex:
                    # del ex
                    print(ex)

                profile_soup = BeautifulSoup(driver.page_source, 'lxml')

                with open(f'{os.path.join(data_folder, f"{c_name}.html")}', 'w') as file:
                    file.write(driver.page_source)

                profile_name = profile_soup.find('h1', attrs={'data-shmid': 'profilePrepName'}).text.strip()
                result_dict['Имя'] = [profile_name]

                profile_edu = profile_soup.find('div', attrs={'data-shmid': 'profileOIO'}).\
                    find_all('div', class_='_1Q9TGk6')

                person_edu = list()
                for edu in profile_edu:
                    truly_edu = edu.find('div', class_='ui-text').text.strip()
                    person_edu.append(truly_edu)
                result_dict['Образование'] = person_edu

                profile_service = list()
                profile_value = list()
                profile_ext = list()
                with open(f'{os.path.join(data_folder, f"{c_name}.html")}', 'r') as file:
                    src = file.read()

                    n_u = BeautifulSoup(src, 'lxml')

                    profile_price = n_u.find_all('table', class_='price-list desktop-profile__prices')[1].\
                        find_all('tr', attrs={'data-shmid': 'priceRow'})

                    if profile_price is None:
                        profile_price = n_u.find('div', class_='profile__section').find('table', class_='price-list'). \
                            find_all('tr', attrs={'data-shmid': 'priceRow'})

                    for price in profile_price:
                        item_name = price.find('td', class_='item_name').find('span').text.strip()
                        item_value = price.find('td', class_='item_value').text.strip()

                        profile_service.append(item_name)
                        profile_value.append(item_value)

                    result_dict['Услуга'] = profile_service
                    result_dict['Цена'] = profile_value

                    to_excel(profile=result_dict, url=mod_url)

                    # table_name = mod_url.split('/')
                    # result_table = os.path.join(data_folder, f'{"_".join(table_name[2:5])}.xlsx')
                    #
                    # df = pd.DataFrame.from_dict(result_dict, orient='index')
                    # df = df.transpose()
                    #
                    # if os.path.isfile(result_table):
                    #     workbook = openpyxl.load_workbook(result_table)
                    #     sheet = workbook['result']
                    #
                    #     for row in dataframe_to_rows(df, header=False, index=False):
                    #         sheet.append(row)
                    #     workbook.save(result_table)
                    #     workbook.close()
                    # else:
                    #     with pd.ExcelWriter(path=result_table, engine='openpyxl') as writer:
                    #         df.to_excel(writer, index=False, sheet_name='result')

                profile_count += 1
                time.sleep(1)
            page_count += 1

    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()


def main():
    enter_c_name = str(input('Enter the name of the city:\n> '))
    enter_url = str(input('Enter url:\n> '))
    get_and_modified_data(url=enter_url, c_name=enter_c_name, doc_folder=data_folder)


if __name__ == '__main__':
    main()
