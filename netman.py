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

from urllib import urlopen   # for testing the URL
import sys     # for logging 
import time    # needed to sleep
import subprocess   # opening subprograms 
import logging      # logging and debugging 

#-----------------------------------------------
def hasUSBdevice(devName):
    """ see if a USB device matching a string is plugged in
        Uses substring matching
    """ 

    message = 'testing for USB device: ' ; 
    logger.debug([message, devName]);
 
    proc = subprocess.Popen(['/usr/bin/lsusb'],stdout=subprocess.PIPE)
    for line in proc.stdout:
        
        if line.find(devName) >= 0:
            return True;

    return False;
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
    print "spawned init.d/networking " ;
    
    return True;

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
    """ Try to connect over the WiFi. uses a process list from the 
        program wnd
    """ 
   # get the list of access points and if they have a key 
    args = ['/sbin/iwlist' , 'wlan0', 'scan'];
    proc = subprocess.Popen(args,stdout=subprocess.PIPE)
    for line in proc.stdout:
        if line.find('Cell') >= 0:
            return True;
    return False;

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

    return hasKey & loadedModule;

#-----------------------------------------------
# try to connect to the 3G
def connect3G(): 
#wvdial <something>

    return True;

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
maxDevices = len(devConnects);
#where we are in the list
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

            for devIndex in range(0,maxDevices-1): 
                availableDevs.append( devTests.get(devIndex)() ) ;

            # if the device is there, try to connect                 
            for devIndex in range(0,maxDevices-1):                 

                if availableDevs[devIndex] == True:
                    print "trying device ", devConnects.get(devIndex) ;
                    devConnects.get(devIndex)();
                    time.sleep(5);
                    isConnected = testURL();

                # is the above worked, then break search for devices 
                if isConnected == True:
                    break;
    else: 
         logger.debug('got URL OK');

    logger.debug('got URL OK2'); 
    time.sleep(10);

                    
                    
                
