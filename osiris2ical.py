#!/usr/bin/env python -W ignore::DeprecationWarning
#
#
#          Author: Hiram (  hiram_ AT g m x DOT n e t   )
#		   Website: http://gitorious.org/osiris2ical#more
#          License: GPL v3 or later  (http://www.fsf.org/licensing/licenses/agpl-3.0.html)        
#          Dependencies: Beautiful Soup (http://www.crummy.com/software/BeautifulSoup/)  Python License
#                        Ical for python (http://pypi.python.org/pypi/icalendar/2.0.1)  LGPL
#          Install: 1. Download depencies and install using "python setup.py install" in the map of the dependency
#                   2. Drop this file somewhere and make sure it is chmodded to execute
#
#
#
VERSION='1.1'
ICALFILE='rooster.ics'


import urllib2
import urllib
import cookielib
from BeautifulSoup import BeautifulSoup, Tag, NavigableString
from icalendar import Calendar, Event, Timezone
from datetime import datetime
from icalendar import UTC # timezone
import os.path
import re
import time
import sys
import getpass
from optparse import OptionParser

monthnames = ['Januari', 
              'Februari', 
              'Maart', 
              'April', 
              'Mei', 
              'Juni', 
              'Juli', 
              'Augustus', 
              'September', 
              'Oktober', 
              'November', 
              'December']




    
def main():
    usage = "usage: %prog <username>"
    version = "version: " + VERSION
    parser = OptionParser(usage, version=version)
    (options, args) = parser.parse_args()
    
    if len(args) != 1:
        parser.error("incorrect number of arguments")
    
    username = args[0]
    
    password = getpass.getpass()    
    page = getPage(username, password)
    cal = parsePage(page, username)
    saveIcal(cal)

                  
def getPage(username, password):
    #set up cookie handler
    cj = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)
    
    #http request set up
    txheaders =  {'User-Agent' : ' Mozilla/5.0 (Roosterdata spider, stelletje prutsers waarom moet ik dit zelf doen?)'}
    
    url = 'https://www.osiris.universiteitutrecht.nl/osistu_ospr/AuthenticateUser.do'
    postvalues = {'gebruikersNaam' : username,
              'wachtWoord' : password ,
              'event' : 'login' }
    loginrequest = urllib2.Request(url ,urllib.urlencode(postvalues), txheaders)
    
    url = 'https://www.osiris.universiteitutrecht.nl/osistu_ospr/KiesRooster.do'
    postvalues = {'event' : 'toonTotaalrooster' } 
    datarequest = urllib2.Request(url ,urllib.urlencode(postvalues), txheaders)
    
    #actual requests
    #inlog request, geeft ons een cookie
    page = urllib2.urlopen(loginrequest)
    
    #check of we wel echt zijn ingelogged
    if not checkLoggedIn(page):
        print('De ingevoerde inloggegevens kloppen niet!')
        sys.exit(2)
    
    #fucked up osiris request, anders krijgen we een fout
    page = urllib2.urlopen(url)
    
    #data request, hiermee krijgen we data
    page = urllib2.urlopen(datarequest)
    return page


def checkLoggedIn(page):
    soup = BeautifulSoup(page)
    return soup.find(text=re.compile("Laatst ingelogd")) != None


def parsePage(page, username):
    soup = BeautifulSoup(page)
  
    geroosterd =  soup('span', id="RoosterIngeroosterd0")[0].find('table', "OraTableContent")
    ingeloggedstring = soup.find(text=re.compile("Laatst ingelogd"))

    m = re.search('(\d{4})',ingeloggedstring)
    jaar = int(m.group(0))

    #print 'Niet geroosterd'
    #print soup('span', id="RoosterNietIngeroosterd0")[0].find('table', "x1h")
    
    #setup calendar
    cal = Calendar()
    cal.add('version', '2.0')
    cal.add('prodid', '-//Mijn Rooster//osiris.uu.nl//')
    cal.add('x-wr-calname', 'Rooster')
    cal.add('X-WR-TIMEZONE', 'Europe/Amsterdam')
    
    newtimezone = Timezone()
    newtimezone.add('tzid', "Europe/Amsterdam")
    cal.add_component(newtimezone)


    #get the data out and into the calendar
    maand = 0
    dag = 0
    for tr in geroosterd:
        if tr.contents[0].contents[0].name == 'table':
            #get the day
            dag = int(tr.contents[0].tr.contents[1].span.string) if len(tr.contents[0].tr.contents[1].span.string) > 1 else dag
      
            #get the time
            tijd = tr.contents[0].tr.contents[2].span.string
            startuur = int(tijd[1:3])
            startmin = int(tijd[4:6])
            enduur = int(tijd[10:12])
            endmin = int(tijd[13:15])
      
            #get the other data
            vakcode = tr.contents[1].span.string
            naam = tr.contents[3].span.string
            ctype = tr.contents[5].span.string
            groep = tr.contents[7].span.string if tr.contents[7].span != None else ''
            gebouw = tr.contents[9].a.string if tr.contents[9].a != None else ''
            ruimte = tr.contents[11].span.string if tr.contents[11].span != None else ''
            docent = tr.contents[13].span.string  if tr.contents[13].span != None else ''
              
            description = groep + '\n' if groep != '' else ''
            description += 'docent: ' + docent if docent != '' else ''
              
            #make an event and add it
            event = Event()
            event.add('summary', ctype + ' ' + naam)
            event.add('location', gebouw + ' ' + ruimte)
            event.add('description', description)
            event.add('dtstart', datetime(jaar,maand,dag,startuur,startmin,0))
            event.add('dtend', datetime(jaar,maand,dag,enduur,endmin,0))
            event.add('dtstamp', datetime.now())
            event['uid'] = str(jaar)+str(maand)+str(dag)+'T'+str(startuur)+str(startmin)+'00/'+username+vakcode+str(datetime.now().toordinal())+'0@osiris.uu.nl'
            cal.add_component(event)
      
        elif tr.contents[0].name == 'td':
            #record the new month and check if we are in the next year  
            maand = monthnames.index(tr.contents[0].span.string) + 1
            if maand == 1:
                jaar = jaar + 1
    return cal
  
def saveIcal(cal):  
    icalFile = open(ICALFILE, 'w')
    icalFile.write(cal.as_string())
    icalFile.close()
    print('ical opgeslagen in rooster.ics')


if __name__ == "__main__":
    main()
