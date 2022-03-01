from sys import argv
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from seleniumwire.utils import decode
import platform

def get_courses():
    username = argv[1]
    password = argv[2]
    chrome_options = Options()
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "normal"
    #chrome_options.add_argument("--headless")
    if platform.machine() == 'arm64':
        driver = webdriver.Chrome(desired_capabilities=caps, executable_path='./chromedriver', options=chrome_options)
    else: 
        driver = webdriver.Chrome(desired_capabilities=caps, executable_path='./chromedriver_intel', options=chrome_options)

    url = 'https://mytimetable.mcmaster.ca/login.jsp'

    wait = WebDriverWait(driver, 10)
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="word1"]'))).send_keys(username)
    driver.find_element(By.XPATH, '//*[@id="word2"]').send_keys(password)
    driver.find_element(By.XPATH, '//*[@id="bodyContent"]/div[2]/form/div/button').click()
    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="welcomeTerms"]/div/a'))).click()
    print("logged in! waiting for course data to load.")
    # Access requests via the `requests` attribute
    classdata = ''
    enrollment = ''
    while classdata == '' or enrollment == '':
        for request in driver.requests:
            if request.response and 'getclassdata' in request.url:
                classdata = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
                classdata = classdata.decode("utf8")
            if request.response and 'getEnrollment' in request.url:
                enrollment = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
                enrollment = enrollment.decode("utf8")

    f = open("classdata.xml", "w")
    f.write(classdata)
    f.close()

    f = open("enrollment.json", "w")
    f.write(enrollment)
    f.close()
    driver.quit()

    print("Got course data. Parsing.")

