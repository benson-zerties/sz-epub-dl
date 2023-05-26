#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
import argparse
from selenium import webdriver
from sz_html_parser import SzHtmlParser

def epub_download(target_dir: str, credentials: dict, parser):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_experimental_option('prefs', {
            "download.default_directory": target_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
    })
    driver = webdriver.Chrome(options=options)
    
    # Login
    driver.get("https://id.sueddeutsche.de/login")
    username_form = driver.find_element('id', 'login_login-form')
    pw_form = driver.find_element('id', 'password_login-form')
    username_form.send_keys(credentials['user'])
    pw_form.send_keys(credentials['password'])
    driver.find_element('id', 'authentication-button').click()
    time.sleep(2)
    try:
        # check if login was successful by looks for the customer-number
        customer_number_el = WebDriverWait(driver, 10).until(EC.presence_of_element_located( (By.CLASS_NAME, 'customer-number') ) )
        customer_number = customer_number_el.get_attribute('innerHTML')
        print(customer_number)
    except:
        driver.quit()
        print('Login failed')
        return

    # wait some time for the login to be successfull: how to improve this?
    driver.get("https://reader.sueddeutsche.de/") # (1)
    parser.feedParser(driver.page_source)
    epub_list = parser.getResult()
    # Download newspaper
    for entry in epub_list:
        print('Downloading %s' % (entry))
        # Move to download website
        driver.get("https://reader.sueddeutsche.de/") # (1)
        # Referer must match?? We always need to come via (1)
        driver.get(entry) # (2)
        time.sleep(2)

    driver.quit()


if __name__ == '__main__':
    import hashlib
    import subprocess
    import argparse

    parser = argparse.ArgumentParser(description='Download epubs from SZ.')
    parser.add_argument('--user', default=None, help='Login for sueddeutsche.de')
    parser.add_argument('--password', default=None, help='Login for sueddeutsche.de')
    parser.add_argument('--epub_dir')
    args = parser.parse_args()    
    target_dir = args.epub_dir
    user = args.user

    print('Storing epubs to %s' % (target_dir))
    sz_parser = SzHtmlParser(
	u'https://reader.sueddeutsche.de',
	r'/restricted/downloadDesktop/SZ',
        r'format=EPUB',
    )

    if args.password == None:
        # obtain password from pass application
        print('Obtaining password from pass')
        site = "id.sueddeutsche.de"
        entry = hashlib.sha1(site.encode('utf8')).hexdigest()
        pass_result = subprocess.run(["pass", "show", "%s/%s" % (entry,user)], capture_output=True)

        if pass_result.returncode:
            print("Something went wrong")
            print(pass_result)
            sys.exit(1)
        else:
            # remove trailing newline
            pw = pass_result.stdout[:-1].decode('utf8')
    else:
        pw = args.password

    credentials = {'user': user, 'password': pw}
    epub_download(target_dir, credentials, sz_parser)
