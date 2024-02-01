from __future__ import annotations

import asyncio
import random
import re
import time

from bot.handlers.test_handler import send_forecast_to_channel
from bot.my_types import ChannelAnswerType
from scrapper.db import match_db
from scrapper.db.database_controller import MatchRow, MatchStat

import chromedriver_autoinstaller
import fake_useragent
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException
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
# global consts
original_window: str = ''
start_unix = 0


def open_main_page(url='https://www.flashscorekz.com/?rd=flashscore.ru.com#!/'):
    global original_window, start_unix
    start_unix = time.time()
    if url:
        driver.get(url=url)
        time.sleep(1)
        driver.implicitly_wait(1)
        original_window = driver.current_window_handle
        # mute notifications
        try:
            s = driver.find_element(By.CLASS_NAME, 'tabs__sound ')
            ActionChains(driver) \
                .click(s) \
                .perform()
            time.sleep(1)
        except Exception:
            print("cant mute notifications")
    time.sleep(0.5)
    # click to live matches
    driver.find_elements(By.CLASS_NAME, 'filters__tab')[1].click()
    time.sleep(0.5)


def accept_cookies():
    try:
        temp = driver.find_element(By.ID, 'onetrust-button-group')
        ActionChains(driver) \
            .click(temp) \
            .perform()
    except ElementNotInteractableException:
        print("cookies is already accepted")
    except NoSuchElementException:
        print("cookies is already accepted")


def open_countries():
    for clickable in driver.find_elements(By.CLASS_NAME, '_simpleText_1d7gd_5'):
        ActionChains(driver) \
            .click(clickable) \
            .perform()
        time.sleep(1)


def open_every_match():
    print("iam calling", 'open matches')
    offset = 500
    for match in driver.find_elements(By.CLASS_NAME, 'event__match'):
        match_id = match.get_attribute('id').split('_')[-1]
        res = match_db.check_match_id(match_id)
        if res is not None and res[0] == 'nostat':
            continue
        try:
            name = match.find_elements(By.CLASS_NAME, 'event__participant')
            team1_name = name[0].text
            team2_name = name[1].text
        except NoSuchElementException:
            print("cant find element with .event_participant")
            continue
        except Exception as ex:
            print("Unexpected error in open_every_match", ex)
            continue

        match_url = f"https://www.flashscorekz.com/match/{match_id}/#/match-summary"
        match_db.write_data(MatchRow(match_id=match_id, match_url=match_url, team1=team1_name, team2=team2_name))
        print(team1_name, match_id, match_url)

        ActionChains(driver) \
            .click(match) \
            .perform()
        driver.execute_script(f"window.scrollTo(0, {offset})")
        offset += 50
    # print("all is opened")


def get_match_id_from_url(match_url):
    spl = match_url.split('/')
    i1 = spl.index('#')
    return spl[i1 - 1]


async def check_matches_for_needed_stat():
    global start_unix
    while 1:
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            match_url = driver.current_url

            try:
                match_id = get_match_id_from_url(match_url)
            except ValueError:
                continue

            match_db.write_new_match(match_id=match_id)

            ans = test(driver, match_id, match_url)

            # print('some wrong with statistic function', ex)
            # continue

            if ans == 'skip_window':
                continue
            elif ans is None:
                match_db.delete_row_by_id(match_id=match_id)
            elif isinstance(ans, ChannelAnswerType):
                # print('Я очень хотел отправит это сообщение', ans)
                await send_forecast_to_channel(ans)
                driver.close()
        now_unix = time.time()
        if len(driver.window_handles) == 1 or now_unix - start_unix >= 5 * 60:
            print("Нет открытых матчей или статистика пока не обновилась")
            time.sleep(60 * random.randint(4, 6))
            driver.switch_to.window(original_window)
            open_countries()
            open_every_match()
            start_unix = now_unix


def test(driver, match_id, match_url) -> str | None | ChannelAnswerType:
    '''
    asking page with match and returning statistic
    '''
    f = 0
    status = match_db.return_status_by_id(match_id)
    if status == "nostat":
        return "skip_window"
    # open statistic table
    try:
        all_buttons = driver.find_element(By.CLASS_NAME, "filterOver").find_elements(By.TAG_NAME, 'a')
    except NoSuchElementException:
        time.sleep(3)
        driver.close()
        match_db.update_status(MatchStat(match_id=match_id, status='nostat'))
        return "skip_window"
    try:
        for button in all_buttons:
            if button.text == 'СТАТИСТИКА':
                ActionChains(driver) \
                    .click(button) \
                    .perform()
                f = 1
                break
    except Exception as ex:
        match_db.update_status(MatchStat(match_id=match_id, status='wait_for_stat'))
        print("cant find button <Статистика>")

    if f == 0:
        # match without statistic
        driver.close()
        match_db.update_status(
            MatchStat(match_id=match_id, status="nostat")
        )
        return None
    soup = BeautifulSoup(driver.page_source, 'lxml')
    match_db.update_status(MatchStat(match_id=match_id, status='wait_for_stat'))
    team1_name = team2_name = ''
    try:
        block_with_team_names = soup.find('div', class_='duelParticipant')
        team1, team2 = block_with_team_names.find_all('a', class_='participant__participantName')
        team1_name = team1.text
        team2_name = team2.text
        match_db.write_data(MatchRow(team1=team1_name, team2=team2_name, match_id=match_id, match_url=match_url))
    except Exception as ex:
        print("cant find names of teams", ex)

    # saving first time statistic
    time.sleep(1)
    try:
        if soup.find('div', class_='detailScore__status').text == 'Перерыв':
            now_team_count = soup.find('div', class_='detailScore__wrapper')
            team1_count, team2_count = now_team_count.text.split('-')
            match_db.first_time_update_data(
                MatchStat(team1_count=team1_count, team2_count=team2_count, status='first_time_stat',
                          match_id=match_id))
    except Exception as ex:
        print('error in soup find перерыв', ex)
    try:
        match_country, championship = soup.find('span', class_='tournamentHeader__country').text.split(':')
    except Exception as ex:
        print("cant find match_country and championship", ex)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    try:
        now_match_time = driver.find_element(By.CLASS_NAME, 'eventTime').text
    except Exception as ex:
        print('Не удалось найти время первым способом', ex)
        try:
            now_match_time = soup.find('span', class_='eventTime').text
        except Exception as ex:
            print("Не удалось найти время вторым способом")
        match_db.update_status(MatchStat(match_id=match_id, status="cant_find_match_minute"))
        return "skip_window"

    second_time: bool = False
    team1_count = 0
    team2_count = 0

    for button in driver.find_elements(By.TAG_NAME, 'button'):
        try:
            if button.text == '2-Й ТАЙМ':
                # choosing second time
                ActionChains(driver) \
                    .click(button) \
                    .perform()
                second_time = True
                now_team_count = soup.find('div', class_='detailScore__wrapper')
                try:
                    team1_count, team2_count = map(int, now_team_count.text.split('-'))
                except Exception as ex:
                    print("cant split score from second time", ex)
                break
            elif button.text == '1-Й ТАЙМ':
                ActionChains(driver) \
                    .click(button) \
                    .perform()
                # saving now count
                now_team_count = soup.find('div', class_='detailScore__wrapper')
                try:
                    team1_count, team2_count = map(int, now_team_count.text.split('-'))
                except Exception as ex:
                    print("cant split teams score from first time", ex)
        except Exception as ex:
            print("cant find <1-й ТАЙМ> or <2-й ТАЙМ>", ex)
        time.sleep(0.25)
    team1_first_count, team2_first_count = 0, 0
    if second_time:
        team1_first_count, team2_first_count = map(int, match_db.get_first_time_stat(match_id=match_id))

    ## filtering statistics
    # finding stat table
    # s = soup.find('div', class_='section')
    print("Перехожу к сбору данных из таблички")
    team1_xg = team1_danger = 0
    team2_xg = team2_danger = 0
    soup = BeautifulSoup(driver.page_source, 'lxml')
    for stat in soup.find_all('div', class_='_row_rz3ch_9'):
        try:
            # matching needed data and getting data from <number><text><number>
            split_row = re.match(r'(\d+\.?\d*)(\D+)(\d+\.?\d*)', stat.text)
            team1_stat = split_row.group(1)
            name_stat = split_row.group(2)
            team2_stat = split_row.group(3)
        except AttributeError:
            match_db.update_status(MatchStat(match_id=match_id, status="wait for xG"))
            return "skip_window"

        if name_stat == 'Ожидаемые голы (xG)':  # get xG
            team1_xg = float(team1_stat)
            team2_xg = float(team2_stat)

        if name_stat == 'Опасные атаки':  # get danger attacks
            team1_danger = int(team1_stat)
            team2_danger = int(team2_stat)

    if (team1_xg == 0 or team2_xg == 0) or (team2_danger == 0 and team2_danger == 0):
        return "skip_window"
    if team1_count is None or team2_count is None:
        print('UnexpectedError')
        return "skip_window"
    team1_X = (team1_xg + team1_danger / 100) - (team1_count - team1_first_count)
    team2_X = (team2_xg + team2_danger / 100) - (team2_count - team2_first_count)
    print(team1_X, team2_X, team1_name, team2_name, match_url)
    if team1_X >= 1:
        return ChannelAnswerType(country=match_country,
                                 championship=championship,
                                 team1=team1_name,
                                 team2=team2_name,
                                 team1_score=team1_count,
                                 team2_score=team2_first_count,
                                 match_minute=now_match_time,
                                 forecast_team=team1_name
                                 )

    elif team2_X >= 1:
        driver.close()
        return ChannelAnswerType(country=match_country,
                                 championship=championship,
                                 team1=team1_name,
                                 team2=team2_name,
                                 team1_score=team1_count,
                                 team2_score=team2_first_count,
                                 match_minute=now_match_time,
                                 forecast_team=team2_name
                                 )
    return "skip_window"


async def main():
    try:
        # first block
        open_main_page()
        accept_cookies()
        open_countries()
    except Exception as ex:
        print('Ошибка в первом блоке', ex)
    try:
        # second block
        open_every_match()
    except Exception as ex:
        print('error in second block', ex)
    # try:
    # third block
    await check_matches_for_needed_stat()
    # except Exception as ex:
    #     print('error in third block', ex)


if __name__ == '__main__':
    asyncio.run(main())
