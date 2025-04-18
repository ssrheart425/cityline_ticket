import json
import os
import time

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from my_logging import logger


def get_cityline_cookies(browser_id):
    """
    获取指定浏览器ID的cookies
    :param browser_id: 浏览器实例的唯一标识符
    """
    driver = uc.Chrome(use_subprocess=False)
    try:
        logger.info(f"开始获取浏览器 {browser_id} 的cookies")
        driver.get("https://www.cityline.com")
        logger.info("等待手动登录...")
        login_button = WebDriverWait(driver, 3, 0.1).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-login")))
        login_button.click()
        time.sleep(100)  # 等待手动登录

        # 确保目录存在
        os.makedirs("user_cookies", exist_ok=True)

        # 获取cookies
        cookies = driver.get_cookies()

        # 保存cookies到文件
        cookie_file = f"user_cookies/cityline_cookies_{browser_id}.json"
        with open(cookie_file, "w") as f:
            json.dump(cookies, f)
        logger.info(f"成功保存cookies到 {cookie_file}")

    except Exception as e:
        logger.error(f"获取cookies时出错: {str(e)}")
    finally:
        driver.quit()


def main():
    # 加载配置文件
    with open("config/config.json", "r") as f:
        configs = json.load(f)

    # 按顺序处理每个浏览器配置
    for config in configs:
        browser_id = config["browser_id"]
        logger.info(f"开始处理浏览器 {browser_id}")
        get_cityline_cookies(browser_id)
        logger.info(f"完成处理浏览器 {browser_id}")


if __name__ == "__main__":
    main()
