from sys import argv
from urllib.request import Request
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from seleniumwire.utils import decode
from urllib.parse import urlparse
import json
from collections import defaultdict
import platform
from dateutil import parser 
from time import sleep
from icalendar import Calendar, Event
from icalendar.cal import Alarm
from datetime import datetime, timezone, timedelta

def get_courses():
    #Username and Password of the student.
    username = argv[1]
    password = argv[2]

    #This sets up the chrome session, comment out the line containing "headless" to see the chrome session.
    chrome_options = Options()
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "eager"
    chrome_options.add_argument("--headless")
    if platform.machine() == 'arm64':
        driver = webdriver.Chrome(desired_capabilities=caps, executable_path='../chromedriver', options=chrome_options)
    else: 
        driver = webdriver.Chrome(desired_capabilities=caps, executable_path='../chromedriver_intel', options=chrome_options)
    
    #Navigate the website using xPath 
    url = 'https://avenue.mcmaster.ca/'

    wait = WebDriverWait(driver, 10)
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login_button"]'))).click()
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="i0116"]'))).send_keys(username + "@mcmaster.ca")
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="idSIButton9"]')))
    button = driver.find_element(By.XPATH, '//*[@id="idSIButton9"]')
    button.click()
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="i0118"]'))).send_keys(password)
    sleep(2)
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="idSIButton9"]'))).click()
    sleep(2)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="idSIButton9"]'))).click()
    print("logged in! waiting for course data to load.")
    wait.until(EC.element_to_be_clickable((By.XPATH, '//html/body/div[2]/div[2]/div[2]/div/div[2]/div/div[2]/div[1]/div/div[1]/a'))).click()
    
    #Telemetry is always the lest request on the work to do page. We can stop looking for requests.
    driver.wait_for_request('telemetryservice.brightspace.com/api/events/', timeout=100)
    driver.close()
    return driver.requests

#There are two kinds of work we are processing. Quizes and Assignments. 
# The following function definitions are present to process each type of work. 

"""
This method creates an entry for each quiz we encounter while scraping. 
Quizes have a special format in the way they are represented in the request.
We parse this data and return a task array containing the information about a given quiz. 
"""
def process_quiz(request, courses):
    course_code = urlparse(request["links"][0]["href"]).path.split('/')[1]
    task_name = courses[course_code] + " " + request["properties"]["name"]
    start = request["entities"][0]["properties"]["date"]
    end = request["entities"][1]["properties"]["date"]
    print(f"found quiz: {task_name}")
    return ['quiz', task_name, start, end]

"""
This method creates an entry for each assignment we encounter while scraping. 
In a similar fashion as the above function for quizes, assignments also have a special format in their requests.
We use this to process the assignments.
Once again returns an array containing information about a given assignment. 
"""
def process_assignment(request: Request, courses: dict):
    course_code = urlparse(request["links"][0]["href"]).path.split('/')[1]
    task_name = courses[course_code] + " " + request["properties"]["name"]
    due = request["entities"][0]["properties"]["date"]
    notes = 'no notes.'
    try:
        notes = request["properties"]["instructionsText"]
    except:
        pass
    print(f"found assignment: {task_name}")
    return ['assignment', task_name, due, notes]

"""
The website provides due dates and deadlines in UTC. 
This helper method converts them into local time.
Returns a datetime instance containing the correct local time. 
"""
def set_time(time: datetime):
    time = parser.parse(time)
    local_time = time.replace(tzinfo=timezone.utc).astimezone(tz=None)
    return local_time

"""
This method creates a list of events from all the tasks that are collected.
Returns a list of Events for each task. 
"""
def make_event(work: defaultdict):
    events = []
    for _, tasks in work.items():
        for task in tasks:
            if task[0] == 'quiz':
                start_date = set_time(task[2])
                end_date = set_time(task[3])
                if (end_date - start_date).days > 1:
                    start_date = end_date + timedelta(hours=-1)
                name = task[1]
                event = Event()
                event.add('summary', name)
                event.add('dtstart', start_date)
                event.add('dtend', end_date)
                alarm = Alarm()
                alarm.add('action', 'DISPLAY')
                alert_time = timedelta(minutes=-10)
                alarm.add('trigger', alert_time)
                event.add_component(alarm)
                print(f"processed: {name}")
                events.append(event)
            else:
                name = task[1]
                due_date = set_time(task[2])
                start_date = due_date + timedelta(hours=-1)
                notes = task[3]
                event = Event()
                event.add('summary', name)
                event.add('dtstart', start_date)
                event.add('dtend', due_date)
                event.add('description', notes)
                alarm = Alarm()
                alarm.add('action', 'DISPLAY')
                alert_time = timedelta(days=-1)
                alarm.add('trigger', alert_time)
                event.add_component(alarm)
                print(f"processed: {name}")
                events.append(event)

    return events

if __name__ == "__main__":
    courses = {}
    work = defaultdict(list)

    requests = get_courses()

    for request in requests:
        try:
            rq = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
            r = json.loads(rq)
            if 'course-offering' in r["class"]:
                course_code = r["entities"][3]["properties"]["path"].split('/')[-1]
                courses[course_code] = r["properties"]["name"].split(':')[0]
            
            if 'start-date' in r["entities"][0]["class"][1]:
                work[course_code].append(process_quiz(r, courses))
            
            if 'due-date' in r["entities"][0]["class"][1]:
                work[course_code].append(process_assignment(r, courses))
        except:
            pass
    
    events = make_event(work)
    cal = Calendar()
    for event in events:
        cal.add_component(event)
    
    # This exports a txt containing all the tasks that need to be done. 
    # My use case for this was to add it to my to-do list. Use it however you want. 
    f = open('tasks.txt', 'w')
    for _, tasks in work.items():
        for task in tasks:
            f.write(task[1] + "\n")
    f.close()

    # We create the ics file that can be used to add the tasks to any calendar app.
    f = open('tasks.ics', 'wb')
    f.write(cal.to_ical())
    f.close()