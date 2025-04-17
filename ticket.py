import json
import os
import random
import threading
import time
from concurrent.futures import ProcessPoolExecutor

import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from twocaptcha import TwoCaptcha

from config import env_config as conf
from my_logging import logger


class CityLineTicket:

    def __init__(self, browser_id):
        self.driver = None
        self.solved_code = None
        self.driver_url = None
        self.browser_id = browser_id
        self.config = self._load_config()
        self.keys = self.config.get("keys")
        self.ticket_price = self.config.get("ticket_price", [1])
        self.ticket_type = self.config.get("ticket_type", 1)
        self.date = self.config.get("date", [0])
        self.ticket_password = self.config.get("ticket_password", "123456")
        self.payment_method = self.config.get("payment_method")
        self.visa_name = None
        self.visa_credit_card_number = None
        self.visa_mm = None
        self.visa_yy = None
        self.visa_security_code = None
        self.twocaptcha_apikey = conf.TWOCAPTCHA_KEY
        self.css_locator_for_input_send_token = 'input[name="cf-turnstile-response"]'
        logger.info(
            f"初始化CityLineTicket实例 - browser_id: {self.browser_id}, keys: {self.keys}, ticket_price: {self.ticket_price}, ticket_type: {self.ticket_type}"
        )

    def _load_config(self):
        """
        加载配置文件
        :return: 返回对应browser_id的配置
        """
        try:
            logger.info(f"开始加载配置文件,查找browser_id: {self.browser_id}")
            with open("config/config.json", "r") as f:
                configs = json.load(f)
                logger.info(f"配置文件内容: {configs}")
                for config in configs:
                    if config["browser_id"] == self.browser_id:
                        logger.info(f"找到匹配的配置: {config}")
                        return config
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
        self.driver = uc.Chrome(headless=False, use_subprocess=False)
        logger.info(f"打开浏览器 访问网站")
        self.driver.get("https://www.cityline.com")
        logger.info(f"{browser_id} 清空初始Cookies")
        self.driver.delete_all_cookies()
        # 手动登录
        login_button = WebDriverWait(self.driver, 3, 0.1).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-login"))
        )
        login_button.click()
        time.sleep(60)
        try:
            login_button = WebDriverWait(self.driver, 3, 0.1).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btn-login"))
            )
            login_button.click()
        except Exception as e:
            logger.info(f"登陆按钮不存在 error:{e}")
            self.driver.refresh()
        logger.info(f"获取{browser_id}_Cookies")
        cookies = self.driver.get_cookies()

        # 确保目录存在
        os.makedirs("user_cookies", exist_ok=True)
        logger.info(f"保存Cookies 到文件: user_cookies/cityline_cookies_{browser_id}.json")
        # 使用 browser_id 来区分不同的 cookies 文件
        cookie_file = f"user_cookies/cityline_cookies_{browser_id}.json"
        with open(cookie_file, "w") as f:
            json.dump(cookies, f)
        self.driver.quit()

    def main_process(self):
        """
        加载Cookies
        :param browser_id: 浏览器实例的唯一标识符
        :return: cookies 列表
        """
        # 加载cookies 刷新页面
        self.driver = self._load_cookies_refresh(self.browser_id)
        # 等待页面加载完成
        time.sleep(0.5)
        # 搜索关键词
        self._search_keyword()
        # 等待页面加载完成
        time.sleep(0.5)
        logger.info("点击前往购票按钮")
        self._click_go_button()
        time.sleep(0.5)
        # 点击购票 登入 检查模态框
        self._check_model()
        time.sleep(0.5)
        self._select_ticket()
        time.sleep(0.5)
        self._insert_ticket_password()
        time.sleep(0.5)
        if self.payment_method == "visa":
            self._visa_payment()
        elif self.payment_method == "alipay":
            self._alipay_payment()
        time.sleep(0.5)
        self._checkbox_select()
        time.sleep(30000)
        self.driver.quit()

    def _load_cookies_refresh(self, browser_id):
        if not self._check_user_cookies(browser_id):
            self._save_cookies(browser_id)
        self.driver = uc.Chrome(headless=False, use_subprocess=False)
        self.driver.get("https://www.cityline.com")
        logger.info("删除所有cookies")
        self.driver.delete_all_cookies()
        logger.info("加载Cookies")
        with open(f"user_cookies/cityline_cookies_{browser_id}.json", "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
        logger.info("刷新页面")
        self.driver.refresh()
        return self.driver

    def _switch_to_new_window(self):
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[-1])
        return

    def _search_keyword(self):
        logger.info("搜索关键字")
        first_input_element = self.driver.find_element(
            By.XPATH, "//*[@id='app']/div/div[2]/div[4]/div[2]/div/div/span/input"
        )
        first_input_element.send_keys(self.keys)
        first_input_element.send_keys(Keys.RETURN)
        time.sleep(0.5)
        logger.info("点击搜索结果")
        search_first_div = self.driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div[4]/div[5]")
        link = search_first_div.find_element(By.TAG_NAME, "a")
        link.click()
        logger.info("获取所有标签页的句柄")
        logger.info("切换到最新打开的标签页")
        self._switch_to_new_window()
        return

    def _click_go_button(self):
        while True:
            try:
                # 直接查找父级div中的按钮
                parent_div = self.driver.find_element(By.CLASS_NAME, "buyTicketBox")
                go_button = parent_div.find_element(By.XPATH, ".//*[@id='buyTicketBtn']")
                go_button.click()
                logger.info("成功点击前往购票按钮")
                break

            except Exception as e:
                logger.info(f"{self.browser_id} 未找到前往购票按钮 刷新重试")
                self.driver.refresh()
                time.sleep(0.1)

    def _retry_button(self, current_title):
        # 当标题包含"Cityline"时继续循环
        while current_title == "Cityline":
            try:
                # 添加3-5秒的随机延迟
                random_delay = random.uniform(3, 4)
                logger.info(f"{self.browser_id} 等待随机延迟: {random_delay:.2f}秒")
                time.sleep(random_delay)
                # 尝试多个可能的XPath路径
                button_xpaths = [
                    "/html/body/div[3]/div[1]/div/div[1]/button[1]",
                    "/html/body/div[2]/div[1]/div/div[1]/button[1]",
                ]
                queue_button = None
                for xpath in button_xpaths:
                    try:
                        logger.info(f"{self.browser_id} 尝试定位按钮: {xpath}")
                        queue_button = WebDriverWait(self.driver, 3, 0.3).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        if queue_button:
                            logger.info(f"{self.browser_id} 成功找到按钮: {xpath}")
                            break
                    except Exception as e:
                        logger.info(f"{self.browser_id} 按钮未找到: {xpath}, 错误: {str(e)}")

                if queue_button:
                    queue_button.click()
                else:
                    raise Exception("所有可能的按钮路径都未找到可点击的按钮")
                # 更新当前页面标题
                current_title = self.driver.title
                logger.info(f"{self.browser_id} 更新后的页面标题: {current_title}")
            except Exception as e:
                logger.info(f"{self.browser_id} 模态框不存在或页面已变化: {str(e)}")
                logger.info("刷新页面并重试...")
                self.driver.refresh()
                time.sleep(2)  # 等待页面刷新完成
                # 更新当前页面标题
                current_title = self.driver.title
                logger.info(f"{self.browser_id} 刷新后的页面标题: {current_title}")
                continue  # 继续循环，而不是break
        return

    def _check_model(self):
        logger.info("切换到最新打开的标签页")
        self._switch_to_new_window()
        time.sleep(2)
        self.driver.save_screenshot(f"screenshot_{self.browser_id}.png")

        # 获取当前页面标题
        current_title = self.driver.title
        logger.info(f"当前页面标题: {current_title}")
        time.sleep(0.5)
        self._retry_button(current_title)
        logger.info("点击购买按钮")
        try:
            buy_button = WebDriverWait(self.driver, 3, 0.5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "/html/body/section/div/div/div[2]/div/div[4]/div[2]/button")
                )
            )
            buy_button.click()
        except Exception as e:
            logger.error(f"{self.browser_id} 购买按钮超时未加载出来")
        time.sleep(10)
        try:
            input_ele = WebDriverWait(self.driver, 10, 0.1).until(
                EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div[1]/section[1]/div/div/div/div[2]/form/div[8]/div[1]/div/input")
                )
            )
            input_value = input_ele.get_attribute("value")
            if not input_value:
                self.driver_url = self.driver.current_url
                logger.info("2captcha开始解决turnstile")
                solver = TwoCaptcha(self.twocaptcha_apikey)
                result = solver.turnstile(sitekey="0x4AAAAAAAWNjB2Bt2Whyc7f", url=self.driver_url)
                logger.info(f"2captcha解决成功!")
                self.solved_code = result["code"]
                logger.info(f"返回code {self.solved_code}")
                self.driver.execute_script(
                    """
                    document.evaluate("//input[@name='cf-turnstile-response']", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null)
                        .singleNodeValue.value = arguments[0];
                """,
                    self.solved_code,
                )
                logger.info(f"执行script 往input插入code")
                login_button = WebDriverWait(self.driver, 30, 0.1).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, "/html/body/div[1]/section[1]/div/div/div/div[3]/button")
                    )
                )
                logger.info(f"执行script 设置login_button 可见")
                self.driver.execute_script("arguments[0].removeAttribute('disabled')", login_button)
                logger.info(f"执行script 设置不透明度为1")
                self.driver.execute_script("arguments[0].style.opacity = '1'", login_button)
                time.sleep(3)
                logger.info("2captcha完成之后点击登入按钮")
                login_button.click()
        except Exception as e:
            logger.info(f"无captcha触发或解决失败: {e}")
        while True:
            try:
                time.sleep(3)
                login_button.click()
            except Exception as e:
                logger.info(f"点击login_button失败")
                break
        time.sleep(3)
        try:
            logger.info("点击登入按钮")
            login_button = WebDriverWait(self.driver, 10, 0.1).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/section[1]/div/div/div/div[3]/button"))
            )
            login_button.click()
        except Exception as e:
            logger.info(f"没找到登入按钮 继续执行")
        time.sleep(3)
        logger.info(f"{self.browser_id} 检测模态框是否存在")
        try:
            modal_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.modal-content")
            if len(modal_elements) > 0:
                modal = modal_elements[0]
                logger.info(f"{self.browser_id} 模态框存在,找到按钮点击")
                confirm_button = modal.find_element(
                    By.XPATH, "/html/body/div[1]/section[2]/div/div/div/div/div/button[1]"
                )
                confirm_button.click()
        except Exception as e:
            logger.info(f"{self.browser_id} 模态框不存在")
        return

    def _select_ticket(self):
        time.sleep(1)
        try:
            logger.info(f"{self.browser_id} 尝试选择票种: {self.ticket_type}")
            time.sleep(2)

            dropdown_element = self.driver.find_element(By.NAME, f"ticketType0")
            select = Select(dropdown_element)
            select.select_by_index(self.ticket_type)
            time.sleep(0.5)
            self._select_date()
            time.sleep(0.5)
            for ticket_price in self.ticket_price:
                try:
                    if ticket_price > 8:
                        logger.info(f"{self.browser_id} 票价编号{ticket_price}大于8，执行向下滚动")
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    else:
                        logger.info(f"{self.browser_id} 票价编号{ticket_price}小于等于8，执行向上滚动")
                        self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(0.5)  # 等待滚动完成
                    # 选择票价
                    logger.info(f"{self.browser_id} 尝试选择票价: ticketPrice{ticket_price}")
                    price_button = self.driver.find_element(
                        By.XPATH, f"//*[@id='ticketPrice{ticket_price}']"
                    )  # 这个地方是从0开始
                    price_button.click()
                    time.sleep(0.5)
                    # 点击确定按钮
                    logger.info(f"{self.browser_id} 点击快速购票按钮")
                    quick_button = WebDriverWait(self.driver, 3, 0.1).until(
                        EC.presence_of_element_located((By.ID, "expressPurchaseBtn"))
                    )
                    quick_button.click()
                    time.sleep(1)
                    error_elements = [
                        "/html/body/section[1]/div[2]/div/div[1]/div/div[3]/div[2]/div[3]/span",
                        "/html/body/section[1]/div[2]/div/div[1]/div/div[3]/div[2]/div[4]",
                        "/html/body/section[1]/div[2]/div/div[1]/div/div[3]/div[3]/span",
                        "/html/body/section[1]/div[2]/div/div[1]/div/div[3]/div[4]",
                    ]
                    error_found = False
                    for error_xpath in error_elements:
                        try:
                            error_element = self.driver.find_element(By.XPATH, error_xpath)
                            if error_element.is_displayed():
                                logger.info(f"{self.browser_id} 发现错误提示，尝试下一个票价")
                                error_found = True
                                break
                        except:
                            continue
                    if error_found:
                        logger.info(f"{self.browser_id} 发现错误提示，尝试下一个票价")
                        continue
                    else:
                        logger.info(f"{self.browser_id} 成功选择票价{ticket_price}")
                        return
                except Exception as e:
                    logger.info(f"{self.browser_id} 选择票价{ticket_price}失败: {str(e)}")
                    continue
            logger.error(f"{self.browser_id} 所有票价都尝试失败")
            raise Exception("没有可用的票价")
        except Exception as e:
            logger.error(f"{self.browser_id} 选择票种失败: {str(e)}")
            raise

    def _select_date(self):
        if self.date == [0]:
            return
        try:
            # 等待元素加载
            logger.info(f"{self.browser_id} 等待日期选择按钮加载")
            performance_buttons = WebDriverWait(self.driver, 10, 0.5).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "date-box"))
            )
            success = False
            error_messages = []

            for date in self.date:
                try:
                    if date >= len(performance_buttons):
                        error_messages.append(f"日期索引 {date} 超出范围")
                        continue

                    logger.info(f"{self.browser_id} 尝试选择第 {date + 1} 个日期")
                    selected_button = performance_buttons[date]

                    # 检查按钮是否可见
                    if not selected_button.is_displayed():
                        error_messages.append(f"第 {date + 1} 个日期按钮不可见")
                        continue

                    # 尝试滚动到按钮位置
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", selected_button)
                    time.sleep(0.5)

                    # 点击按钮
                    selected_button.click()
                    logger.info(f"{self.browser_id} 成功选择第 {date + 1} 个日期")
                    success = True
                    break

                except Exception as e:
                    error_msg = f"选择第 {date + 1} 个日期失败: {str(e)}"
                    error_messages.append(error_msg)
                    logger.warning(f"{self.browser_id} {error_msg}，尝试下一个")
                    continue

            if not success:
                raise Exception(f"{self.browser_id} 所有日期都选择失败:\n" + "\n".join(error_messages))

            time.sleep(1)

        except Exception as e:
            logger.error(f"{self.browser_id} 选择日期失败: {str(e)}")
            raise

    def _insert_ticket_password(self):
        try:
            time.sleep(2)
            ticket_collection_input1 = WebDriverWait(self.driver, 5, 0.1).until(
                EC.visibility_of_element_located((By.XPATH, "//*[@id='claimPassword']"))
            )
            ticket_collection_input1.send_keys(f"{self.ticket_password}")
            ticket_collection_input2 = WebDriverWait(self.driver, 5, 0.1).until(
                EC.visibility_of_element_located((By.XPATH, "//*[@id='ReTypePwd']"))
            )
            ticket_collection_input2.send_keys(f"{self.ticket_password}")
        except Exception as e:
            logger.info("取票密码输入框不存在，跳过输入")
        return

    def _purchase_button_click(self):
        try:
            logger.info("点击去付款(确认)按钮")
            purchase_button = WebDriverWait(self.driver, 3, 0.1).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='proceedDisplay']/form/div[2]/div[30]/button"))
            )
            purchase_button.click()
        except Exception as e:
            logger.error(f"确认按钮点击失败 error:{e}")
        return

    def _alipay_payment(self):
        logger.info("点击支付宝付款方式")
        try:
            alipay_button = WebDriverWait(self.driver, 8, 0.1).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-payment-code='ALIPAY']"))
            )
            alipay_button.click()
            self._purchase_button_click()
        except Exception as e:
            logger.error(f"点击支付宝付款失败 error: {e}")
        return

    def _visa_payment(self):
        logger.info("点击visa付款方式")
        self.visa_name = self.config.get("visa_name")
        self.visa_credit_card_number = self.config.get("visa_credit_card_number")
        self.visa_mm = self.config.get("visa_mm")
        self.visa_yy = self.config.get("visa_yy")
        self.visa_security_code = self.config.get("visa_security_code")
        try:
            visa_button = WebDriverWait(self.driver, 8, 0.1).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-payment-code='VISA']"))
            )
            visa_button.click()
            logger.info("付款信息填入")
            # /html/body/section[1]/div[3]/div[1]/form/div[2]/div[25]/input
            visa_name = WebDriverWait(self.driver, 8, 0.1).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='holder']"))
            )
            visa_name.send_keys(f"{self.visa_name}")
            visa_card_number = WebDriverWait(self.driver, 3, 0.1).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='card']"))
            )
            visa_card_number.send_keys(f"{self.visa_credit_card_number}")
            visa_expiry_date = WebDriverWait(self.driver, 3, 0.1).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='expiry']"))
            )
            visa_expiry_date.send_keys(f"{self.visa_mm}")
            time.sleep(0.1)
            visa_expiry_date.send_keys(f"{self.visa_yy}")
            visa_cvc = WebDriverWait(self.driver, 3, 0.1).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='code']"))
            )
            visa_cvc.send_keys(f"{self.visa_security_code}")
            self._purchase_button_click()
        except Exception as e:
            logger.info(f"付款信息填入失败 error:{e}")
            time.sleep(1000)
        return

    def _checkbox_select(self):
        logger.info("复选框选择")
        time.sleep(2)
        try:
            first_multiple_check_box = self.driver.find_element(
                By.XPATH, "/html/body/section[1]/div[2]/div[1]/div[3]/label"
            )
            first_multiple_check_box.click()
            second_multiple_check_box = self.driver.find_element(
                By.XPATH, "/html/body/section[1]/div[2]/div[1]/div[4]/div[1]/label"
            )
            second_multiple_check_box.click()
            third_multiple_check_box = self.driver.find_element(
                By.XPATH, "/html/body/section[1]/div[2]/div[1]/div[4]/div[2]/label"
            )
            third_multiple_check_box.click()
        except Exception as e:
            logger.info(f"复选框选择失败 error:{e}")
            time.sleep(1000)
        logger.info("确认付款按钮点击")
        confirm_button = WebDriverWait(self.driver, 3, 0.1).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='mainContainer']/div[1]/div[7]/button[2]"))
        )
        confirm_button.click()
        if self.payment_method == "alipay":
            time.sleep(5)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            self.driver.save_screenshot(f"screenshot/{self.browser_id}_alipay_{timestamp}.png")
            time.sleep(300)
        return


def process_ticket(browser_id):
    """
    处理单个浏览器的购票流程（含并发优化）
    :param browser_id: 浏览器实例的唯一标识符
    """
    try:
        # 添加随机延迟（2~4秒）缓解并发竞争
        initial_delay = random.uniform(2, 4)
        logger.info(f"浏览器 {browser_id} 初始化前等待 {initial_delay:.2f} 秒")
        time.sleep(initial_delay)

        cityline_ticket = CityLineTicket(browser_id=browser_id)  # 确保类支持该参数
        cityline_ticket.main_process()
    except Exception as e:
        logger.error(f"处理浏览器 {browser_id} 时出错: {str(e)}")
        raise


def main():
    try:
        logger.info("开始加载配置文件")
        with open("config/config.json", "r") as f:
            configs = json.load(f)
            logger.info(f"成功加载配置文件，内容: {configs}")

        browser_ids = [item["browser_id"] for item in configs]

        # 主进程预先初始化驱动（可选）
        _preinit_chromedriver()

        with ProcessPoolExecutor(max_workers=3) as executor:
            logger.info(f"准备启动的浏览器ID列表: {browser_ids}")

            # 提交任务时添加间隔（建议1~3秒）
            futures = []
            for idx, bid in enumerate(browser_ids):
                futures.append(executor.submit(process_ticket, bid))
                if idx != len(browser_ids) - 1:  # 最后一个任务不等待
                    time.sleep(1.5)  # 控制进程启动间隔

            # 等待所有任务完成
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"任务执行出错: {str(e)}")
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")


def _preinit_chromedriver():
    """主进程预先初始化驱动确保文件存在"""
    from undetected_chromedriver import Chrome

    logger.info("预初始化chromedriver...")
    try:
        temp_driver = Chrome()
        temp_driver.quit()
    except Exception as e:
        logger.warning(f"预初始化失败: {e}")


if __name__ == "__main__":
    # cityline_ticket = CityLineTicket(browser_id="ticket1")
    # cityline_ticket.main_process()
    main()

# if __name__ == "__main__":
#     cityline_ticket = CityLineTicket(browser_id="ticket1")
#     cityline_ticket.main_process()
