import time

import chromedriver_autoinstaller
import fake_useragent
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

# generate fake useragent
user = fake_useragent.UserAgent().random

# collecting options
options = webdriver.ChromeOptions()
# options.add_argument("--headless")
options.add_argument(f"user-agent={user}")
options.add_argument("--start-maximized")

# downloading webdriver
chromedriver_autoinstaller.install()

# initializing webdriver via options
driver: webdriver = webdriver.Chrome(options=options)


def open_main_page():
    driver.get(url="https://www.flashscorekz.com/?rd=flashscore.ru.com#!/")
    driver.find_elements(By.CLASS_NAME, 'filters__tab')[1].click()
    # mute notifications
    try:
        driver.find_element(By.CLASS_NAME, 'tabs__sound').click()
        time.sleep(1)
    except Exception as ex:
        print(ex)
        print("cant mute notifications")


def open_countries():
    offset = 500
    for country_arrow in driver.find_elements(By.CLASS_NAME, 'event__info'):
        if 'показать игры' in country_arrow.text:
            print(country_arrow.text)
            ActionChains(driver).click(country_arrow).perform()
            driver.execute_script(f"window.scrollTo(0, {offset})")
            time.sleep(0.5)
            offset += 50
        else:
            print('not if ', country_arrow.text)
    print('all is clicked')


def open_every_match():
    offset = 500
    for match in driver.find_elements(By.CLASS_NAME, 'event__match'):
        ActionChains(driver).click(match).perform()
        driver.execute_script(f"window.scrollTo(0, {offset})")
        offset += 20


def check_matches_for_xG():
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        print(driver.current_url)


def main():
    open_main_page()
    open_countries()
    open_every_match()
    check_matches_for_xG()


if __name__ == '__main__':
    main()
