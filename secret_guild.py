import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random

def get_character_info_from_nexon(character_name):
    url = f"https://maplestory.nexon.com/Ranking/World/Total?c={character_name}"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    rows = soup.select("table.ranking_table2 > tbody > tr")
    for row in rows:
        name_tag = row.select_one("a")
        if name_tag and name_tag.text.strip() == character_name:
            try:
                level = row.select("td")[1].text.strip()
                job = row.select("td")[2].text.strip()
                guild = row.select("td")[3].text.strip()
                return {
                    "character_name": character_name,
                    "guild": guild,
                    "job": job,
                    "level": level
                }
            except:
                continue
    return None

def get_guild_members_selenium(guild_name="악마", pages=7):
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    url = f"https://maplestory.nexon.com/N23Ranking/World/Guild?w=10&t=1&n={guild_name}"
    driver.get(url)

    member_names = []

    try:
        guild_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".guild_ranking_list tr td.left a"))
        )
        ActionChains(driver).move_to_element(guild_link).pause(1).click().perform()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".guild_user_list"))
        )

        for page_num in range(1, pages + 1):
            try:
                page_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, str(page_num)))
                )
                ActionChains(driver).move_to_element(page_link).pause(1).click().perform()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".guild_user_list"))
                )
                time.sleep(random.uniform(1.0, 1.8))

                users = driver.find_elements(By.CSS_SELECTOR, ".guild_user_list li span.name")
                member_names += [user.text.strip() for user in users if user.text.strip()]
            except Exception as e:
                print(f"❌ {page_num}페이지 오류:", e)
                continue

    except Exception as e:
        print("❌ 길드 상세 진입 실패:", e)

    driver.quit()
    return member_names
