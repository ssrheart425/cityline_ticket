import json
import time
import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from my_logging import logger


class CityLineTicket:

    def __init__(self, browser_id):
        self.browser_id = browser_id
        self.keys = self._load_config()
        logger.info(f"初始化CityLineTicket实例 - browser_id: {self.browser_id}, keys: {self.keys}")

    def _load_config(self):
        """
        加载配置文件
        :return: 返回对应browser_id的配置
        """
        try:
            logger.info(f"开始加载配置文件，查找browser_id: {self.browser_id}")
            with open("config/config.json", "r") as f:
                configs = json.load(f)
                logger.info(f"配置文件内容: {configs}")
                for config in configs:
                    if config["browser_id"] == self.browser_id:
                        logger.info(f"找到匹配的配置: {config}")
                        return config["keys"]
                raise ValueError(f"未找到browser_id为{self.browser_id}的配置")
        except FileNotFoundError:
            logger.error("配置文件不存在: config/config.json")
            raise
        except json.JSONDecodeError:
            logger.error("配置文件格式错误")
            raise
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            raise

    def _check_user_cookies(self, browser_id):
        if os.path.exists(f"user_cookies/cityline_cookies_{browser_id}.json"):
            return True
        else:
            return False

    def _save_cookies(self, browser_id):
        """
        保存Cookies
        :param browser_id: 浏览器实例的唯一标识符
        """
        driver = uc.Chrome(headless=False, use_subprocess=False)
        logger.info(f"打开浏览器 访问网站")
        driver.get("https://www.cityline.com")
        logger.info("清空初始Cookies")
        driver.delete_all_cookies()  # 清空初始Cookies
        # 手动登录
        login_button = WebDriverWait(driver, 3, 0.1).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-login")))
        login_button.click()
        time.sleep(50)
        try:
            login_button = WebDriverWait(driver, 3, 0.1).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-login")))
            login_button.click()
        except Exception as e:
            logger.info(f"登陆按钮不存在 error:{e}")
            driver.refresh()
        logger.info("获取Cookies")
        cookies = driver.get_cookies()

        # 确保目录存在
        os.makedirs("user_cookies", exist_ok=True)
        logger.info(f"保存Cookies 到文件: user_cookies/cityline_cookies_{browser_id}.json")
        # 使用 browser_id 来区分不同的 cookies 文件
        cookie_file = f"user_cookies/cityline_cookies_{browser_id}.json"
        with open(cookie_file, "w") as f:
            json.dump(cookies, f)
        driver.quit()

    def main_process(self, browser_id="default"):
        """
        加载Cookies
        :param browser_id: 浏览器实例的唯一标识符
        :return: cookies 列表
        """
        # 加载cookies 刷新页面
        driver = self._load_cookies_refresh(browser_id)
        # 等待页面加载完成
        time.sleep(0.5)
        # 搜索关键词
        self._search_keyword(driver)
        # 等待页面加载完成
        time.sleep(0.5)
        logger.info("点击前往购票按钮")
        self._click_go_button(driver)
        time.sleep(0.5)
        # 点击购票 登入 检查模态框
        self._check_model(driver)
        time.sleep(0.5)
        self._select_ticket(driver)
        self._visa_payment(driver)
        time.sleep(30000)
        driver.quit()

    def _load_cookies_refresh(self, browser_id):
        if not self._check_user_cookies(browser_id):
            self._save_cookies(browser_id)
        driver = uc.Chrome(headless=False, use_subprocess=False)
        driver.get("https://www.cityline.com")
        logger.info("删除所有cookies")
        driver.delete_all_cookies()
        logger.info("加载Cookies")
        with open(f"user_cookies/cityline_cookies_{browser_id}.json", "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        logger.info("刷新页面")
        driver.refresh()
        return driver

    def _switch_to_new_window(self, driver):
        handles = driver.window_handles
        driver.switch_to.window(handles[-1])
        return

    def _search_keyword(self, driver):
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
        logger.info("切换到最新打开的标签页")
        self._switch_to_new_window(driver)
        return

    def _click_go_button(self, driver):
        while True:
            try:
                # 直接查找父级div中的按钮
                parent_div = driver.find_element(By.CLASS_NAME, "buyTicketBox")
                go_button = parent_div.find_element(By.XPATH, ".//*[@id='buyTicketBtn']")
                go_button.click()
                logger.info("成功点击前往购票按钮")
                break

            except Exception as e:
                logger.info(f"未找到前往购票按钮 刷新重试")
                driver.refresh()
                time.sleep(0.1)

    def _check_model(self, driver):
        logger.info("切换到最新打开的标签页")
        self._switch_to_new_window(driver)
        time.sleep(5)
        # 获取当前页面标题
        current_title = driver.title
        logger.info(f"当前页面标题: {current_title}")
        time.sleep(0.5)
        # 当标题包含"Cityline"时继续循环
        while current_title == "Cityline":
            try:
                # 添加3-5秒的随机延迟
                random_delay = random.uniform(3, 4)
                logger.info(f"等待随机延迟: {random_delay:.2f}秒")
                time.sleep(random_delay)
                # 尝试多个可能的XPath路径
                button_xpaths = [
                    "/html/body/div[3]/div[1]/div/div[1]/button[1]",
                    "/html/body/div[2]/div[1]/div/div[1]/button[1]",
                ]
                queue_button = None
                for xpath in button_xpaths:
                    try:
                        logger.info(f"尝试定位按钮: {xpath}")
                        queue_button = WebDriverWait(driver, 3, 0.3).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        if queue_button:
                            logger.info(f"成功找到按钮: {xpath}")
                            break
                    except Exception as e:
                        logger.info(f"按钮未找到: {xpath}, 错误: {str(e)}")

                if queue_button:
                    queue_button.click()
                else:
                    raise Exception("所有可能的按钮路径都未找到可点击的按钮")
                # 更新当前页面标题
                current_title = driver.title
                logger.info(f"更新后的页面标题: {current_title}")
            except Exception as e:
                logger.info(f"模态框不存在或页面已变化: {str(e)}")
                logger.info("刷新页面并重试...")
                driver.refresh()
                time.sleep(2)  # 等待页面刷新完成
                # 更新当前页面标题
                current_title = driver.title
                logger.info(f"刷新后的页面标题: {current_title}")
                continue  # 继续循环，而不是break
        logger.info("点击购买按钮")
        try:
            buy_button = WebDriverWait(driver, 3, 0.5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "/html/body/section/div/div/div[2]/div/div[4]/div[2]/button")
                )
            )
            buy_button.click()
        except Exception as e:
            logger.error("购买按钮超时未加载出来")
        logger.info("点击登入按钮")
        time.sleep(5)
        login_button = WebDriverWait(driver, 3, 0.1).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/section[1]/div/div/div/div[3]/button"))
        )
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
        return

    def _select_ticket(self, driver):
        time.sleep(1)
        # 添加向下滚动功能
        logger.info("执行向下滚动")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)  # 等待滚动完成
        second_round_button = driver.find_element(By.XPATH, "//*[@id='ticketPrice8']")
        second_round_button.click()
        time.sleep(0.5)
        dropdown_element = driver.find_element(By.NAME, "ticketType0")
        select = Select(dropdown_element)
        select.select_by_index(1)  # 选择第三个选项（索引从0开始）
        logger.info("点击快速购票按钮")
        time.sleep(0.5)
        quick_button = WebDriverWait(driver, 3, 0.1).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/section[1]/div[2]/div/div[2]/div[2]/div[2]/button[2]")
            )
        )
        quick_button.click()
        return

    def _visa_payment(self, driver):
        try:
            time.sleep(2)
            ticket_collection_input1 = WebDriverWait(driver, 5, 0.1).until(
                EC.visibility_of_element_located((By.XPATH, "//*[@id='claimPassword']"))
            )
            ticket_collection_input1.send_keys("123456")
            ticket_collection_input2 = WebDriverWait(driver, 5, 0.1).until(
                EC.visibility_of_element_located((By.XPATH, "//*[@id='ReTypePwd']"))
            )
            ticket_collection_input2.send_keys("123456")
        except Exception as e:
            logger.info("取票密码输入框不存在，跳过输入")
        logger.info("点击visa付款方式")
        try:
            visa_button = WebDriverWait(driver, 8, 0.1).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-payment-code='VISA']"))
            )
            visa_button.click()
            logger.info("付款信息填入")
            # /html/body/section[1]/div[3]/div[1]/form/div[2]/div[25]/input
            visa_name = WebDriverWait(driver, 8, 0.1).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='holder']"))
            )
            visa_name.send_keys("heart")
            visa_card_number = WebDriverWait(driver, 3, 0.1).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='card']"))
            )
            visa_card_number.send_keys("4242424242424242")
            visa_expiry_date = WebDriverWait(driver, 3, 0.1).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='expiry']"))
            )
            visa_expiry_date.send_keys("11")
            time.sleep(0.1)
            visa_expiry_date.send_keys("29")
            visa_cvc = WebDriverWait(driver, 3, 0.1).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='code']"))
            )
            visa_cvc.send_keys("333")
            logger.info("点击去付款按钮")
            purchase_button = WebDriverWait(driver, 3, 0.1).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='proceedDisplay']/form/div[2]/div[30]/button"))
            )
            purchase_button.click()
        except Exception as e:
            logger.info(f"付款信息填入失败 error:{e}")
            time.sleep(1000)
        logger.info("复选框选择")
        time.sleep(2)
        try:
            first_multiple_check_box = driver.find_element(By.XPATH, "/html/body/section[1]/div[2]/div[1]/div[3]/label")
            first_multiple_check_box.click()
            second_multiple_check_box = driver.find_element(
                By.XPATH, "/html/body/section[1]/div[2]/div[1]/div[4]/div[1]/label"
            )
            second_multiple_check_box.click()
            third_multiple_check_box = driver.find_element(
                By.XPATH, "/html/body/section[1]/div[2]/div[1]/div[4]/div[2]/label"
            )
            third_multiple_check_box.click()
            logger.info("确认付款按钮点击")
        except Exception as e:
            logger.info(f"复选框选择失败 error:{e}")
            time.sleep(1000)
        confirm_button = WebDriverWait(driver, 3, 0.1).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='mainContainer']/div[1]/div[7]/button[2]"))
        )
        confirm_button.click()
        return


def process_ticket(browser_id):
    """
    处理单个浏览器的购票流程
    :param browser_id: 浏览器实例的唯一标识符
    """
    try:
        logger.info(f"开始处理浏览器 {browser_id}")
        cityline_ticket = CityLineTicket(browser_id=browser_id)
        logger.info(f"成功创建CityLineTicket实例，开始执行购票流程")
        cityline_ticket.main_process(browser_id=browser_id)
    except Exception as e:
        logger.error(f"处理浏览器 {browser_id} 时出错: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        logger.info("开始加载配置文件")
        with open("config/config.json", "r") as f:
            configs = json.load(f)
            logger.info(f"成功加载配置文件，内容: {configs}")

        # 创建线程池
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 启动多个浏览器实例
            browser_ids = [item["browser_id"] for item in configs]
            logger.info(f"准备启动的浏览器ID列表: {browser_ids}")

            futures = [executor.submit(process_ticket, browser_id) for browser_id in browser_ids]
            logger.info("所有任务已提交到线程池")

            # 等待所有任务完成
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"任务执行出错: {str(e)}")
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
