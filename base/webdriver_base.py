# import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By

def setup_driver():
    # driver = uc.Chrome('zoho1')
    driver = webdriver.Chrome()
    return driver

class WebDriverBase:
    def __init__(self):
        self.driver = setup_driver()
        self.driver.implicitly_wait(10)  # Set a default implicit wait

    def quit(self):
        self.driver.quit()

    def wait_for_element(self, by, value, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"Element not found: {value}")
            return None

    def click_element(self, by, value):
        try:
            element = self.wait_for_element(by, value)
            if element:
                element.click()
                return True
        except WebDriverException:
            print(f"Standard click failed for element: {value}. Trying JavaScript click.")
            if element:
                self.driver.execute_script("arguments[0].click();", element) 
                return True
        return False