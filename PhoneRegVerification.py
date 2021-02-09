##################################################
# Phone Registration Verification
# This script is intended to use the UCM RisPort
# to find which phones are registered to Call Manager
# both before and after a change, to confirm all
# phones re-register.
#
# Version 1.0
# Created for Converged Technology Group
# By Dave Lamb - 10/28/2020
##################################################

from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from zeep.exceptions import Fault
from zeep.plugins import HistoryPlugin
from requests import Session
from requests.auth import HTTPBasicAuth
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from lxml import etree
import getpass
from os.path import abspath
from os import path
import os
import requests
import time, datetime

disable_warnings(InsecureRequestWarning)


#Collect OS Admin Credentials
print("\n")
print("="*75)
print("Enter the IP address or FQDN for this cluster")
print("Do not include the http reference")
print("E.G.: ucmpub.customer.com")
print("="*75)
server = input("Cluster Address: ")


#Collect OS Admin Credentials
print("\n")
print("="*75)
print("Enter the UCM credentials for this cluster")
print("At minimum the application user account requires *Standard CCM Server Monitoring* rights")
print("="*75)
strUCMAdmUserID = input("User ID: ")
strUCMAdmPassword = getpass.getpass(prompt="Password: ")

#Is this first run or verify pass
print("\n")
print("="*75)
print("Is this the first run, or post change verification?")
print("Enter F for First Run or V for verification")
print("="*75)
verifypass = input("F or V: ")
verifypass = verifypass.lower()

for i in range(1, 4):
    if i == 3:
        print("\n")
        print("="*75)
        print("Invalid selection, you messed it up three times!")
        print("What's wrong with you? Go get some coffee and try again.")
        print("="*75)
        exit()
    if verifypass == "f" or verifypass == "v":
        if verifypass == "f":
            print("\n")
            print("="*75)
            print("This is the Pre-change data collection")
            print("="*75)
        elif verifypass == "v":
            print("\n")
            print("="*75)
            print("This is the Post-change Verification")
            print("="*75)

        break
    else:
        verifypass = input("F or V: ")
        verifypass = verifypass.lower()

#Collect Timestamps
print("\n")
print("="*75)
print("If your change causes phones to reregister, the timestamps will change,")
print("this will cause the Diff file to note all phones have changed. If you only")
print("want to find the phones that failed to register, do not collect timestamps.")
print("Collect Timestamps?")
print("="*75)
collecttime = input("Y or N: ")
collecttime = collecttime.lower()

for i in range(1, 4):
    if i == 3:
        print("\n")
        print("="*75)
        print("Invalid selection, you messed it up three times!")
        print("What's wrong with you? Go get some coffee and try again.")
        print("="*75)
        exit()
    if collecttime == "y" or collecttime == "n":
        if collecttime == "y":
            print("\n")
            print("="*75)
            print("We will collect timestamps.")
            print("="*75)
        elif collecttime == "n":
            print("\n")
            print("="*75)
            print("We will not collect timestamps")
            print("="*75)

        break
    else:
        verifypass = input("F or V: ")
        verifypass = verifypass.lower()


#==============================Define Functions=================================
#Compare function that compares the before and after files
#Function takes OS Path and file name as strings
def compare(OrigCSVPath,VerifyCSVPath, Timestamps):
    #See if a Diff file exists, and if so, delete it
    diffileName = 'Differences.csv'
    if path.exists(abspath(diffileName)):
        print("="*75)
        print('A diff file already exists')
        print('Delete Existing File and Continue?')
        print("="*75)
        deleteFile = input("Y or N: ")
        deleteFile = deleteFile.lower()
        if deleteFile == 'y':
            os.remove(abspath(diffileName))
        else:
            print('Please manually remove the file or chose V and run the script again')
            exit()
    
    #Create a new Diff File and write the header
    diffCSV = open(abspath(diffileName),'a')
    if Timestamps == 'y':
        diffCSV.write("Name,Description,Device Pool,Status,Last Reg Change UTC,DN,IP,Active Load,Download Status,Download Fail Reason,Type\n")
    else:
        diffCSV.write("Name,Description,Device Pool,Status,DN,IP,Active Load,Download Status,Download Fail Reason,Type\n")
    
    #Open and read the text from the files to compare
    OrigCSV = open(OrigCSVPath, 'r')
    VerifyCSV = open(VerifyCSVPath, 'r')
    OrigCSVText = OrigCSV.read()
    VerifyCSVText = VerifyCSV.read()

    #Split the text in to a List where each element is a line from the files
    OrigCSVLines = OrigCSVText.split('\n')
    VerifyCSVLines = VerifyCSVText.split('\n')

    #Loop through Verification CSV to 
    for line in VerifyCSVLines:
        if line not in OrigCSVLines:
            diffCSV.write(line + '\n')

    diffCSV.close()


#==============================Define Functions=================================

#===================Setup Zeep Soap Client for AXL Connection===================
#Collect path to the UCM AXL Schema
#The schema files are downloaded from UCM > Applications > Plugins > Cisco AXL Toolkit
axlwsdl = abspath('axlsqltoolkit/schema/current/AXLAPI.wsdl')
axllocation = 'https://{host}:8443/axl/'.format(host=server)
axlbinding = "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding"

# Define http session and allow insecure connections
axlsession = Session()
axlsession.verify = False
requests.packages.urllib3.disable_warnings()
axlsession.auth = HTTPBasicAuth(strUCMAdmUserID, strUCMAdmPassword)

#Define a SOAP client
axltransport = Transport(cache=SqliteCache(), session=axlsession, timeout=20)
axlclient = Client(wsdl=axlwsdl, transport=axltransport)
axlservice = axlclient.create_service(axlbinding, axllocation)
#===================Setup Zeep Soap Client for AXL Connection==================



#===================Setup Zeep Soap Client for RIS Connection===================
#Collect path to the UCM AXL Schema
#The schema files are downloaded from UCM > Applications > Plugins > Cisco AXL Toolkit
riswsdl = f'https://{server}:8443/realtimeservice2/services/RISService70?wsdl'

# Define http session and allow insecure connections
rissession = Session()
rissession.trust_env = False
rissession.verify = False
requests.packages.urllib3.disable_warnings()
rissession.auth = HTTPBasicAuth(strUCMAdmUserID, strUCMAdmPassword)

#Define a SOAP client
ristransport = Transport(cache=SqliteCache(), session=rissession, timeout=20)
risclient = Client(wsdl=riswsdl, transport=ristransport)
#===================Setup Zeep Soap Client for RIS Connection==================


#===================Meat and Potatoes==================

#Generate the output files
if verifypass == 'f':
    fileName = 'FirstPass.csv'
    if path.exists(abspath(fileName)):
        print('You chose F for the First Pass and a First pass file exists')
        print('Delete Existing File?')
        deleteFile = input("Y or N: ")
        deleteFile = deleteFile.lower()
        if deleteFile == 'y':
            os.remove(abspath(fileName))
        else:
            print('Please manually remove the file or chose V and run the script again')
            exit()
else:
    fileName = 'VerifyPass.csv'
    if path.exists(abspath(fileName)):
        print('You chose V for the Verify Pass and a verification file exists')
        print('Delete Existing File?')
        deleteFile = input("Y or N: ")
        deleteFile = deleteFile.lower()
        if deleteFile == 'y':
            os.remove(abspath(fileName))
        else:
            print('Please manually remove the file and run the script again')
            exit()

csvFile = open(abspath(fileName), mode="a")


# Create AXL Call to collect all the phones because RIS will only return 1000 phones
# We need to collect the phones first via AXL and then loop through them via RIS
phoneAXLresponse = axlservice.listPhone(
            searchCriteria={
                'name': '%'
            },
            returnedTags={
                'name': True
        })

phoneNames = phoneAXLresponse['return'].phone

#Print output headers to Screen
print("="*203)
print('{:18}{:30}{:20}{:23}{:13}{:18}{:30}{:18}'.format("Name", "Description", "Status", "Last Reg Change UTC", "DN", "IP", "Active Load", "Type"))
print("="*203)

#Write the Output headers to disk
if collecttime == 'y':
    csvFile.write("Name,Description,Device Pool,Status,Last Reg Change UTC,DN,IP,Active Load,Download Status,Download Fail Reason,Type\n")
else:
    csvFile.write("Name,Description,Device Pool,Status,DN,IP,Active Load,Download Status,Download Fail Reason,Type\n")

#Loop through the AXL Results and use that as the Selection Critera for RIS lookup
#We are looking for phones that are registered to UCM
#Documentation can be found here:  https://paultursan.com/2018/12/getting-cucm-real-time-data-via-risport70-with-python-and-zeep-cisco-serviceability-api/

#loop through each Phone Found in AXL List
phoneCount = 0
for phone in phoneNames:
    #Count the number of passes to report on number of devices found
    phoneCount = phoneCount + 1

    #Set the RIS search criteria for this phone
    risSelectionCriteria = {
        'MaxReturnedDevices': '1000',
        'DeviceClass': 'Any',
        'Model': '255',
        'Status': 'Any',
        'NodeName': '',
        'SelectBy': 'Name',
        'SelectItems': {
            'item': phone.name
        },
        'Protocol': 'Any',
        'DownloadStatus': 'Any'
    }

    StateInfo = ''
    
    #Execute RIS Query
    phoneStatus = risclient.service.selectCmDeviceExt(CmSelectionCriteria=risSelectionCriteria, StateInfo=StateInfo)
    CmNodes = phoneStatus.SelectCmDeviceResult.CmNodes.item

    #Test if the RIS data returned a result
    devicesFound = phoneStatus.SelectCmDeviceResult.TotalDevicesFound

    #Use AXL to get device details
    phoneresponse = axlservice.getPhone(name = phone.name)
    phoneAXL = phoneresponse['return'].phone

    #Assign AXL Lookup Results to variables
    PhoneName = phoneAXL.name
    PhoneDesc = phoneAXL.description
    if not PhoneDesc:
        PhoneDesc = 'None'
    PhoneType = phoneAXL.product
    DevPoolList = phoneAXL.devicePoolName
    PhoneDevPool = DevPoolList._value_1
    linesList = phoneAXL.lines
    try:
        PhoneDN = linesList.line[0].dirn.pattern
    except:
        PhoneDN = 'No DN'

    #If RIS returned data, collect the RIS data
    if devicesFound == 1:
        #RIS results will list a response for each UCM Node, so we have to loop through the nodes
        for CmNode in CmNodes:
            if len(CmNode.CmDevices.item) > 0:
                # If the node has returned CmDevices, Loop the devices even though there should only be one found
                for item in CmNode.CmDevices.item:
                    #Collect RIS status
                    PhoneStatus = item.Status
                    #Timestamp field is Seconds since Linux Epoch of the last change in registration status
                    #Convert to human readible time
                    PhoneTimestamp = item.TimeStamp
                    PhoneLastRegChange = time.strftime('%m/%d/%Y %I:%M:%S %p', time.gmtime(PhoneTimestamp))

                    PhoneActiveLoad = item.ActiveLoadID
                    if PhoneActiveLoad is None:
                        PhoneActiveLoad = 'Unknown'

                    PhoneDwnLdStatus = item.DownloadStatus
                    PhoneDwnLdFailReasons = item.DownloadFailureReason
                    if PhoneDwnLdFailReasons is None:
                        PhoneDwnLdFailReasons = 'Unknown'

                    #if IP Address fails to populate, Return Unknown                   
                    try:
                        IPAddressInfoList = item.IPAddress.item
                        PhoneIP = IPAddressInfoList[0].IP
                    except:
                        PhoneIP = 'Unknown'
    else:
        #If RIS returned no Results, populate this information
        PhoneStatus = 'No RIS Status'
        PhoneIP = 'No RIS IP Addr'
        PhoneLastRegChange = 'Never'
        #Some Devices have AXL Stored Load Info, we might be able to collect this\
        loadInfoList = phoneAXL.loadInformation
        PhoneActiveLoad = loadInfoList._value_1
        if not PhoneActiveLoad:
            PhoneActiveLoad = 'Unknown'
        PhoneDwnLdStatus = 'No RIS Dwnld Status'
        PhoneDwnLdFailReasons = 'No RIS Dwnld Reason'

    print("{:18}{:31}{:20}{:23}{:14}{:18}{:30}{:18}".format(PhoneName, PhoneDesc[0:30], PhoneStatus, PhoneLastRegChange, PhoneDN, PhoneIP, PhoneActiveLoad[0:30], PhoneType))

    if collecttime == 'y':
        csvFile.write(PhoneName + ',' + PhoneDesc + ',' + PhoneDevPool + ',' + PhoneStatus + ',' + PhoneLastRegChange + ',' + PhoneDN + ',' + PhoneIP + ',' + PhoneActiveLoad + ',' + PhoneDwnLdStatus + ',' + PhoneDwnLdFailReasons + ',' + PhoneType + '\n')
    else:
        csvFile.write(PhoneName + ',' + PhoneDesc + ',' + PhoneDevPool + ',' + PhoneStatus + ','  + PhoneDN + ',' + PhoneIP + ',' + PhoneActiveLoad + ',' + PhoneDwnLdStatus + ',' + PhoneDwnLdFailReasons + ',' + PhoneType + '\n')

csvFile.close

print("="*203)
print('Returned ' + str(phoneCount) + ' Phones.')
print("="*203)

#If this is the verification pass, compare the first and second pass and create Diff file
if verifypass == 'v':
    firstfile = abspath('FirstPass.csv')
    verifyfile = abspath('VerifyPass.csv')

    compare(firstfile, verifyfile, collecttime)


