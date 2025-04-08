import json
import time
import os

import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from my_logging import logger


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
        logger.info(f"打开浏览器 访问网站: https://www.cityline.com")
        driver.get("https://www.cityline.com")
        logger.info("清空初始Cookies")
        driver.delete_all_cookies()  # 清空初始Cookies
        # 手动登录
        time.sleep(50)
        logger.info("获取Cookies")
        cookies = driver.get_cookies()

        # 确保目录存在
        os.makedirs("user_cookies", exist_ok=True)
        logger.info(f"保存Cookies 到文件: user_cookies/cityline_cookies_{browser_id}.json")
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
        logger.info("删除所有cookies")
        driver.delete_all_cookies()
        logger.info("加载Cookies")
        with open("user_cookies/cityline_cookies.json", "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        logger.info("刷新页面")
        driver.refresh()
        # 等待页面加载完成
        time.sleep(1)
        logger.info("搜索关键字")
        first_input_element = driver.find_element(
            By.XPATH, "/html/body/div[1]/div/div[2]/div[4]/div[2]/div/div/span/input"
        )
        first_input_element.send_keys(self.keys)
        first_input_element.send_keys(Keys.RETURN)
        time.sleep(0.5)
        logger.info("点击搜索结果")
        search_first_div = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div[4]/div[5]")
        link = search_first_div.find_element(By.TAG_NAME, "a")
        link.click()
        logger.info("获取所有标签页的句柄")
        handles = driver.window_handles
        logger.info("切换到最新打开的标签页")
        driver.switch_to.window(handles[-1])

        # 等待页面加载完成
        time.sleep(1)
        logger.info("点击前往购票按钮")
        go_button = driver.find_element(By.XPATH, "/html/body/main/div[2]/section/div[4]/button")
        go_button.click()
        logger.info("切换到最新打开的标签页")
        handles = driver.window_handles
        driver.switch_to.window(handles[-1])
        time.sleep(1)
        logger.info("点击购买按钮")
        buy_button = driver.find_element(By.XPATH, "/html/body/section/div/div/div[2]/div/div[4]/div[2]/button")
        buy_button.click()
        time.sleep(3)
        logger.info("点击登入按钮")
        login_button = driver.find_element(By.XPATH, "/html/body/div[1]/section[1]/div/div/div/div[3]/button")
        login_button.click()
        time.sleep(2)
        logger.info("检测模态框是否存在")
        try:
            modal_elements = driver.find_elements(By.CSS_SELECTOR, "div.modal-content")
            if len(modal_elements) > 0:
                modal = modal_elements[0]
                logger.info("模态框存在,找到按钮点击")
                confirm_button = modal.find_element(
                    By.XPATH, "/html/body/div[1]/section[2]/div/div/div/div/div/button[1]"
                )
                confirm_button.click()
        except Exception as e:
            logger.info(f"模态框不存在")
        time.sleep(2)
        second_round_button = driver.find_element(
            By.XPATH, "/html/body/section[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div[2]/input"
        )
        second_round_button.click()
        dropdown_element = driver.find_element(
            By.XPATH, "/html/body/section[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[2]/div[2]/div[1]/select"
        )
        select = Select(dropdown_element)
        select.select_by_index(2)  # 选择第三个选项（索引从0开始）
        logger.info("点击快速购票按钮")
        quick_button = driver.find_element(By.XPATH, "/html/body/section[1]/div[2]/div/div[2]/div[2]/div[2]/button[2]")
        quick_button.click()
        time.sleep(5)
        visa_button = driver.find_element(
            By.XPATH, "/html/body/section[1]/div[3]/div[1]/form/div[2]/div[23]/div[1]/button[1]"
        )
        visa_button.click()
        visa_name = driver.find_element(By.XPATH, "/html/body/section[1]/div[3]/div[1]/form/div[2]/div[24]/input")
        visa_name.send_keys("heart")
        visa_card_number = driver.find_element(
            By.XPATH, "/html/body/section[1]/div[3]/div[1]/form/div[2]/div[25]/input"
        )
        visa_card_number.send_keys("424242424242424242424242424242")
        visa_expiry_date = driver.find_element(
            By.XPATH, "/html/body/section[1]/div[3]/div[1]/form/div[2]/div[26]/input"
        )
        visa_expiry_date.send_keys("11")
        time.sleep(0.5)
        visa_expiry_date.send_keys("29")
        visa_cvc = driver.find_element(By.XPATH, "/html/body/section[1]/div[3]/div[1]/form/div[2]/div[27]/input")
        visa_cvc.send_keys("333")
        time.sleep(300)
        driver.quit()


if __name__ == "__main__":
    keys = "王若琳"
    cityline_ticket = CityLineTicket(keys=keys)
    logger.info(f"开始执行 关键字：{keys}")
    # cityline_ticket.save_cookies()
    cityline_ticket.load_cookies()
