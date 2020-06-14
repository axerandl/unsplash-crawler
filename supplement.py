''' Tool for scraping data from Unsplash.com

author: Anthony Hung Nguen
date_created: 14/2/2019
'''

import time
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions
import urllib.request
import pathlib
import requests
import os

UNSPLASH = 1
PEXELS = 2


def scroll_webpage(driver, times):
    SCROLL_PAUSE_TIME = 1
    count = 0

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while count < times:
        # Scroll down to bottom
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

        count += 1


def extract_userinput(query, site):
    if site == UNSPLASH:
        url = "https://unsplash.com/s/photos/" + \
            query + "?orientation=portrait"
    elif site == PEXELS:
        url = "https://www.pexels.com/search/" + \
            query + "?orientation=portrait"
    return url


def extract_data(browser, url, scroll, css_selector):
    browser.get(url)
    if 'collections/' in url:
        load_more(browser)
        time.sleep(5)
    scroll_webpage(browser, scroll)
    time.sleep(2)
    return browser.find_elements_by_css_selector(css_selector)


def extract_and_save_imgs(site, browser, img_url, scroll, result_folder):
    # Save img
    # Make folder
    pathlib.Path(result_folder).mkdir(parents=True, exist_ok=True)

    pexels_selector = "img.photo-item__img"
    unsplash_selector = "a[itemprop='contentUrl']"

    if site == UNSPLASH:
        selector = unsplash_selector
    elif site == PEXELS:
        selector = pexels_selector

    imgs = extract_data(browser, img_url, scroll, selector)

    src = []
    if site == UNSPLASH:
        for img in imgs:
            try:
                img_id = img.get_attribute('href').split('/')[-1]
                src.append('https://unsplash.com/photos/' +
                           img_id + '/download?force=true')
            except exceptions.StaleElementReferenceException:
                pass
    elif site == PEXELS:
        for img in imgs:
            try:
                url = img.get_attribute('src')
                url = "https://static." + \
                    url.split("images.")[1].split("?")[0]
                src.append(url)
            except exceptions.StaleElementReferenceException:
                pass

    for url in src:
        if site == UNSPLASH:
            img_name = url.split('/')[-2] + '.jpg'
        elif site == PEXELS:
            img_name = url.split("/")[-1].split('-')[-1]

        while img_name.startswith('_') or img_name.startswith('-'):
            img_name = img_name[1:]

        print('Downloading %s' % img_name)

        try:
            image_data = requests.get(url)
        except requests.exceptions.RequestException as e:
            print('\tError: ' + e)
            pass

        # image_data = requests.get(url)
        # try:
        #     image_data.raise_for_status()
        # except Exception as e:
        #     print('There is a problem with this image: ' + e)

        image_file = open(result_folder + img_name, 'wb')

        for chunk in image_data.iter_content(100000):
            image_file.write(chunk)

        image_file.close()
        print('\tSuccess', end='\n\n')


def extract_href_and_name(browser, scroll):
    collections_href_selector = "div[data-test='collection-feed-card'] div:nth-child(1) div a"
    collections_url = 'https://unsplash.com/collections'
    # Selectors

    name = []
    href = []

    collections_href = extract_data(
        browser, collections_url, scroll, collections_href_selector)
    for collection in collections_href:
        url = collection.get_attribute('href')
        if url not in href:
            href.append(url)
            url_split = url.split('/')[-1].split('-')
            title = ''
            for url_s in url_split:
                title += url_s + ' '
            name.append(title.title().strip())

    return name, href


def load_more(browser):
    button = browser.find_element_by_xpath(
        "//button[@class='_37zTg _1l4Hh _1CBrG _3TTOE NDx0k _2Xklx']")
    print(button)
    browser.execute_script("arguments[0].click();", button)


def display_categories(browser):
    browser.get('https://unsplash.com/')
    categories = browser.find_elements_by_xpath(
        "//a[@class='SI2Kz _1CBrG xLon9']")
    for i in range(1, len(categories)):
        print('%d. %s' % (i, categories[i-1].text))
    while True:
        choice = int(input('Enter your choice: '))
        if choice >= 1 and choice <= len(categories):
            return categories[choice - 1]
        else:
            print('Incorrect choice. Please try again')
