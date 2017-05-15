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


PATH_FIRMYCZ_XXX42 = "organizations/firmyCzInfoJsons_fixed.txt"

def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

                
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
            (" ,",",",", "),
            ("inc","inc.","inc .")
                   ]
    stripWords = ["s. r. o.","s.r.o.","s . r . o .","s r . o .",
                  "a. s.","a.s.","a . s .",
                  "k. s.","k.s.","k . s .",
                  "spol.","spol .",
                  "czech republic", "czech", "česká republika", "cz",
                  "usa", "bank", "corporation", "online",
                  "inc", "inc.", "inc .",
                  "N.A.", "N. A.", "N . A .", 
                  "praha",
                  "distribution", "services", "technologies",
                  "penzijní společnost",
                  "1.", "1 ."
                  ]
    stripChars = ",. -.?!& "
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



def countTargetPercentages(nerResult, firmyCzData):
    domainCounts = defaultdict(int)
    totalCounts = 0
    # count entities for each domain
    for ent in nerResult:
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

    #errprint(sorted_domainCounts)

    mailResult = {"targets": []} 
    prevVal = 0
    for pair in sorted_domainCounts:
        percentage = pair[1] * 1.0 / totalCounts
        mailResult["targets"].append((pair[0], percentage)) 

    return mailResult
            


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
    with open(PATH_FIRMYCZ_XXX42, "r") as jsons:
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
    with open(PATH_FIRMYCZ_XXX42, "r") as jsons:
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



