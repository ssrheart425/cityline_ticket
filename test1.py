import time

import undetected_chromedriver as uc
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import WebDriverException

proxy = Proxy()
proxy.proxy_type = ProxyType.MANUAL
proxy.http_proxy = "http://89946fa3e89f4537:RNW78Fm5@res.proxy-seller.com:10002"
proxy.ssl_proxy = "http://89946fa3e89f4537:RNW78Fm5@res.proxy-seller.com:10002"

options = uc.ChromeOptions()
options.add_argument("--proxy-server=http://89946fa3e89f4537:RNW78Fm5@res.proxy-seller.com:10002")
driver = uc.Chrome(options=options)
try:
    driver.get("https://www.whatismyip.com/")
    print("页面加载成功")
except WebDriverException as e:
    print(f"加载页面失败: {e}")

time.sleep(100)

driver.quit()
