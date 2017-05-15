# -*- coding: utf-8 -*-
from __future__ import print_function

import json
from collections import defaultdict
import orgExtractor
import sys, argparse
import os
import pickle
from os import listdir
from os.path import isfile, join
import operator
import datetime
from targetDetectionCore import *


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
                
def normalize(entity):
    #print("O: " + entity)
    if not len(entity):
        return set()
    #print("E: " + entity)
    result = set([entity])
    replacePairs = [
            ("s. r. o.","s.r.o.","s . r . o .","s r . o ."),
            ("a. s.","a.s.","a . s ."),
            ("k. s.","k.s.","k . s ."),
            ("spol.","spol ."),
            (" ,",",",", ")
                   ]
    stripWords = ["s. r. o.","s.r.o.","s . r . o .","s r . o .",
                  "a. s.","a.s.","a . s .",
                  "k. s.","k.s.","k . s .",
                  "spol.","spol .",
                  "czech republic", "czech", "česká republika", "cz",
                  "praha",
                  "distribution", "services", "technologies",
                  "penzijní společnost",
                  "1.", "1 ."
                  ]
    stripChars = ",. -.?! "
    # use synonymes
    for synonymes in replacePairs:
        for word1 in synonymes:
            for word2 in synonymes:
                if word1 == word2:
                    continue
                #print("B: " + entity)
                tmpEnt = entity.replace(word1, word2)
                tmpEntStrip = tmpEnt.strip(stripChars)
                #print("t: " + tmpEnt)
                #print("A: " + entity)
                if tmpEnt != entity:
                    result.add(tmpEnt)
                if tmpEntStrip != entity:
                    result.add(tmpEntStrip)

    # double word remove
    for word1 in stripWords:
        for word2 in stripWords:
            if word1 == word2:
                continue
            #print("W: " + word)
            #print("B: " + entity)
            tmpEnt = entity.replace(word1, "")
            tmpEnt2 = entity.replace(word2, "")
            tmpEntStrip = tmpEnt.strip(stripChars)
            tmpEntStrip2 = tmpEnt2.strip(stripChars)
            #print("t: " + tmpEnt)
            #print("A: " + entity)
            if tmpEnt != entity:
                result.add(tmpEnt)
            if tmpEntStrip != entity:
                result.add(tmpEntStrip)
            if tmpEnt2 != entity:
                result.add(tmpEnt2)
            if tmpEntStrip2 != entity:
                result.add(tmpEntStrip2)

    return result



def countTargetMatched(nerResults, referenceDomain, firmyCzData):
    mailsMatch = 0
    results = []
    for mail in nerResults:
        domainCounts = defaultdict(int)
        totalCounts = 0
        # count entities for each domain
        for ent in mail:
            doms = None
            for normal in normalize(ent[0].decode('utf8').lower().encode('utf8')):
                if normal in firmyCzData:
                    doms = firmyCzData[normal]
                    break
            if doms == None:
                continue
            for dom in doms:
                domainCounts[dom] += ent[1]
                totalCounts += ent[1]

        sorted_domainCounts = sorted(domainCounts.items(),
                                     key=operator.itemgetter(1),
                                     reverse=True)
        print(referenceDomain + " ... REF!")
        print(sorted_domainCounts)
        
        mailResult = {"domains": [],
                      "refDomainRank": -1, "refDomainPercentage": 0.0} 
        rank = 0
        prevVal = 0
        for x,pair in enumerate(sorted_domainCounts):
            percentage = pair[1] * 1.0 / totalCounts

            if not prevVal:
                prevVal = percentage
            if percentage < prevVal:
                rank += 1
            
            mailResult["domains"].append((pair[0], percentage)) 
            if pair[0].decode('utf8') == referenceDomain:
                mailResult["refDomainOrder"] = x 
                mailResult["refDomainRank"] = rank 
                mailResult["refDomainPercentage"] = percentage
        results.append(mailResult)
        if mailResult["refDomainRank"] == 0:
            mailsMatch += 1

    return (mailsMatch, results)
            


def formatDomain(string):
    buff = "" 
    for i,char in enumerate(string):
        buff += char
        if i < 5:
            continue
        if buff[-4:] == "www.":
            a = string[i+1:]
            b = string[i+1:].split('/')[0]
            return a 
    for i,char in enumerate(string):
        buff += char
        if i < 5:
            continue
        if buff[-3:] == "://":
            a = string[i+1:]
            b = string[i+1:].split('/')[0]
            return a
    errprint("domain formating failed for <{0}>".format(string))


def getDomainTitleDict():
    with open(PATH_FIRMYCZ, "r") as jsons:
        result = defaultdict(set)
        for line in jsons:
            data = json.loads(line)
            if not data["_FOUND"] or not data["_HAS_URL"]:
                continue
            domainRaw = data["url_visible"]

            domain = formatDomain(domainRaw)
            for key in ("title","_ORGANIZATION","title_alternative"):
                #print("SRC: " + data[key].lower().encode('utf8'))
                for ent in normalize(data[key].lower().encode('utf8')):
                    ent = ent.lower()
                    #print("OUT: " + ent)
                    result[domain].add(ent)
            result[domain].add(domain)
        return result



def getTitleDomainDict():
    with open(PATH_FIRMYCZ, "r") as jsons:
        result = defaultdict(set) 
        for line in jsons:
            data = json.loads(line)
            if not data["_FOUND"] or not data["_HAS_URL"]:
                continue
            domainRaw = data["url_visible"]

            domain = formatDomain(domainRaw)
            result[domain].add(domain)
            for key in ("title","_ORGANIZATION","title_alternative"):
                for ent in normalize(data[key].lower().encode('utf8')):
                    result[ent].add(domain)
        return result


        
    

PATH_FIRMYCZ = "/home/simonlet/git/nametag/organizations/firmyCzInfoJsons_fixed.txt"
#DOM_PATH_TRAIN = "/mfs/replicated/datasets/domain_mail_eml_simon/train/"
DOM_PATH_TEST = "/mfs/replicated/datasets/domain_mail_eml_simon/test/"
FEATURED_DOMAINS = "/home/simonlet/git/nametag/domains/featured.txt"

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

domains = os.listdir(DOM_PATH_TEST) 
domains.sort()


firmyCzData = getTitleDomainDict() 
firmyCzDataSupport = getDomainTitleDict() 

featured = [] 
featuredSet = set()
with open(FEATURED_DOMAINS, 'r') as f:
    for line in f:
        d = line.strip('\n')
        if d in featuredSet:
            continue
        featured.append(d)
        featuredSet.add(d)
    
noDomains = len(featured)
if opt.numberOfDomains < noDomains:
    noDomains = opt.numberOfDomains
noProcessed = 0

domain_results = []
all_results = []
domains_used = []
        
for domain in featured:
    if domain not in featured:
        continue
    orgTitles = firmyCzDataSupport[domain]
    if not len(orgTitles):
        continue
    domains_used.append(domain) 
    if opt.debug:
        print("Progress: {0} / {1}".format(noProcessed, noDomains))
        print("################### DOMAIN: <{0}> REF_ENTITIES:".format(domain))
        for org in orgTitles:
            print(org)
        print("################### ENDREF")

    #domTrain = join(DOM_PATH_TRAIN, domain)
    domTest = join(DOM_PATH_TEST, domain)

    testEmls = [f for f in listdir(domTest) if isfile(join(domTest, f))]
    noTest = len(testEmls)
    testEmls.sort()

    noProcessed += 1

    if noProcessed > opt.numberOfDomains:
        break

    #emails = [f for f in listdir(domTest) if isfile(join(domTest, f))]

    results = []
    x = 0
    for mail in testEmls:

        mailPath = join(domTest, mail)

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

    results_dict = dictify(results)

    if len(results):  
        countedData = countTargetMatched(results, domain, firmyCzData)
        targetMatchPercentage = countedData[0] * 1.0 / len(results)
        if opt.debug:
            print(countedData[1])
    else:
        targetMatchPercentage = None

    if opt.debug:
        print(targetMatchPercentage)


    domain_results.append((domain, targetMatchPercentage))
    all_results.append({"countedData":countedData, "ntg":results,
                        "ntgOneDict":results_dict, "domain": domain})
        

sorted_domain_res = sorted(domain_results, key=operator.itemgetter(1),
                           reverse=True)

print(sorted_domain_res)

dt = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
PICKLE_PATH ="/home/simonlet/git/nametag/pickle_res/"+dt

os.mkdir(PICKLE_PATH)

PICKLE_RESULT_FINAL = PICKLE_PATH+"/result_final.pkl"
PICKLE_RESULTS_ALL = PICKLE_PATH+"/results_all.pkl"
PICKLE_DOMAINS = PICKLE_PATH+"/domains.pkl"


with open(PICKLE_RESULT_FINAL, 'wb') as f:
    pickle.dump(sorted_domain_res, f, pickle.HIGHEST_PROTOCOL)

with open(PICKLE_RESULTS_ALL, 'wb') as f:
    pickle.dump(all_results, f, pickle.HIGHEST_PROTOCOL)

with open(PICKLE_DOMAINS, 'wb') as f:
    pickle.dump(domains_used, f, pickle.HIGHEST_PROTOCOL)




