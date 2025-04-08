# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from concurrent.futures import ThreadPoolExecutor

# # 创建一个执行任务的函数
# def fetch_data(url):
#     driver = webdriver.Chrome()
#     driver.get(url)
#     title = driver.title  # 获取页面的标题
#     print(f"Page title for {url}: {title}")
#     driver.quit()

# # 定义要抓取的多个URL
# urls = [
#     "https://baidu.com",
#     "https://jd.com",
#     "https://zhihu.com"
# ]

# # 使用 ThreadPoolExecutor 来并发执行多个任务
# with ThreadPoolExecutor(max_workers=3) as executor:
#     executor.map(fetch_data, urls)


import time

from selenium import webdriver

driver = webdriver.Chrome()  # 启动谷歌浏览器
driver.get("http://www.zhihu.com")  # 访问一个网页
time.sleep(5)
driver.quit()  # 退出浏览器
