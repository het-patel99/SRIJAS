from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import mysql.connector
from mysql.connector import Error
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import keyword_extraction_modules as ke
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from socket import gaierror
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
import json
#######################################################DATABASE OPERATIONS########################################################################################


############################################creating connection for database#################################
def db_connect(properties):
    properties = open('parameters.json')
    data = json.load(properties)
    server_name = data['server_name']
    user_name = data['user_name']
    password = data['password']
    db_name = data['db_name']
    connection = mysql.connector.connect(host=server_name,
                                              database=db_name,
                                              user=user_name,
                                              password=password)
    return connection

def get_all_skills(connection):
    sql_select_Query = "select DISTINCT skill_id,skill_title from skill_master"
    cursor=connection.cursor()
    cursor.execute(sql_select_Query)
    records=cursor.fetchall()
    all_skills={}
    for row in records:
        all_skills[row[0]]=row[1]
    print("All skills",all_skills)
    return all_skills


def get_resume_skills(connection):
    sql_select_Query2="select  resume_id,skill_id from resume_skills where is_active=1"
    cursor=connection.cursor()
    cursor.execute(sql_select_Query2)
    records2=cursor.fetchall()
    resume_skills={}
    for row in records2:
        if(row[0]) in resume_skills:
            resume_skills[row[0]].append(row[1])
        else:
            resume_skills[row[0]]=[row[1]]
    return resume_skills
        

def get_emailing_list(connection):
    email_id_list={}
    sql_select_Query3="SELECT resume_id,user_email from user_master um join user_resume ur on um.user_id=ur.user_id"
    cursor=connection.cursor()
    cursor.execute(sql_select_Query3)
    records_email=cursor.fetchall()
    for row in records_email:
        email_id_list[row[0]]=row[1]
    print("Resume id and email id",email_id_list)
    return email_id_list

def get_job_description(keyword,no_of_jobs_to_retrieve,data):
    username="srijas.alerts@gmail.com"
    pwd=data['linked_in_pwd']
    no_of_jobs_to_retrieve=5
    count=0
    searchquery="Software Engineer"
    options = Options()
    options.add_argument("--window-size=1920,1200")
    options.headless= True
    options.add_argument('--nosandbox')
    options.add_argument('--disable-dev-shm-usage')    
    browser = webdriver.Chrome(options=options, executable_path=ChromeDriverManager().install())
    match_threshold=1
    
    ################################Sign IN#################################################
    browser.get('https://www.linkedin.com/checkpoint/rm/sign-in-another-account?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')
    username_ip=browser.find_element_by_id('username')
    username_ip.send_keys(username)
    pwd_ip=browser.find_element_by_id('password')
    pwd_ip.send_keys(pwd)
    sign_in_button=browser.find_element_by_xpath("//button[@data-litms-control-urn='login-submit']")
    sign_in_button.click();
    
    
    ######################################################## traverse to job lisitng page #########################
    browser.get('https://www.linkedin.com/jobs/jobs-in-raleigh-nc?trk=homepage-basic_intent-module-jobs&position=1&pageNum=0')
    weblement = WebDriverWait(browser, 10000).until(
        EC.presence_of_element_located((By.XPATH, "//input[contains(@id,'jobs-search-box-keyword-id')]"))
    )
    job_description=browser.find_element_by_xpath("//input[contains(@id,'jobs-search-box-keyword-id')]").send_keys(searchquery)
    #inserting job filter value
    search_button=browser.find_element_by_class_name("jobs-search-box__submit-button")
    search_button.click()
    time.sleep(3)#give time to load search query results
    
    ############################################scroll to the bottom of the page#############################################
    recentList = browser.find_elements_by_xpath("//section[@aria-label='pagination']")
    for list in recentList :
            browser.execute_script("arguments[0].scrollIntoView();", list )
    time.sleep(5)
    ####################################retrieve job links####################################################
    job_cards=browser.find_elements_by_xpath("//a[@class='disabled ember-view job-card-container__link job-card-list__title']")
    href_arr=[]
    for i in job_cards:
        href_arr.append(i.get_attribute("href"))
    #print(len(href_arr))
    
     ################looping through every job listing to scrape relevant data##################################
    
    final={}
    listele=[]
    for url in href_arr:
         browser.get(url)
         time.sleep(5)
         show_more_button=browser.find_element_by_xpath("//button[contains(@aria-label,'Click to see more description')]")
         show_more_button.click()
         list_ele=browser.find_elements_by_xpath("//article//li")
        ############for each job lisitng loop through all list items and add the text######################
         data=[]
         datastr=""
         for li in list_ele:
             data.append(li.text)
         for val in data:
             datastr+=val + " "
         time.sleep(5)
         count+=1
         if(count==no_of_jobs_to_retrieve):
             break
         final[url]=datastr
    #     print(datastr,url,final)
    
    
    #print(resume_skills,final,connection,all_skills,match_threshold)
    
    final_result=ke.get_user_id_to_list_of_job_ids(resume_skills,final,connection,all_skills,match_threshold)
    return final_result







if __name__ =='__main__':
    properties = open('parameters.json')
    data = json.load(properties)
    connection = db_connect(properties)
    all_skills = get_all_skills(connection)
    #print(all_skills)
    resume_skills = get_resume_skills(connection)
    #print(resume_skills)
    email_id_list = get_emailing_list(connection)
   # print(email_list)
    final_result = get_job_description("Software Engineer",5,data)
    print(final_result)


##########################################################EMAIL SERVICE######################################################################


 ##generating receiever email ids
port = 587
smtp_server = "smtp.gmail.com"
login = "srijas.alerts@gmail.com"
password = ""
sender = "srijas.alerts@gmail.com"
for key in final_result:
     if key in email_id_list:
        receiver = email_id_list[key]
        print(receiver)
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = 'Job Lisitngs'
        body = """Hi, \n PFA the attached list of jobs that match your resume \n"""
        temp_str = ""
        list_of_curr_links = final_result[key]
        counter = 1
        for link in list_of_curr_links:
            pre = """<a href='"""
            embedded_link = link
            post = """'>View Position</a>"""
            temp_str += (str(counter) + ".  " + pre + embedded_link + post+ '\n')
            counter += 1
        body += temp_str
        msg.attach(MIMEText(body, 'html'))
        text = msg.as_string()

        try:
            server = smtplib.SMTP(smtp_server, port)
            server.connect(smtp_server,port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(login, password)
            server.sendmail(sender, receiver, text)
            server.quit()                                                                                # tell the script to report if your message was sent or which errors need to be fixed
            print('Sent')
        except (gaierror, ConnectionRefusedError):
            print('Failed to connect to the server. Bad connection settings?')
        except smtplib.SMTPServerDisconnected as e:
            print('Failed to connect to the server. Wrong user/password?')
            print(str(e))
        except smtplib.SMTPException as e:
            print('SMTP error occurred: ' + str(e))