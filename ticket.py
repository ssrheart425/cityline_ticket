import json
import time
import os

import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class CityLineTicket:

    def __init__(self, keys):
        self.ua = UserAgent()
        self.user_agent = self.ua.random
        self.keys = keys

    def save_cookies(self, browser_id="default"):
        """
        保存Cookies
        :param browser_id: 浏览器实例的唯一标识符
        """
        driver = uc.Chrome(headless=False, use_subprocess=False)
        driver.get("https://www.cityline.com")
        driver.delete_all_cookies()  # 清空初始Cookies
        # 手动登录
        # time.sleep(50)
        cookies = driver.get_cookies()

        # 确保目录存在
        os.makedirs("user_cookies", exist_ok=True)

        # 使用 browser_id 来区分不同的 cookies 文件
        cookie_file = f"user_cookies/cityline_cookies_{browser_id}.json"
        with open(cookie_file, "w") as f:
            json.dump(cookies, f)
        driver.close()

    def load_cookies(self, browser_id="default"):
        """
        加载Cookies
        :param browser_id: 浏览器实例的唯一标识符
        :return: cookies 列表
        """
        # 设置 ChromeOptions
        driver = uc.Chrome(headless=False, use_subprocess=False)
        driver.get("https://www.cityline.com")
        driver.delete_all_cookies()
        with open("user_cookies/cityline_cookies.json", "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.refresh()
        # 等待页面加载完成
        time.sleep(3)
        first_input_element = driver.find_element(
            By.XPATH, "/html/body/div[1]/div/div[2]/div[4]/div[2]/div/div/span/input"
        )
        first_input_element.send_keys(self.keys)
        time.sleep(2)
        first_input_element.send_keys(Keys.RETURN)
        time.sleep(2)
        search_first_div = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div[4]/div[5]")
        link = search_first_div.find_element(By.TAG_NAME, "a")
        link.click()
        time.sleep(3)

        # 获取所有标签页的句柄
        handles = driver.window_handles
        # 切换到最新打开的标签页
        driver.switch_to.window(handles[-1])

        # 等待页面加载完成
        time.sleep(2)
        # 点击前往购票按钮
        go_button = driver.find_element(By.XPATH, "/html/body/main/div[2]/section/div[4]/button")
        time.sleep(2)
        go_button.click()
        time.sleep(2)
        handles = driver.window_handles
        driver.switch_to.window(handles[-1])
        time.sleep(2)
        # 点击购买按钮
        buy_button = driver.find_element(By.XPATH, "/html/body/section/div/div/div[2]/div/div[4]/div[2]/button")
        time.sleep(2)
        buy_button.click()
        time.sleep(3)
        login_button = driver.find_element(By.XPATH, "/html/body/div[1]/section[1]/div/div/div/div[3]/button")
        login_button.click()
        time.sleep(3)
        driver.quit()


if __name__ == "__main__":
    cityline_ticket = CityLineTicket(keys="王若琳")
    # cityline_ticket.save_cookies()
    cityline_ticket.load_cookies()
