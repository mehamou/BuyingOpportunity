from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from datetime import datetime
from io import StringIO
import csv
from pymongo import MongoClient
from bson.binary import Binary
import pickle
import pymongo
from datetime import datetime, date
import json

def removeNonAscii(s): return "".join(i for i in s if ord(i)<128)

def checkingBoxes(driver,cbID):
    for i in range(10):
        try:
            webelt = driver.find_element_by_id(cbID)
            driver.execute_script("arguments[0].click();", webelt)
            # time.sleep(1)
            break
        except NoSuchElementException as e:
            print('Retry check the box in 1 second')
            # time.sleep(1)
        else:
            raise e

def setInputBoxes(driver,inputID,inputText):
    webelt = driver.find_element_by_class_name(inputID)
    webelt.send_keys(inputText)

def expandAll(driver,className):
    expandElts = driver.find_elements(By.CLASS_NAME,className)
    for webElt in expandElts:
        driver.execute_script("arguments[0].click();", webElt)
        # time.sleep(1)

def getURL(a):
    try:
      carurl = a.find_element_by_class_name('vehicle-data').get_attribute('href')
    except NoSuchElementException:
      carurl = " "
    return carurl

def num_months(start_date,end_date):
    numMonth = (end_date. year - start_date. year) * 12 + (end_date. month - start_date. month)
    return numMonth

#Retrieving number of results
def getNbResults(driver):
    roughStr = driver.find_element_by_class_name('search-result-header').get_attribute('data-result-count')
    roughStr = removeNonAscii(roughStr)
    return int(roughStr)

def nav_to_first_detailed_page(driver):
    firstArticleURL = getURL(driver.find_element_by_class_name('list-entry'))
    driver.get(firstArticleURL)
    time.sleep(1)

def readKMString(inputString):
    return int(inputString.replace("km","").replace(" ",""))

def convertStringMYtoDate(inputString):
    return datetime.strptime(inputString.replace(" ",""), '%m/%Y')

def readgRows(carAttributes,carDetails):
    for detail in carAttributes:
        temp = list(csv.reader(StringIO(detail.text),delimiter='\n'))
        carDetails.append([temp[0][0],temp[1][0]])

def readCarDetail(driver):
    carDetails = [['title',driver.find_element_by_class_name('h2').text]]
    carDetails.append(['prices',driver.find_element_by_class_name('h3').text])
    carAttributes = driver.find_element_by_class_name('attributes-box').find_elements(By.CLASS_NAME,'g-row')
    readgRows(carAttributes,carDetails)
    carTechData = driver.find_element_by_class_name('further-tec-data').find_elements(By.CLASS_NAME,'g-row')
    readgRows(carTechData,carDetails)
    optionElts = driver.find_elements(By.CLASS_NAME,'g-col-s-6')
    optionStr = ""
    first = True
    for optionEl in optionElts:
        if first:
            first = False
        else:
            optionStr+=';'
        optionStr+=optionEl.text
    carDetails.append(['options',optionStr])
    carDetails.append(['url',driver.current_url])
    return carDetails


#driver setting
DRIVER_PATH = '/Users/mehdihamou/Documents/ChromeDriver/chromedriver'
driver = webdriver.Chrome(executable_path=DRIVER_PATH)

#page opening
driver.get("https://www.automobile.fr/")

#removing cookies bot message
driver.find_element_by_xpath("//button[@id='gdpr-consent-accept-button']").click()

#search paramaters settings
driver.find_element_by_xpath("//select[@name='makeModelVariant1.make']/option[text()='Audi']").click()
time.sleep(3)
driver.find_element_by_xpath("//select[@name='makeModelVariant1.model']/option[text()='A3']").click()
driver.find_element_by_xpath("//select[@name='minFirstRegistration']/option[text()='2020']").click()
# time.sleep(3)
driver.find_element_by_xpath("//select[@name='maxMileage']/option[@value='100000']").click()
driver.find_element_by_xpath("//select[@name='fuelType']/option[text()='Diesel']").click()
# driver.find_element_by_class_name('search-btn').click()
# makeModelVariant1.modelDescription
#submitting button
driver.find_element_by_class_name('search-btn').click()
# time.sleep(3)

#setting the remaining parameters

#before setting parameters we need to expand all the Options
expandAll(driver,'expand-label')

checkingBoxes(driver,'gearBox_AUTOMATIC_GEAR')
checkingBoxes(driver,'features_ALLOY_WHEELS')
checkingBoxes(driver,'advertOption_PICTURES')

setInputBoxes(driver,'location-name-input','68300')
setInputBoxes(driver,'location-radius-input','1000')


driver.find_element_by_id('countryCode').find_element_by_xpath("//option[text()='Allemagne']").click()

#submitting remaining parameters
driver.find_element_by_class_name('btn--orange').click()

#setting results number per page to max
pageNumber = 50
driver.find_element_by_class_name('results-per-page').find_element_by_xpath("//a[text()='"+str(pageNumber)+"']").click()



# #browsing all pages
# print(nbResults)
# maxScrappingResults = 2000

# cars=[]
uncounteredCondition = True

# opening connection to mongodb
client = pymongo.MongoClient(
   "mongodb+srv://pyaccess:MZMde6jVAM5px3J@cluster0.3b9aj.mongodb.net/test?retryWrites=true&w=majority&connect=false")

db = client['ScrappedCars']

db.test.drop()
coll = db.test

nav_to_first_detailed_page(driver)
# browsing all ads
while uncounteredCondition:

    # founding car details
    try:
        carDetails = readCarDetail(driver)



        # storing data to mongodb
        coll.insert_one(dict(carDetails))


    except NoSuchElementException:
        print("cars details not found")

    # founding consulted page and compare to number of results
    try:
        roughtAdNumber = driver.find_element_by_class_name('u-inline').text
        pagesVSresults=list(csv.reader(StringIO(roughtAdNumber),delimiter='/'))
        currentPage = pagesVSresults[0][0].replace(" ","")
        numberResult = pagesVSresults[0][1].replace(" ","")
        if (currentPage==numberResult):
            break
    except NoSuchElementException:
        print("number details not found")

    # navigating through the next car
    try:
        navArrows = driver.find_elements(By.CLASS_NAME,'nav-arrow')
        lastNavArrows = len(navArrows)
        if lastNavArrows > 0:
            lastNavArrows = lastNavArrows - 1
            navArrows[lastNavArrows].click()
            time.sleep(1)
        else:
            try:
                driver.find_element_by_class_name('btn').click()
                nav_to_first_detailed_page(driver)
            except NoSuchElementException:
                print("get back to result research button not found")
    except NoSuchElementException:
        print("nav arrow element not found")
        break






# browing all car detailed pages

#
# for i in range(len(cars)):
#     url = len(cars[i])-1
#     driver.get(cars[i][url])
#     WebDriverWait(driver,timeout=3).until(document_initialised)
#closing driver windows
driver.quit()
# f.close
