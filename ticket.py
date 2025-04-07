from selenium import webdriver

# from selenium.webdriver.chrome.options import Options
import time

# options = webdriver.ChromeOptions()
# options.add_experimental_option("detach", True)  # 浏览器不自动关闭


# driver = webdriver.Chrome(options=options)

# driver.get("http://www.cityline.com")  # 访问网页
# time.sleep(3)
# print("刷新")
# driver.refresh()
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import undetected_chromedriver as uc

ua = UserAgent()
user_agent = ua.random

if __name__ == "__main__":
    # 保存Cookies
    driver = uc.Chrome(headless=False, use_subprocess=False)
    driver.get("https://www.cityline.com")
    driver.delete_all_cookies()  # 清空初始Cookies[[6]]
    # 手动登录过程...
    time.sleep(100)
    cookies = driver.get_cookies()
    print(cookies)
    with open("cityline_cookies.json", "w") as f:
        json.dump(cookies, f)
    driver.quit()

    time.sleep(5)
    # 加载Cookies
    driver = uc.Chrome(headless=False, use_subprocess=False)

    driver.get("https://www.cityline.com")
    driver.delete_all_cookies()
    with open("cityline_cookies.json", "r") as f:
        cookies = json.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)

    time.sleep(5)
    driver.refresh()
    time.sleep(5)
    driver.quit()
