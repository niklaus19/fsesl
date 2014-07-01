#!/usr/bin/python
from twisted.web import server, resource
import json
from twisted.internet import reactor
import logging
from ESL import *
import re
import ConfigParser
import logging.handlers
from twisted.application import service, strports


con = ESLconnection("127.0.0.1","8021","ClueCon")
headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
url = "http://192.168.1.219:8080"

config = ConfigParser.ConfigParser()
config.read("/opt/Freeswitch-ESL/fsesl.conf")

fsip = config.get("Freeswitch", "ipaddress")
fsport = config.get("Freeswitch","port")
fspasswd = config.get("Freeswitch","password")
logpath= config.get("Log","path")


log = logging.getLogger('fsesl')
hdlr = logging.handlers.RotatingFileHandler(logpath+'fsesl.log', maxBytes=5120, backupCount=10)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)

if con.connected:
    log.debug("Successfully connected to Freeswitch")
    con.events("plain", "all")
    connected=con.connected()

class WebServer(resource.Resource):
    isLeaf = True
    def render_GET(self, request):
        command = request.uri [1:99]
        if command == "calls":
            command = "show calls"
        else:
            command = "show registrations"
        log.debug("The requested command is %s",command)
        con = ESLconnection(fsip,fsport,fspasswd)
        connected=con.connected()
        if connected == 1:
            log.debug("Connected to Freeswitch")
            con.events("plain", "all")
            e = con.api(command)
            r = con.recvEvent()
            data = e.getBody()
        try:
            list=re.split(",|\n",str(data))
	    log.debug(list)
        except:
            log.error("Connection to freeswitch lost...")
            return json.dumps(["Connection to freeswitch lost..."])
        if command == 'show registrations':
            makelist=list[10:-3]
            headers=list[0:10]
            dict_list=[dict(zip(headers,makelist[i:i+10])) for i in range(0,len(makelist),10)]
	    log.debug("JSON data:%s",dict_list)
        if command == 'show calls':
            makelist = list[39:-3]
            headers= list[0:39]
            dict_list=[dict(zip(headers,makelist[i:i+39])) for i in range(0,len(makelist),39)]
	    log.debug("JSON data:%s",dict_list)
        return json.dumps(dict_list, indent=2)


site = server.Site(WebServer())


application = service.Application('fsesl')
server = strports.service('tcp:8080', site)
server.setServiceParent(application)
