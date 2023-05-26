#!/usr/bin/python3
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def accept_cookies(driver: webdriver):
    # switching to cookie banner iframe based on index
    iframes = driver.find_elements(By.TAG_NAME,'iframe')
    print("Number of iframes: %d" % (len(iframes)))
    # switch to selected iframe
    driver.switch_to.frame(iframes[-1])
    try:
        acceptCookies = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable( (By.CSS_SELECTOR, "button[title='Akzeptieren']") ))
        acceptCookies.click()
    except Exception as e:
        print("Cookie banner not found")
    # switch back to default content
    driver.switch_to.default_content()

def login(driver: webdriver, credentials: dict):
    # Login
    driver.get("https://id.sueddeutsche.de/login")
    username_form = driver.find_element('id', 'login_login-form')
    pw_form = driver.find_element('id', 'password_login-form')
    username_form.send_keys(credentials['user'])
    pw_form.send_keys(credentials['password'])
    driver.find_element('id', 'authentication-button').click()
    try:
        # check if login was successful by looks for the customer-number
        customer_number_el = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located( (By.CLASS_NAME, 'customer-number') ) )
        customer_number = customer_number_el.get_attribute('innerHTML')
        print(customer_number)
        return True
    except Exception as e:
        print(e)
        print('Login failed')
        return False
