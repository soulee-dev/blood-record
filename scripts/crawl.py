#!/usr/bin/env python3

import json
import os
import re
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def log(msg):
    print(f"[*] {msg}", file=sys.stderr, flush=True)


def create_driver():
    log("Chrome 드라이버 준비 중...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    log("Chrome 드라이버 준비 완료")
    return driver


def login(driver, user_id, password):
    log("로그인 페이지 접속 중...")
    driver.get("https://bloodinfo.net/knrcbs/lo/login/loginPage.do")
    wait = WebDriverWait(driver, 15)

    id_input = wait.until(EC.presence_of_element_located((By.ID, "member_id")))
    id_input.clear()
    id_input.send_keys(user_id)

    pw_input = driver.find_element(By.ID, "member_pwd")
    pw_input.clear()
    pw_input.send_keys(password)

    log("로그인 시도 중...")
    login_btn = driver.find_element(By.CSS_SELECTOR, "button.btnLogin")
    login_btn.click()

    wait.until(EC.url_changes("https://bloodinfo.net/knrcbs/lo/login/loginPage.do"))
    log("로그인 성공")


def crawl_records(driver):
    log("헌혈 기록 페이지 접속 중...")
    driver.get("https://bloodinfo.net/knrcbs/br/rcord/bldRcordList.do?mi=1107")
    wait = WebDriverWait(driver, 15)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".box_st1")))
    log("헌혈 기록 데이터 파싱 중...")

    # 총 헌혈 횟수: <span class="pc_red">37</span>
    total_el = driver.find_element(By.CSS_SELECTOR, ".box_st1 h5.tit3 span.pc_red")
    total = int(total_el.text.strip().replace(",", ""))

    # 종류별: "전혈: 14회" 형태의 텍스트
    li_elements = driver.find_elements(By.CSS_SELECTOR, ".box_st1 ul.list_st3 li")
    breakdown = {}

    for li in li_elements[:5]:
        text = li.text.strip()  # ex) "전혈: 14회"
        m = re.match(r"(.+?):\s*(\d+)회", text)
        if m:
            label = m.group(1).strip()
            count = int(m.group(2))
            breakdown[label] = count

    log(f"파싱 완료 — 총 {total}회")
    return {"total": total, "breakdown": breakdown}


def main():
    user_id = os.environ.get("BLOODINFO_ID")
    password = os.environ.get("BLOODINFO_PW")

    if not user_id or not password:
        print("Error: BLOODINFO_ID and BLOODINFO_PW environment variables required.", file=sys.stderr)
        sys.exit(1)

    driver = create_driver()
    try:
        login(driver, user_id, password)
        data = crawl_records(driver)
        print(json.dumps(data, ensure_ascii=False))
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
