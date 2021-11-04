from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import keyword_extraction_modules as ke
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from socket import gaierror
from webdriver_manager.chrome import ChromeDriverManager
import json
import urllib.parse
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests


def get_job_description(keyrolword,num_jobs,verbose):
    options = Options()
    options.add_argument("--window-size-1920,1200")
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver  =  webdriver.Chrome (options=options,executable_path=ChromeDriverManager().install())
    url = "https://www.glassdoor.com/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword="+keyword+"&sc.keyword="+keyword+"&locT=&locId=&jobType="
    driver.get(url)
    job_urls = []
    c=0
    job_buttons = driver.find_elements_by_xpath('.//a[@class = "jobLink job-search-key-1rd3saf eigr9kq1"]')  #jl for Job Listing. These are the buttons we're going to click.
    time.sleep(2)
    print(len(job_buttons))
    for text in job_buttons:
        if text.get_attribute('href'):                       ### get all the job postings URL's
            job_urls.append(text.get_attribute('href'))
            c=c+1
            if(c>=num_jobs):
                break
    
    final_dict = {}
    
    # ========== Iterate through each url and get the job description =================================

    for i in job_urls:
            time.sleep(5)
            jobs = []
            driver.get(i)
            button = driver.find_element_by_xpath('//*[@id="JobDescriptionContainer"]/div[2]')
            button.click()
            job_description = driver.find_element_by_xpath('//*[@id="JobDescriptionContainer"]/div[1]').text
            jobs.append(job_description)
            final_dict[i] = job_description

    return final_dict        

