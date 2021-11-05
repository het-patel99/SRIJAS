import json
import mysql.connector
from mysql.connector import Error
import scrapper_glassdoor as sg
import scrapper_indeed as si
import scrapper_linkedIn as sl
import email_alert as ea
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

#Setup Web driver
def get_driver():
    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(options=options, executable_path=ChromeDriverManager().install())
    return driver

#######################################################DATABASE OPERATIONS########################################################################################

# Creating connection for database
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

# Returns list of sills present in Skill Master Table in Database
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

# Returns user location from User Master Table from Database
def get_location(connection):
    sql_select_query = "select user_location from user_master um join user_resume ur where um.user_id=ur.user_id"
    cursor=connection.cursor()
    cursor.execute(sql_select_query)
    records2=cursor.fetchall()
    return records2[-1][0]

# Returns user threshold from User Master Table from Database 
def get_threshold(connection):
    sql_select_query = "select user_threshold from user_master um join user_resume ur where um.user_id=ur.user_id"
    cursor=connection.cursor()
    cursor.execute(sql_select_query)
    records2=cursor.fetchall()
    return records2[-1][0]

# Returns job_title from Job Master Table from Database
def get_role(connection):
    sql_select_query = "select job_title from job_master jm join user_master um where jm.job_id=um.user_preferred_job_id"
    cursor=connection.cursor()
    cursor.execute(sql_select_query)
    records2=cursor.fetchall()
    return records2[-1][0]

# Returns list of skills associated with each resume id from Resume Skills Table from Database
def get_resume_skills(connection):
    sql_select_Query2="select resume_id,skill_id from resume_skills where is_active=1"
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

# Returns list of emails associated with each resume id from User Master Table from Database
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



if __name__ =='__main__':
    # driver = get_driver()
    properties = open('parameters.json')
    data = json.load(properties)
    connection = db_connect(properties)

    #fetch details from database
    all_skills = get_all_skills(connection)
    #print(all_skills)
    resume_skills = get_resume_skills(connection)
    #print(resume_skills)
    email_id_list = get_emailing_list(connection)
    # print(email_list)
    location = str(get_location(connection))
    role = str(get_role(connection))
    print(role)
    no_of_jobs_to_retrieve = 5
    match_threshold = int(get_threshold(connection))

    #scrap role name and job links along with job description from LinkedIn, glassdoor and Indeed
    role_name_linkedIn, final_result_linkedIn = sl.get_job_description(resume_skills,all_skills, match_threshold, role, location, no_of_jobs_to_retrieve, data)
    role_name_glassdoor, final_result_glassdoor = sg.get_job_description(resume_skills,all_skills, match_threshold, role, location, no_of_jobs_to_retrieve, data)
    role_name_indeed, final_result_indeed = si.get_job_description(resume_skills,all_skills, match_threshold, role, location, no_of_jobs_to_retrieve, data)
    # print(final_result_glassdoor)
    # final_results = final_result_linkedIn + final_result_glassdoor + final_result_indeed
    # role_name = role_name_linkedIn + role_name_glassdoor + role_name_indeed
    list_of_link = final_result_linkedIn[1] + final_result_glassdoor[1] + final_result_indeed[1]
    # print(list_of_link)

    # final_results = {**final_result_linkedIn, **final_result_glassdoor, **final_result_indeed}
    # print(final_results)

    newDict = {}
    keySet = set(list(final_result_linkedIn.keys()) + list(final_result_glassdoor.keys()) + list(final_result_indeed.keys()))
    for k in keySet:
        if k not in newDict:
            newDict[k] = []
        if k in final_result_indeed:
            newDict[k] = newDict[k] + final_result_indeed[k]
        if k in final_result_glassdoor:
            newDict[k] = newDict[k] + final_result_glassdoor[k]
        if k in final_result_linkedIn:
            newDict[k] = newDict[k] + final_result_linkedIn[k]
    # print("New dict")
    # print(newDict)

    role_name = role_name_linkedIn + role_name_glassdoor + role_name_indeed    
    # print(final_result_linkedIn)

    #Send Email of job links
    print(ea.sendmail(newDict,email_id_list,role_name))
    #Send Email of job links
    # ea.sendmail(final_result_linkedIn,email_id_list,role_name_linkedIn)


