from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time

def document_initialised(driver):
    return driver.execute_script("return initialised")

DRIVER_PATH = '/Users/mehdihamou/Documents/ChromeDriver/chromedriver'

driver = webdriver.Chrome(executable_path=DRIVER_PATH)
driver.get("https://www.leboncoin.fr/")
