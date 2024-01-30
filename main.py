import re
import time

import chromedriver_autoinstaller
import fake_useragent
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
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
    driver.implicitly_wait(1)
    time.sleep(1)
    # mute notifications
    try:
        s = driver.find_element(By.CLASS_NAME, 'tabs__sound')
        ActionChains(driver).click(s).perform()
        time.sleep(1)
    except Exception as ex:
        print(ex)
        print("cant mute notifications")


def accept_cookies():
    temp = driver.find_element(By.ID, 'onetrust-button-group')
    ActionChains(driver).click(temp).perform()


def open_countries():
    """maybe working"""
    offset = 500
    countries = driver.find_elements(By.CLASS_NAME, '_simpleText_1d7gd_5')
    count_countries = len(countries)
    for i, country_arrow in enumerate(countries):
        if i - 1 == count_countries // 2:
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight / 2)")

        try:
            offset += 15 * int(country_arrow.text.split('(')[-1][:-1])
        except Exception as ex:
            print(ex)

        if 'показать игры' in country_arrow.text:
            ActionChains(driver).click(country_arrow).perform()
            driver.execute_script(f"window.scrollTo(0, {offset});")
            time.sleep(0.5)
            offset += 150
        else:
            print('not if ', country_arrow.text)
    print('all is clicked')


def open_every_match():
    offset = 500
    for match in driver.find_elements(By.CLASS_NAME, 'event__match'):
        ActionChains(driver).click(match).perform()
        driver.execute_script(f"window.scrollTo(0, {offset})")
        offset += 50


def check_matches_for_needed_stat():
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        ans = test(driver)
        if ans == 'skip_window':
            continue
        elif ans is None:
            pass
        elif isinstance(ans, """my type"""):
            pass
            # await bot func


def test(driver):
    '''getting page with match and returning statistic
    '''
    f = 0
    # open statistic table
    try:
        all_buttons = driver.find_element(By.CLASS_NAME, "filterOver").find_elements(By.TAG_NAME, 'a')
    except NoSuchElementException:
        print(driver.current_url)
        print('cant find row with statistic')
        time.sleep(3)
        driver.close()
        return "skip_window"

    for button in all_buttons:
        if button.text == 'СТАТИСТИКА':
            ActionChains(driver).click(button).perform()
            f = 1
            break
    if f == 0:
        # match without statistic
        """close this window"""
        driver.close()
        return None

    soup = BeautifulSoup(driver.page_source, 'lxml')
    """choose Тайм игры"""
    time.sleep(1)
    for button in driver.find_elements(By.TAG_NAME, 'button'):
        if button.text == '2-Й ТАЙМ':
            # choosing second time
            ActionChains(driver).click(button).perform()
            break
        elif button.text == '1-Й ТАЙМ':
            ActionChains(driver).click(button).perform()
            """DELETE BREAK"""
            # saving now count
            now_team_count = soup.find('div', class_='detailScore__wrapper')
            team1_count, team2_count = now_team_count.text.split('-')
        else:
            pass
    # saving first time statistic
    if soup.find('div', class_='detailScore__status').text == 'Перерыв':
        now_team_count = soup.find('div', class_='detailScore__wrapper')
        team1_count, team2_count = now_team_count.text.split('-')
        """database (Первый Тайм) save
        team1  ,team2 , count1, count2, current_time
        """

    ## filtering statistics
    # finding stat table
    s = soup.find('div', class_='section')
    team1_xg = team1_danger = 0
    team2_xg = team2_danger = 0
    for stat in s.find_all('div', class_='_row_rz3ch_9'):
        # matching needed data and getting data from <number><text><number>
        try:
            split_row = re.match(r'(\d+\.?\d*)(\D+)(\d+\.?\d*)', stat.text)
            team1_stat = split_row.group(1)
            name_stat = split_row.group(2)
            team2_stat = split_row.group(3)
        except AttributeError:
            print('Статистика пока не появилась')
            print(stat.text)
            time.sleep(54456)
            return "skip_window"

        if name_stat == 'Ожидаемые голы (xG)':  # get xG
            team1_xg = team1_stat
            team2_xg = team2_stat
        if name_stat == 'Опасные атаки':  # get danger attacks
            team1_danger = team1_stat
            team2_danger = team2_stat

    if (team1_xg == 0 and team2_xg == 0) or (team2_danger == 0 and team2_danger == 0):
        return "skip_window"

    team1_count, team2_count = 0, 0  # TAKE FROM DATA BASE
    team1_X = team1_xg + team1_danger / 100 - team1_count
    team2_X = team2_xg + team2_danger / 100 - team2_count
    if team1_X >= 1:
        '''return datatype'''
        pass
    elif team2_X >= 1:
        pass
    return "skip_window"


def main():
    open_main_page()
    accept_cookies()
    open_countries()
    open_every_match()
    check_matches_for_needed_stat()


if __name__ == '__main__':
    main()
