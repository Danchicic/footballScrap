from selenium.webdriver.common.by import By

from scrapper.db import match_db


def get_match_id_from_url(match_url):
    spl = match_url.split('/')
    i1 = spl.index('#')
    return spl[i1 - 1]


def delete_rows(url, driver):
    driver.get(url=url)
    # print(url, get_match_id_from_url(url))
    try:
        match_status = driver.find_element(By.CLASS_NAME, 'detailScore__status').text
    except Exception as ex:
        match_status = '?'
    if match_status == 'ЗАВЕРШЕН':
        match_db.delete_row_by_id(match_id=get_match_id_from_url(url))
    else:
        print(match_status)
    driver.close()


def delete_past_rows(driver):
    for url in match_db.get_urls():
        if url[0] is not None and url[0] != 'https':
            url = url[0]
            delete_rows(url, driver)
        else:
            continue
