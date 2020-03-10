"""
Importing the libraries that we are going to use
for loading the settings file and scraping the website
"""
import configparser
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from django.conf import settings



def load_settings():
    """
    Loading and assigning global variables from our settings.txt file
    """

    browser = settings.BROWSER
    browser_path = settings.BROWSER_PATH
    name = settings.NAME
    page = settings.PAGE

    setting = {
        'browser': browser,
        'browser_path': browser_path,
        'name': name,
        'page': page
    }
    return setting


def load_driver(settings, url, session_id):
    """
    Load the Selenium driver depending on the browser
    (Edge and Safari are not running yet)
    """
    driver = None
    if settings['browser'] == 'firefox':
        if driver:
            driver = webdriver.Remote(command_executor=url, desired_capabilities={})
            driver.session_id = session_id
        firefox_profile = webdriver.FirefoxProfile(settings['browser_path'])
        driver = webdriver.Firefox(firefox_profile)


    elif settings['browser'] == 'chrome':
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('user-data-dir=' +
                                    settings['browser_path'])
        driver = webdriver.Chrome(settings['browser_path'])
    elif settings['browser'] == 'safari':
        pass
    elif settings['browser'] == 'edge':
        pass

    url = driver.command_executor._url
    session_id = driver.session_id

    return driver


def search_chatter(driver, settings):
    """
    Function that search the specified user and activates his chat
    """

    while True:
        for chatter in driver.find_elements_by_xpath("//div[@class='X7YrQ']"):
            chatter_name = chatter.find_element_by_xpath(
                ".//span[contains(@class, '_19RFN')]").text
            if chatter_name == settings['name']:
                chatter.find_element_by_xpath(
                    ".//div[contains(@class,'_2UaNq')]").click()
                return


def read_last_in_message(driver):
    """
    Reading the last message that you got in from the chatter
    """
    message = ''
    emojis = []
    for messages in driver.find_elements_by_xpath(
            "//div[contains(@class,'message-in')]"):
        try:
            message = ""
            emojis = []

            message_container = messages.find_element_by_xpath(
                ".//div[@class='copyable-text']")

            message = message_container.find_element_by_xpath(
                ".//span[contains(@class,'selectable-text invisible-space copyable-text')]"
            ).text

            for emoji in message_container.find_elements_by_xpath(
                    ".//img[contains(@class,'selectable-text invisible-space copyable-text')]"
            ):
                emojis.append(emoji.get_attribute("data-plain-text"))

        except NoSuchElementException:  # In case there are only emojis in the message
            try:
                message = ""
                emojis = []
                message_container = messages.find_element_by_xpath(
                    ".//div[@class='copyable-text']")

                for emoji in message_container.find_elements_by_xpath(
                        ".//img[contains(@class,'selectable-text invisible-space copyable-text')]"
                ):
                    emojis.append(emoji.get_attribute("data-plain-text"))
            except NoSuchElementException:
                pass

    return message, emojis


def main(driver=None):
    """
    Loading all the configuration and opening the website
    (Browser profile where whatsapp web is already scanned)
    """

    settings = load_settings()
    url = ''
    session_id = ''
    if driver:
        url = driver.command_executor._url
        session_id = driver.session_id
    driver = load_driver(settings, url, session_id)
    driver.get(settings['page'])

    search_chatter(driver, settings)

    previous_in_message = None
    while True:
        last_in_message, emojis = read_last_in_message(driver)

        if previous_in_message != last_in_message:
            print(last_in_message, emojis)
            previous_in_message = last_in_message
            return previous_in_message, driver

        time.sleep(1)


if __name__ == '__main__':
    main()