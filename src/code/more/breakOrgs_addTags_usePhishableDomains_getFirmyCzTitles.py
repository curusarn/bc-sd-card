from __future__ import print_function

from collections import defaultdict
import sys
import json
import pickle
import os


PATH_FIRMYCZ = "/home/simonlet/git/nametag/organizations/firmyCzInfoJsons_fixed.txt"
PHISHABLE_DOM_PATH = "/home/simonlet/git/nametag/domains/phishable.pkl"
DOM_PATH_TRAIN = "/mfs/replicated/datasets/domain_mail_eml_simon/train/"
 

def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def formatDomain(string):
    buff = "" 
    for i,char in enumerate(string):
        buff += char
        if i < 5:
            continue
        if buff[-4:] == "www.":
            return string[i+1:].decode('utf8')
    for i,char in enumerate(string):
        buff += char
        if i < 5:
            continue
        if buff[-3:] == "://":
            return string[i+1:].decode('utf8')
    errprint("domain formating failed for <{0}>".format(string))

         

def getDomainTitleDict():
    with open(PATH_FIRMYCZ, "r") as jsons:
        result = defaultdict(set)
        for x,line in enumerate(jsons):
            try:
                data = json.loads(line)
            except ValueError as e:
                print(e)
                print("line:")
                print(line)
                print("on line {0}".format(x))
            if not data["_FOUND"] or not data["_HAS_URL"]:
                continue
            domainRaw = data["url_visible"]
            try:
                domain = formatDomain(domainRaw)
            except UnicodeEncodeError:
                # ignore non unicode domains
                continue
            result[domain].add(data["title"].encode('utf8'))
        return result

def getCommonNames():
    with open(PATH_OUT, "r") as jsons:
        result = []
        for line in jsons:
            data = json.loads(line)
            if not data["_FOUND"] or not data["_HAS_URL"]:
                continue
            result.append(data["title"].encode('utf8'))
        return result

domains = os.listdir(DOM_PATH_TRAIN) 
firmyCzData = getDomainTitleDict() 


for domain in domains:
    #line = line.strip(' \t\n\r')
    #shift = 0 # shifts B-ORG tag if first word is empty
    if not domain in firmyCzData:
        #errprint("No title for <{0}> - NOT FOUND".format(domain))
        continue
    lines = firmyCzData[domain]
    for line in lines:
        #errprint("{0} -> {1}".format(domain, line))
        for i,word in enumerate(line.split(' ')):
            if word.isspace() or len(word) == 0:
                # ignore empty words
                #shift += 1
                continue
            if i == 0:
                tag = "B-if"
            else:
                tag = "I-if"

            print(word + '\t' + tag)

        print("")
        


