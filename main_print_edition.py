#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import argparse
import glob
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from sz_html_parser import SzHtmlParser
import sz_utils
from pathlib import Path
import polling2


def get_downloaded_files(driver):
    # https://gist.github.com/florentbr/033d4ed722465366632d7b95b301e11e
    if not driver.current_url.startswith("chrome://downloads"):
        driver.get("chrome://downloads/")

    # [... ] operator will convert the array of nodes into an array
    elements = driver.execute_script("""
            return [...document.querySelector('downloads-manager')
                        .shadowRoot.querySelectorAll('downloads-item')]
                        .map(el => el.shadowRoot.querySelector('a').innerText);
                        """);
    progress = driver.execute_script("""
            return [...document.querySelector('downloads-manager')
                        .shadowRoot.querySelectorAll('downloads-item')]
                        .map(el => el.shadowRoot.getElementById('progress')?.value);
                        """);
 
    #https://gist.github.com/ic0n/a38b354cac213e5aa50c55a0d8b87a0b?permalink_comment_id=3297438
    # download progress
    return (elements, progress)

def epub_download(target_dir: str, credentials: dict, parser):
    options = webdriver.ChromeOptions()
    print("Target dir: %s" % (target_dir))
    options.add_argument("--headless=new")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument('--window-size=800,1080')
    options.add_experimental_option('prefs', {
            "download.default_directory": target_dir, # absolute path is required
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
    })
    driver = webdriver.Chrome(options=options)
    if not sz_utils.login(driver, credentials):
        driver.quit()
        sys.exit(1)
    
    # wait some time for the login to be successfull: how to improve this?
    driver.get("https://epaper.sueddeutsche.de/Stadtausgabe") # (1)
    time.sleep(2) 
    sz_utils.accept_cookies(driver)
    login_el = WebDriverWait(driver, 10).until(EC.element_to_be_clickable( 
        (By.CSS_SELECTOR, "a[href='/login'") ) )
    login_el.click()
    pdf_list_el = WebDriverWait(driver, 10).until(EC.presence_of_element_located( 
        (By.CSS_SELECTOR, "ul[aria-labelledby='pdfDocumentsDropdown'") ) )
    parser.feedParser(pdf_list_el.get_attribute('innerHTML'))
    epub_list = parser.getResult()

    # debug output
    with open('debug_stadtausgabe.html', 'w+') as f:
        f.write(driver.page_source)

    issues = driver.find_elements(By.CLASS_NAME,'day')
    links = []
    for el in issues:
        text = el.get_attribute('innerHTML')
        soup = BeautifulSoup(text, features="lxml")
        lTmp = soup.find_all('a')
        links.append(lTmp[0].get('href'))

    downloadIds = [re.search(r'/webreader/(\d*)', ll).group(1) for ll in links]
    print('download ids')
    print(downloadIds)
    # start downloads
    for d in downloadIds:
        driver.get('https://epaper.sueddeutsche.de/download/' + d)
    driver.get('chrome://downloads/')
   
    # waiting for downloads to complete
    polling2.poll(
            lambda: all([el==100 or el==None for el in get_downloaded_files(driver)[1]]),
            step=1,
            timeout=5*60)
    #while True:
    #    time.sleep(0.5)
    #    (elements, progress) = get_downloaded_files(driver)
    #    print(progress)
    #    if all([el==100 or el==None for el in progress]):
    #        break
    driver.quit()


if __name__ == '__main__':
    import hashlib
    import subprocess
    import argparse

    parser = argparse.ArgumentParser(description='Download epubs from SZ.')
    parser.add_argument('--user', default=None, help='Login for sueddeutsche.de')
    parser.add_argument('--password', default=None, help='Login for sueddeutsche.de')
    parser.add_argument('--pdf_dir')
    args = parser.parse_args()    
    target_dir = str(Path(args.pdf_dir).resolve()) # convert to absolute path
    # clear target directory
    files = glob.glob(str(Path(target_dir, '*')))
    for f in files:
        os.remove(f)

    user = args.user

    #https://epaper.sueddeutsche.de/download/844625
    print('Storing epubs to %s' % (target_dir))
    sz_parser = SzHtmlParser(
	u'https://epaper.sueddeutsche.de',
	r'/Stadtausgabe',
        r'\d\d\d\d-\d\d-\d\d',
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
