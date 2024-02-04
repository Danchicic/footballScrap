from __future__ import annotations
import re

import asyncio
import time

from update_database import delete_past_rows
from bot.handlers.test_handler import send_forecast_to_channel
from bot.my_types import ChannelAnswerType
from scrapper.db import match_db
from scrapper.db.database_controller import MatchRow, MatchStat

import chromedriver_autoinstaller
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

# generate fake useragent
# user = fake_useragent.UserAgent().random
user = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
# collecting options
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument(f"user-agent={user}")
# options.add_argument("--start-maximized")

# downloading webdriver
chromedriver_autoinstaller.install()

# initializing webdriver via options
driver: webdriver = webdriver.Chrome(options=options)
# global consts
original_window: str = ''
start_unix = time.time()

DEBUG = False


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
    # double check
    for clickable in driver.find_elements(By.CLASS_NAME, '_simpleText_1d7gd_5'):
        ActionChains(driver) \
            .click(clickable) \
            .perform()
        time.sleep(1)
    # print("clicked")


def get_match_id_from_url(match_url):
    spl = match_url.split('/')
    i1 = spl.index('#')
    return spl[i1 - 1]


def open_every_match():
    offset = 500
    for match in driver.find_elements(By.CLASS_NAME, 'event__match'):
        try:
            match_id = match.get_attribute('id').split('_')[-1]
        except Exception:
            driver.switch_to.window(original_window)
            if DEBUG:
                with open(f'index_exception_{time.time()}.html', 'w+') as html_file:
                    html_file.write(str(driver.page_source))
            continue

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
        if team1_name == 'ГОЛ':
            if DEBUG:
                with open("Гол error", 'w+') as new_f:
                    new_f.write(
                        f"{team1_name} - {team2_name}\n{match.find_elements(By.CLASS_NAME, 'event__participant')}")

            # match_db.write_data(MatchRow(match_id=match_id, match_url=match_url, team1=team1_name, team2=team2_name))
        else:
            match_db.write_data(MatchRow(match_id=match_id, match_url=match_url, team1=team1_name, team2=team2_name))
        print(team1_name, team2_name, match_id, match_url)

        ActionChains(driver) \
            .click(match) \
            .perform()
        driver.execute_script(f"window.scrollTo(0, {offset})")
        offset += 50
    print("all is opened")


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

            # match_db.write_new_match(match_id=match_id)

            ans = test(driver, match_id, match_url)

            # print('some wrong with statistic function', ex)
            # continue

            if ans == 'skip_window':
                continue
            elif ans is None:
                match_db.delete_row_by_id(match_id=match_id)
            elif isinstance(ans, ChannelAnswerType):
                await send_forecast_to_channel(ans)
                driver.close()
                match_db.update_status(MatchStat(match_id=match_id, status='nostat'))
        if len(driver.window_handles) == 1:
            print("Нет открытых матчей")
            driver.switch_to.window(original_window)
            open_countries()
            open_every_match()
            try:
                delete_past_rows(driver)
            except Exception:
                print("cant delete old rows")
        if time.time() - start_unix >= 3 * 60:
            open_every_match()
            start_unix = time.time()


def test(driver, match_id, match_url) -> str | None | ChannelAnswerType:
    '''
    asking page with match and returning statistic
    '''
    statistic_button = 0
    # if DEBUG:
    # with open(f"logs/log_{match_id}_{time.strftime('%m_%d-%H_%M_%S', time.localtime())}.txt", mode='w+',
    #           encoding='utf-8') as log_file_writer:
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
                statistic_button = 1
                break
    except Exception as ex:
        driver.close()
        match_db.update_status(MatchStat(match_id=match_id, status='nostat'))
        if DEBUG:
            log_file_writer.write("cant find button <Статистика>\n")
            print("cant find button <Статистика>")

    if statistic_button == 0:
        # match without statistic
        driver.close()
        match_db.update_status(
            MatchStat(match_id=match_id, status="nostat")
        )
        if DEBUG:
            log_file_writer.write("cant find button <Статистика>\n")
        return None
    soup = BeautifulSoup(driver.page_source, 'lxml')
    # match_db.update_status(MatchStat(match_id=match_id, status='getting_stat_from_table'))
    team1_name = team2_name = ''
    try:
        block_with_team_names = soup.find('div', class_='duelParticipant')
        team1, team2 = block_with_team_names.find_all('a', class_='participant__participantName')
        team1_name = team1.text
        team2_name = team2.text
        """update data"""
        match_db.write_data(MatchRow(team1=team1_name, team2=team2_name, match_id=match_id, match_url=match_url))
    except Exception as ex:
        if DEBUG:
            log_file_writer.write(f"cant find names of teams {ex}\n")
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
        if DEBUG:
            log_file_writer.write(f"error in soup find перерыв {ex}\n")
        print('error in soup find перерыв', ex)
    try:
        match_country, championship = soup.find('span', class_='tournamentHeader__country').text.split(':')
    except Exception as ex:
        print("cant find match_country and championship", ex)
        if DEBUG:
            log_file_writer.write(f"cant find match_country and championship {ex}\n")

    soup = BeautifulSoup(driver.page_source, 'lxml')
    try:
        now_match_time = driver.find_element(By.CLASS_NAME, 'eventTime').text
    except Exception as ex:
        print('Не удалось найти время первым способом', ex)
        try:
            now_match_time = soup.find('span', class_='eventTime').text
        except Exception as ex:
            print("Не удалось найти время вторым способом")
            if DEBUG:
                log_file_writer.write(f"Не удалось найти время вторым способом{ex}\n")
        # match_db.update_status(MatchStat(match_id=match_id, status="cant_find_match_minute"))
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
                    if DEBUG:
                        log_file_writer.write(f"cant split score from second time {ex}\n")
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
                    match_db.update_status(
                        MatchStat(match_id=match_id, status='now_first_time', team1_count=team1_count,
                                  team2_count=team2_count))
                except Exception as ex:
                    if DEBUG:
                        log_file_writer.write(f"cant split score from first time {ex}\n")
                    print("cant split teams score from first time", ex)
        except Exception as ex:
            print("cant find <1-й ТАЙМ> or <2-й ТАЙМ>", ex)
        time.sleep(0.25)
    team1_first_count, team2_first_count = 0, 0
    try:
        if second_time:
            team1_first_count, team2_first_count = map(int, match_db.get_first_time_stat(match_id=match_id))
    except TypeError:
        team1_first_count, team2_first_count = 0, 0
        if DEBUG:
            log_file_writer.write("нет информации по первому тайму\n")
        print("no info about first time")

    # finding stat table
    print("Перехожу к сбору данных из таблички")
    # log_file_writer.write("Перехожу к сбору данных из таблички\n")
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
            # match_db.update_status(MatchStat(match_id=match_id, status="wait for xG"))
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
    if DEBUG:
        log_file_writer.write(
            f'"<team1>", {team1_xg}, {team1_danger},минута матча: {now_match_time}, сейчас:{team1_count}, "первый тайм:"{team1_first_count}\n')
        log_file_writer.write(f'"<team2>", {team2_xg}, {team2_danger}, {team2_count}, {team2_first_count}\n')
        log_file_writer.write(f'{team1_X}, {team2_X}, {team1_name}, {team2_name}, {match_url}\n')
        print("<team1>", team1_xg, team1_danger, team1_count, team1_first_count)
        print("<team2>", team2_xg, team2_danger, team2_count, team2_first_count)
        print(team1_X, team2_X, team1_name, team2_name, match_url)
    if team1_X >= 1:
        # match_db.delete_row_by_id(match_id)
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
        # match_db.delete_row_by_id(match_id)
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
