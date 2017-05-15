from __future__ import print_function

import json
from collections import defaultdict
import orgExtractor
import sys, argparse
import os
from os import listdir
from os.path import isfile, join
import operator


def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def dictify(data):
    #array_of_arrays_of_tuples
    oneDict = {}  
    
    for email in data:
        for pair in email:

            key = pair[0]
            value = pair[1]

            if key in oneDict:
                oneDict[key] += value
            else:
                oneDict[key] = value 

    return oneDict

def sumEnts(data):
    x = 0
    for pair in data:
        x += pair[1]

    return x

def mailsWithOrg(results, refOrgs):
    
    mailCount = 0
    for mail in results:
        maxMailScore = 0
        for ent in mail:
            if not maxMailScore:
                maxMailScore = ent[1]
            if ent[1] + 1 < maxMailScore:
                break
            if ent[0] in refOrgs:
                mailCount += 1
                break

    return mailCount
                
def mailsWithOrgLite(results, refOrgs):
    if not len(group_res):
        return 0

    mailCount = 0
    for mail in results:
        for ent in mail:
            if ent[0] in refOrgs: 
                mailCount += 1
                break

    return mailCount
                

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
                print("on line {0}".format(x))
            if not data["_FOUND"] or not data["_HAS_URL"]:
                continue
            domainRaw = data["url_visible"]
            try:
                domain = formatDomain(domainRaw)
            except UnicodeEncodeError:
                # ignore non unicode domains
                continue
            result[domain].add(data["title"].encode('utf8').lower())
            result[domain].add(data["_ORGANIZATION"].encode('utf8').lower())
            result[domain].add(data["title_alternative"].encode('utf8').lower())
        return result


        
    

PATH_FIRMYCZ = "/home/simonlet/git/nametag/organizations/firmyCzInfoJsons_fixed.txt"
DOM_PATH_TRAIN = "/mfs/replicated/datasets/domain_mail_eml_simon/train/"
#DOM_PATH_TEST = "/mfs/replicated/datasets/domain_mail_eml_simon/test/"

TMP_RESULT = "/tmp/bestDomains"

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("-k", "--keepServerUp", action="count", default=0,
                    help="Keeps nametag server alive")
parser.add_argument("-x", "--killAndExit", action="count", default=0,
                    help="Kills nametag server and exits the program!")
parser.add_argument("-d", "--debug", action="count", default=0,
                    help="Debug mode - write debug prints")
parser.add_argument("-g", "--debug2", action="count", default=0,
                    help="Debug mode - server writes debug prints")
parser.add_argument("-l","--lang", type=str, default=None, 
                    help="Use specified language - don't detect language")
parser.add_argument("-m","--model", type=str, default=None, 
                    help="Use specified model - don't detect language -"
                         "override '--lang'/'-l' option")
parser.add_argument("-w","--raw", action="count", default=0, 
                    help="Don't post process - just print raw tagged data")
parser.add_argument("-p","--absPath", action="count", default=0,
                    help="Use absolute path to domains")
parser.add_argument("-n","--numberOfLines", type=int, default=10, 
                    help="Test X lines for each domain")
parser.add_argument("-o","--numberOfDomains", type=int, default=9999, 
                    help="Test X first domains")
opt = parser.parse_args()

domains = os.listdir(DOM_PATH_TRAIN) 
domains.sort()

firmyCzData = getDomainTitleDict() 

noDomains = len(domains)
if opt.numberOfDomains < noDomains:
    noDomains = opt.numberOfDomains
noProcessed = 0

domain_results = []

for domain in domains:
    orgTitles = firmyCzData[domain]
    if not len(orgTitles):
        continue
    if opt.debug:
        print("Progress: {0} / {1}".format(noProcessed, noDomains))
        print("################### DOMAIN: <{0}> REF: <{1}>"
              .format(domain,orgTitles))

    domTrain = join(DOM_PATH_TRAIN, domain)
    #domTest = join(DOM_PATH_TEST, domain)

    trainEml = [f for f in listdir(domTrain) if isfile(join(domTrain, f))]
    noTrain = len(trainEml)

    if noTrain < 60:
        if opt.debug:
            print("no of emls < 60 - Ignoring! ({0})".format(noTrain))
        continue

    noProcessed += 1

    if noProcessed > opt.numberOfDomains:
        break

    emails = [f for f in listdir(domTrain) if isfile(join(domTrain, f))]
    emails.sort()

    results = []
    x = 0
    for mail in emails:

        mailPath = join(domTrain, mail)

        x += 1
        if x > opt.numberOfLines:
            break

        res = orgExtractor.extract([mailPath],
                               model=opt.model, lang=opt.lang,
                               killAndExit=opt.killAndExit,
                               keepServerUp=opt.keepServerUp,
                               raw=opt.raw, debug=opt.debug2)

        for r in res:
            #print("##################### TEXT:")
            #print(r["text"])
            #print("##################### TAGGED:")
            #print(r["tagged"])
            #print("##################### LANG, MODEL, RESULT:")
            #print(r["lang"])
            #print(r["model"])
            if opt.debug:
                print(r["result"])

            results.append(r["result"])

            
    #dictify results
    results_dict = dictify(results)
    #grouped_res = sorted(results_dict.items(), key=operator.itemgetter(1), reverse=True)

    #group_noEnts = sumEnts(grouped_res) 

    #if len(grouped_res):
    #    mainEntPercentage = grouped_res[0][1] * 1.0 / group_noEnts
    #else:
    #    mainEntPercentage = 0



    mailsMainOrgPercentage = mailsWithOrg(results, orgTitles) * 1.0 / len(results)

    #if mailsMainOrgPercentage == 0 and mainEntPercentage == 0:
    #    mean = 0
    #else:
    #    mean = ((2.0 * mailsMainOrgPercentage * mainEntPercentage ) 
    #                / (mainEntPercentage + mailsMainOrgPercentage))


    if opt.debug:
        #print(grouped_res)
        #print(mainEntPercentage)
        print(mailsMainOrgPercentage)

        #print(mean * 100)


    domain_results.append((domain, mailsMainOrgPercentage))
        

sorted_domain_res = sorted(domain_results, key=operator.itemgetter(1),
                           reverse=True)

print(sorted_domain_res)





