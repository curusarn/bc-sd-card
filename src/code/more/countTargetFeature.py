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


DATA_PATH = "/home/simonlet/git/nametag/feature_data/"
FIRMYCZ_CACHE_PATH = "organizations/firmyCzCache.pkl"

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("-k", "--keepServerUp", action="count", default=1,
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
parser.add_argument("-n","--numberOfFiles", type=int, default=999999, 
                    help="Test X first domains")
parser.add_argument("-v","--dataVersion", type=int, default=None, 
                    help="Data version to count feature data for",
                    required=True)
parser.add_argument("-s","--skipFiles", type=int, default=None, 
                    help="Skip X first files")
parser.add_argument("-r","--skipDirs", type=int, default=None, 
                    help="Skip X first directories")
parser.add_argument("-y", "--dryRun", action="count", default=None,
                    help="Don't write anything")
parser.add_argument("-z", "--noFirmyCz", action="count", default=0,
                    help="Don't load firmy.cz data - for speedy debugging")
parser.add_argument("-e", "--noOverwrite", action="count", default=0,
                    help="Do not overwrite")
opt = parser.parse_args()

files = []
version = "v" + str(opt.dataVersion)
path = join(DATA_PATH, version)
outPath = join(DATA_PATH, "targets", version)
if not os.path.exists(path):
    errprint("data path does not exist <{0}>".format(path))

# get entity -> domain mapping
def loadFirmyCzData():
    if os.path.isfile(FIRMYCZ_CACHE_PATH):
        if opt.debug:
            errprint("loading cached mappings <{0}>".format(FIRMYCZ_CACHE_PATH))
        with open(FIRMYCZ_CACHE_PATH, 'r') as f: 
            firmyCzData = pickle.load(f)
            if opt.debug:
                errprint("done.")
    else:
        if opt.debug:
            errprint("getting entity -> domain mapping")
        firmyCzData = getTitleDomainDict() 
        if opt.debug:
            errprint("done.")

        if not opt.dryRun:
            if opt.debug:
                errprint("saving cache for mappings <{0}>".format(FIRMYCZ_CACHE_PATH))
            with open(FIRMYCZ_CACHE_PATH, 'wb') as f: 
                pickle.dump(firmyCzData, f, pickle.HIGHEST_PROTOCOL)
                if opt.debug:
                    errprint("done.")
    return firmyCzData

if not opt.noFirmyCz:
    firmyCzData = loadFirmyCzData()
else:
    firmyCzData = defaultdict(set)
    
noFiles = 15122 #v1
if opt.numberOfFiles < noFiles:
    noFiles = opt.numberOfFiles
        
noProcessed = 0
for x,dirName in enumerate(sorted(os.listdir(path))):
    if opt.skipDirs and opt.skipDirs > x:
        errprint("skipping directory <{0}>".format(dirName))
        continue
    for name in os.listdir(join(path,dirName)):
        f = join(dirName,name)
        if not isfile(join(path, f)):
            continue

        noProcessed += 1
        if opt.skipFiles and noProcessed < opt.skipFiles:
            continue

        if opt.debug:
            print("Progress: {0} / {1} (don't trust me, I'm off)"
                  .format(noProcessed, noFiles))

        if noProcessed > opt.numberOfFiles:
            break


        filePath = join(path, f)
        outFilePath = join(outPath, f)
        
        if opt.noOverwrite and os.path.exists(outFilePath):
            continue

        if opt.debug:
            print(filePath)

        with open(filePath,'r') as json_file:    
            data = json.load(json_file)
            emlPath = data["email_path"]

        res = orgExtractor.extract([emlPath],
                               model=opt.model, lang=opt.lang,
                               killAndExit=opt.killAndExit,
                               keepServerUp=opt.keepServerUp,
                               raw=opt.raw, debug=opt.debug2)
        nerResults = [] 
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
            nerResults.append(r["result"])
        
        if not len(res):
            continue
        result = countTargetPercentages(nerResults[0], firmyCzData)

        if opt.debug:
            print(result)
 
        if not opt.dryRun:
            outParent = os.path.dirname(outFilePath)
            if not os.path.exists(outParent):
                os.makedirs(outParent)
            print(outFilePath) 
            with open(outFilePath, 'w') as out_file:
                json.dump(result, out_file)

