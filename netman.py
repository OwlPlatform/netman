#!/usr/bin/python 

# this is a very simple connection manager.
# It assumes there are 3 possible networks: (1) Ethernet, (2) WiFi and (3) 3G modem.
# The manager attempts to connect to the internet in that priority order.
# It assumes DHCP runs on all the networks.
# Connectivity is defined by the ability to reach a web site that is 
# currently hard-coded.   
# 
# Author: Richard P. Martin
# Date: April 2013 
# (c) the MIT license 

# iwlist parsing from Hugo Chargois - 17 jan. 2010 - v.0.1
# https://bbs.archlinux.org/viewtopic.php?id=88967

from urllib import urlopen   # for testing the URL
import sys     # for logging and iwlist parsing 
import time    # needed to sleep
import subprocess   # opening subprograms 
import logging      # logging and debugging 

#-----------------------------------------------
def hasUSBdevice(devName):
    """ see if a USB device matching a string is plugged in
        Uses substring matching
    """ 

    foundIt = False; 
    message = 'testing for USB device: ' ; 
    logger.debug([message, devName]);
 
    proc = subprocess.Popen(['/usr/bin/lsusb'],stdout=subprocess.PIPE)
    for line in proc.stdout:
        if line.find(devName) >= 0:
            foundIt = True;

    proc.wait();
    return foundIt;
#----------------------------------------------
#
def hasModule(modName):
    """ See is a kernel module matching a given name is loaded 
        Uses substring matching
    """

    f = open('/proc/modules','r');
    allLines = f.readlines();
    f.close;
    for line in allLines:
        if line.find(modName ) >= 0:
            return True;

    return False;
#----------------------------------------------
def etherPluggedIn(): 
    """ Determine if the Pi's ethernet is plugged in. Uses 
        the carrier of the Ethernet 
    """ 
    isConnected = False; 

    logger.debug('testing for ethernet carrier'); 

    f = open('/sys/class/net/eth0/carrier','r');
    isConnected = f.readline().strip();
    f.close();

    # the cable is not plugged in
    if isConnected == '0' :
        return False; 
    else:  
        return True;     


#----------------------------------------------
def connectEthernet(): 
    """ Try to establish and internet connect over the Ethernet
        Uses the dumb way of calling init.d/networking
    """ 
    # the cable is plugged in
    # we got here, try to re-start the networking.
    args = ['/etc/init.d/networking' , 'networking', 'restart'];
    proc = subprocess.Popen(args,stdout=subprocess.PIPE)
    logger.debug('spawned /etc/init.d/networking');

    wasOK = False; 

    # look for the string 'OK' in the output.

    for line in proc.stdout:
        if line.find('ok') >= 0:
            wasOK = True;

    proc.wait();

    return wasOK;

#-----------------------------------------------
# try to connect to the WiFi
# lsmod | grep 8192cu
def hasWiFi(): 

    # check for a key plugged into the USB 
    # just check for 1 key type for now, can change later. 
    hasKey =  hasUSBdevice("Edimax");

    loadedModule = hasModule("8192cu");

    return hasKey & loadedModule;

#-----------------------------------------------
def connectWiFi(): 
    """ Try to connect over the WiFi. 
    """ 
    ap_table = do_wifi_scan(); 

    for line in ap_table:
        print line

    return False;

# from /usr/sbin/wpa_gui
# iwlist wlan0 scan
# iwconfig wlan0 essid <SOMETHING>
#/sbin/ifplugd -i wlan0 -q -f -u0 -d10 -w -I
#/wpa_supplicant -u -s -O /var/run/wpa_supplicant
#/sbin/wpa_supplicant -s -B -P /var/run/wpa_supplicant.wlan0.pid -i wlan0 -W -D nl80211,wext -c /etc/wpa_supplicant/wpa_supplicant.conf
#/wpa_cli -B -P /var/run/wpa_action.wlan0.pid -i wlan0 -p /var/run/wpa_supplicant -a /sbin/wpa_action

    return 

#-----------------------------------------------
# check if we have a 3G card 
def has3Gcard(): 
    hasDongle =  hasUSBdevice("Airprime");
    loadedModule = hasModule("usbserial");

    has3G = hasDongle & loadedModule; 

    logger.debug([ "3G device: ", has3G ]);

    return has3G;

#-----------------------------------------------
# try to connect to the 3G
def connect3G(): 
#wvdial <something>

    return False;

#-----------------------------------------------
def testURL(): 
    """ Test if we can download a given URL. Note that a DNS failure can take 30
    seconds to fail if the network is connected but down
    """

    isConnected = False; 
    try: 
        doc = urlopen("http://www.google.com/").read()
        isConnected = True;
    except IOError:
        isConnected = False;

    return False;
#    return isConnected;

#----------------------------------------------------------
#--- these are the functions to parse the iwlist output 
#----------------------------------------------------------
def get_name(cell):
    return matching_line(cell,"ESSID:")[1:-1]

def get_quality(cell):
    quality = matching_line(cell,"Quality=").split()[0].split('/')
    return str(int(round(float(quality[0]) / float(quality[1]) * 100))).rjust(3) + " %"

def get_channel(cell):
    return matching_line(cell,"Channel:")

def get_encryption(cell):
    enc=""
    if matching_line(cell,"Encryption key:") == "off":
        enc="Open"
    else:
        for line in cell:
            matching = match(line,"IE:")
            if matching!=None:
                wpa=match(matching,"WPA Version ")
                if wpa!=None:
                    enc="WPA v."+wpa
        if enc=="":
            enc="WEP"
    return enc

def get_address(cell):
    return matching_line(cell,"Address: ")

# Here's a dictionary of rules that will be applied to the description of each
# cell. The key will be the name of the column in the table. The value is a
# function defined above.

rules={"Name":get_name,
       "Quality":get_quality,
       "Channel":get_channel,
       "Encryption":get_encryption,
       "Address":get_address,
       }

# Here you can choose the way of sorting the table. sortby should be a key of
# the dictionary rules.

def sort_cells(cells):
    sortby = "Quality"
    reverse = True
    cells.sort(None, lambda el:el[sortby], reverse)

# You can choose which columns to display here, and most importantly in what order. Of
# course, they must exist as keys in the dict rules.

columns=["Name","Address","Quality","Channel","Encryption"]


def matching_line(lines, keyword):
    """Returns the first matching line in a list of lines. See match()"""
    for line in lines:
        matching=match(line,keyword)
        if matching!=None:
            return matching
    return None

def match(line,keyword):
    """If the first part of line (modulo blanks) matches keyword,
    returns the end of that line. Otherwise returns None"""
    line=line.lstrip()
    length=len(keyword)
    if line[:length] == keyword:
        return line[length:]
    else:
        return None

def parse_cell(cell):
    """Applies the rules to the bunch of text describing a cell and returns the
    corresponding dictionary"""
    parsed_cell={}
    for key in rules:
        rule=rules[key]
        parsed_cell.update({key:rule(cell)})
    return parsed_cell

def print_table(table):
    for line in table:
        print line

def print_cells(cells):
    table=[columns]
    for cell in cells:
        cell_properties=[]
        for column in columns:
            cell_properties.append(cell[column])
        table.append(cell_properties)

    return table;

def do_wifi_scan():
    """ Do an iwlist scan and return the results in a simple table """
    cells=[[]] ;
    parsed_cells=[] ;

   # get the list of access points and if they have a key 
    args = ['/sbin/iwlist' , 'wlan0', 'scan'];
    proc = subprocess.Popen(args,stdout=subprocess.PIPE);
    
    for line in proc.stdout:
        cell_line = match(line,"Cell ");
        if cell_line != None:
            cells.append([]); 
            line = cell_line[-27:]; 
        cells[-1].append(line.rstrip()); 

    proc.wait();
    cells=cells[1:] ;

    for cell in cells:
        parsed_cells.append(parse_cell(cell));

    sort_cells(parsed_cells) ;

    table = print_cells(parsed_cells);
    
    return table;


#------------------------------------------
# this is the main program
keepGoing = True;

# this is the logging stuff
logger = logging.getLogger(); 
logger.setLevel(logging.DEBUG);

# create console handler and set level to debug
ch = logging.StreamHandler( sys.__stdout__ ) 
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# this is the list of devices to try, in which order 
devTests = { 0 : etherPluggedIn , 1 : hasWiFi, 2 : has3Gcard }; 
devConnects =  { 0: connectEthernet, 1: connectWiFi, 2: connect3G, };
devNames = { 0 : 'Ethernet', 1 : 'WiFi', 2 : '3GModem' }; 

maxDevices = len(devConnects);

#where we are in the list of devices 
devIndex = 0; 

# First, see if we are connected by downloading a URL 
# If the download fails, the work manager walks the list of devices,
# checking which ones are plugged in/available, and creates an array 
# of devices that are plugged in.
# It then walks the available list, and tried to connect in priority 
# order. After each connection attempt, it tries to download the 
# URL again. If that succeeds, the loop is done. If not, it moves 
# on to the next device. 

while (keepGoing):

    if testURL() == False :
        print "getting the URL failed" ;
        devIndex = 0; 
        isConnected = False; 


        while isConnected == False : 
            # make a list of all available devices 
            availableDevs = []; 

            for devIndex in range(0,maxDevices): 
                availableDevs.append( devTests.get(devIndex)() ) ;

            # if the device is there, try to connect                 
            for devIndex in range(0,maxDevices):                 

                if availableDevs[devIndex] == True:
                    print "Trying device ", devNames.get(devIndex) ;
                    success = devConnects.get(devIndex)();
                    time.sleep(5);
                    isConnected = testURL();

                # is the above worked, then break search for devices 
                if isConnected == True:
                    break;
    else: 
         logger.debug('got URL OK');

    time.sleep(10);

                    
                    
                
