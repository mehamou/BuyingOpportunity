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
driver.find_element_by_xpath("//select[@name='minFirstRegistration']/option[text()='2016']").click()
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

#Retrieving number of results
# roughStr = driver.find_element_by_class_name('search-result-header').get_attribute('data-result-count')
# roughStr = removeNonAscii(roughStr)
# nbResults = int(roughStr)

#setting results number per page to max
pageNumber = 50
driver.find_element_by_class_name('results-per-page').find_element_by_xpath("//a[text()='"+str(pageNumber)+"']").click()


# #browsing all pages
# print(nbResults)
# maxScrappingResults = 2000

class Car:
    def __init__(self, scrapedList,url):
        # first element is title of the ad
        i=1
        self.title = scrapedList[i][0]
        i+=1

        # setting all parameters to empty string
        self.firstResistration = " "
        self.miles = " "
        self.power = " "
        self.typeFuelGearB = " "
        self.colNbDoor = " "
        self.CO2 = " "
        self.priceATI = " "
        self.priceWT = " "
        self.ratioMileRegis = " "

        for i in range(len(scrapedList)):
            # catching mileAge and First registration date
            if "km" in scrapedList[i][0] and "Distance" not in scrapedList[i][0] and "CO2" not in scrapedList[i][0] and "Consommation" not in scrapedList[i][0] and "Professionnel" not in scrapedList[i][0] and "Particulier" not in scrapedList[i][0]:
                ageMiles = list(csv.reader(StringIO(scrapedList[i][0]),delimiter=','))
                if "km" in ageMiles[0][0]:
                    tempMiles = ageMiles[0][0]
                    tempFirstRegistration = "01/2021"
                else:
                    tempFirstRegistration = ageMiles[0][0]
                    tempMiles = ageMiles[0][1]
                tempMiles = tempMiles.replace("km","")
                tempMiles = tempMiles.replace(" ","")
                try:
                  self.miles = int(tempMiles)
                except ValueError:
                  self.miles = 0
                try:
                  self.firstResistration = datetime.strptime(tempFirstRegistration.replace(" ",""), '%m/%Y')
                except ValueError:
                  self.firstResistration = datetime.today()
                try:
                    self.ratioMileRegis = self.miles / num_months(self.firstResistration,date.today())
                except ValueError:
                    self.ratioMileRegis = ""
                except ZeroDivisionError:
                    self.ratioMileRegis = 0

            #catching power
            elif "kW" in scrapedList[i][0]:
                self.power = scrapedList[i][0]
            #catching fuel type
            elif "Diesel" in scrapedList[i][0]:
                self.typeFuelGearB = scrapedList[i][0]
            # catching nb doors
            elif "portes" in scrapedList[i][0] or "Couleur" in scrapedList[i][0]:
                self.colNbDoor = scrapedList[i][0]
            # catching co2 consumption
            elif "CO2" in scrapedList[i][0]:
                self.CO2 = scrapedList[i][0]
            # catching price all taxes included
            elif "TTC" in scrapedList[i][0]:
                self.priceATI = scrapedList[i][0]
            # catching price without taxes
            elif "HT" in scrapedList[i][0]:
                self.priceWT = scrapedList[i][0]

        if url is not None:
            self.url = url
        else: self.url = " "


    def __str__(self):
        return 'title: '+self.title+', firstResistration: '+self.firstResistration+', mileAge: '+self.mileAge+', power: '+self.power+', type: '+self.type+', fuelType: '+self.fuelType+', gearBoxType: '+self.gearBoxType+', url: '+self.url

    # function to return structure before sending the information to mongo
    def toMongo(self):
        return {
            "title":self.title,
            "firstResistration":self.firstResistration,
            "Miles":self.miles,
            "ratio Mile Registration":self.ratioMileRegis,
            "power":self.power,
            "type, fuel, gearBoxType": self.typeFuelGearB,
            "colors, doors number":self.colNbDoor,
            "CO2":self.CO2,
            "priceATI":self.priceATI,
            "priceWT":self.priceWT,
            "url":self.url,
        }

cars=[]
uncounteredCondition = True

firstArticleURL = getURL(driver.find_element_by_class_name('list-entry'))
driver.get(firstArticleURL)
time.sleep(0.5)
# browsing all ads
while uncounteredCondition:
    try:
        navArrows = driver.find_elements(By.CLASS_NAME,'nav-arrow')

        lastNavArrows = len(navArrows)
        if lastNavArrows > 0:
            lastNavArrows = lastNavArrows - 1
            navArrows[lastNavArrows].click()
            time.sleep(0.5)
        else:
            driver.find_element_by_class_name('btn').click()
            firstArticleURL = getURL(driver.find_element_by_class_name('list-entry'))
            driver.get(firstArticleURL)
            time.sleep(0.5)
    except NoSuchElementException:
        print("element not found")
        break
    #
    # for a in roughArticles:
    #   carAttList = list(csv.reader(StringIO(a.text),delimiter='\n'))
    #   carurl = getURL(a)
    #   carAttList.append(carurl)
    #   cars.append(carAttList)
    # break
    # #moving to next pages
    # try:
    #     driver.find_element_by_class_name('pagination-nav-right').click()
    # except NoSuchElementException:
    #     break



#opening connection to mongodb
# client = pymongo.MongoClient(
#    "mongodb+srv://pyaccess:MZMde6jVAM5px3J@cluster0.3b9aj.mongodb.net/test?retryWrites=true&w=majority&connect=false")
#
# db = client['ScrappedCars']
#
# db.test.drop()
# coll = db.test
# storing data to mongodb
  # car = Car(carAttList,carurl)
  # coll.insert_one(car.toMongo())
# browing all car detailed pages

#
# for i in range(len(cars)):
#     url = len(cars[i])-1
#     driver.get(cars[i][url])
#     WebDriverWait(driver,timeout=3).until(document_initialised)
#closing driver windows
driver.quit()
# f.close
