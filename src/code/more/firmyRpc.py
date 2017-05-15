from __future__ import print_function

from subprocess import call
import fastrpc
import sys
import argparse
import time
import json
import random

parser = argparse.ArgumentParser()
parser.add_argument("-s","--startFrom", type=str, default=None, 
                    help="Skip orgs before X")
parser.add_argument("-w","--wait", type=int, default=5, 
                    help="Wait in seconds after fail (only in retry mode)")
#parser.add_argument("-r", "--retry", action="count", default=1,
#                    help="Retry mode - retry after fail")
opt = parser.parse_args()

PATH = "/home/simonlet/git/nametag/organizations/plain_woLikvidaci_stripEscapedApostropes_sorted_uniqed.txt"

PATH_OUT = "/home/simonlet/git/nametag/organizations/firmyCzInfoJsons.txt"


def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

#def networkSwitch():
#    call("",shell=True)

def getClient():
    for i in range(1,6):
        try:
            client = fastrpc.ServerProxy("http://www.firmy.cz/RPC2/",
                                         readTimeout=3000,
                                         writeTimeout=3000, connectTimeout=6000,
                                         useBinary=fastrpc.ON_SUPPORT_ON_KEEP_ALIVE)
            return client
        except Exception as e:
            errprint("connecting ... hold on tight {0}".format(e))
    sys.exit(4)


def getLastOrg(path):
    with open(path, "r") as jsons:
        lines = jsons.readlines()

        for x in range(1,len(lines)-1):
            errprint("getting last org ({0})".format(x))
            try:
                line = lines[len(lines)-x]
                data = json.loads(line)
            except Exception:
                continue

            return data["_ORGANIZATION"]

        return None

def getOrgInfo(org, keys):

    version = {"version":"1.0"}
    empty = {}
    stuff = {"clusterSize":0.30761718750000355,"zoom":8,"bbox":{"fromLongitude":15.863731003325285,"toLongitude":16.687705612700285,"fromLatitude":48.16163917279508,"toLatitude":51.66160664130034}}
    info = None

    try:
        #result = client.common.getUserInfo(version, "searchweb", "https://www.firmy.cz/?q=" + org)
        if not random.getrandbits(1):
            result = client.search.searchPremises(version, org, 0, 15, empty)
        else:
            result = client.search.searchPremises(version, org, 0, 500, stuff)
        #print "Status is '%d'" % result["status"]
        if result["status"] != 200:
            errprint("STATUS NOT 200 ({0}) for org <{1}>".format(result["status"],org))
            errprint(result)
            if result["status"] == 500:
                return {"_ORGANIZATION":org, "_FOUND":False, "_HAS_URL":False}
            #if result["status"] == 434:
            #    errprint("waiting <{0}> seconds +".format(3))
            #    time.sleep(3)
            return None

        info = {"_ORGANIZATION":org, "_FOUND":False, "_HAS_URL":False}
        entries = result["result"]["premises"]

        if len(entries):
            info["_FOUND"] = True

            for k,v in entries[0].items():
                if k in keys:
                    info[k] = v
            #    try:
            #        print("{0} -> {1}".format(k,v))
            #    except Exception:
            #        print(k)
            if info["url_visible"]:
                info["_HAS_URL"] = True
             
            #print result
            #print info

    except fastrpc.Fault as f:
        errprint(f)
    except fastrpc.ProtocolError as e:
        errprint(e)
    except fastrpc.Error as e:
        errprint(e)

    return info

wantedKeys = frozenset(["url_visible", "title", "title_alternative", "id", "subject_id", "title_addition", "title_use_alternative"])

client = getClient()
lastOrg = getLastOrg(PATH_OUT)
errprint("lastOrg: <{0}>".format(lastOrg.encode("utf8")))

iface1 = True
skip = False
if lastOrg:
    skip = True

with open(PATH, 'r') as plainOrgs:
    for x,line in enumerate(plainOrgs):
        org = line.strip("\n\t\r ")
        if x % 20 == 0:
            errprint("progress: {0} / XXX".format(x))
        if skip:
            if org == lastOrg.encode("utf8"):
               skip = False 
            continue

        info = None
        wait = 1
        while not info:
            if random.randint(0,100) == 1:
                errprint("microsleep")
                time.sleep(1)
            info = getOrgInfo(org, wantedKeys)
            if info:
                break
            errprint("waiting <{0}> seconds".format(wait))
            time.sleep(1)
            if wait < 4:
                wait += 1
            else:
                errprint("progress: {0} / XXX".format(x))
                errprint("EXITING")
                sys.exit(3)
                
        
        print(json.dumps(info))

        
#echo 'search.searchPremises({"version":"1.0"},"alza.cz",0,14,{"filter_all":"nyni-otevreno;eshop;prodejna;vydejni-misto;foto-provozovny","loadGeoms":true})' | xmlrpc-netcat http://www.firmy.cz/RPC2/  | jq .
