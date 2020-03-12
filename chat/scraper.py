"""
Importing the libraries that we are going to use
for loading the settings file and scraping the website
"""
import configparser
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from django.conf import settings
from .models import Message, Room, Chat
from django.contrib.auth.models import User


def create_driver_session(session_id, executor_url):
    from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

    # Save the original function, so we can revert our patch
    org_command_execute = RemoteWebDriver.execute

    def new_command_execute(self, command, params=None):
        if command == "newSession":
            # Mock the response
            return {'success': 0, 'value': None, 'sessionId': session_id}
        else:
            return org_command_execute(self, command, params)

    # Patch the function before creating the driver object
    RemoteWebDriver.execute = new_command_execute

    new_driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
    new_driver.session_id = session_id

    # Replace the patched function with original function
    RemoteWebDriver.execute = org_command_execute

    return new_driver


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
        if url and session_id:
            driver = create_driver_session(session_id, url)
        else:
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
                return chatter_name


def read_last_in_message(session_id = None, url=None):
    """
    Reading the last message that you got in from the chatter
    """
    message = ''
    timestamp = ''
    emojis = []
    driver = create_driver_session(session_id,url)
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

            timestamp_container = messages.find_element_by_xpath(
                ".//div[contains(@class,'_1RNhZ')]"
            )
            timestamp = timestamp_container.find_element_by_xpath(
                ".//span[contains(@class,'_3fnHB')]"
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
    settings = load_settings()
    user = ''
    for chatter in driver.find_elements_by_xpath("//div[@class='X7YrQ']"):
        chatter_name = chatter.find_element_by_xpath(
            ".//span[contains(@class, '_19RFN')]").text

        if chatter_name == settings['name']:
            user = chatter_name

    # user_a = User.objects.get(username=user)
    # room = Room.objects.get(user=user_a.username, room_name='a')
    # msg = Message(content=message, room=room, author=user_a)
    # msg.save()
    # Chat.objects.get_or_create(user=user_a.username, message=msg, room=room)
    return message, emojis, user, timestamp

def send_msg(session_id = None, url=None, msg=None):
    driver = create_driver_session(session_id, url)
    for messages in driver.find_elements_by_xpath(
            "//footer[contains(@class,'_1N6pS')]"):
        try:


            message = messages.find_element_by_xpath(
                ".//div[contains(@class,'_3u328 copyable-text selectable-text')]"
            )
            message.send_keys(msg)
            button = messages.find_element_by_xpath(
                ".//button[contains(@class,'_3M-N-')]"
            )
            button.click()
        except NoSuchElementException:
            pass

def main(url=None, session_id=None):
    """
    Loading all the configuration and opening the website
    (Browser profile where whatsapp web is already scanned)
    """

    settings = load_settings()
    driver = load_driver(settings, url, session_id)
    url = driver.command_executor._url
    session_id = driver.session_id
    driver.get(settings['page'])

    user = search_chatter(driver, settings)

    previous_in_message = None
    if url and session_id:
        while True:
            last_in_message, emojis, user, timestamp = read_last_in_message(session_id, url)

            if previous_in_message != last_in_message:
                previous_in_message = last_in_message
                # user_a = User.objects.get(username=user)
                # room = Room.objects.get(user=user_a.username, room_name='a')
                # msg = Message(content=last_in_message, room=room, author=user_a)
                # msg.save()
                # Chat.objects.get_or_create(user=user_a.username,message=msg, room=room)
                return url, session_id, driver
            time.sleep(1)
    else:
        return url, session_id, driver

if __name__ == '__main__':
    main()