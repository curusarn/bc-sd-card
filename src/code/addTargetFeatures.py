import json
import sys
import os
import argparse
import pprint


def formatDomain(string):
    if not len(string):
        return string
    buff = "" 
    for i,char in enumerate(string):
        buff += char
        if i < 5:
            continue
        if buff[-4:] == "www.":
            a = string[i+1:]
            b = string[i+1:].split('/')[0]
            return b 
    for i,char in enumerate(string):
        buff += char
        if i < 5:
            continue
        if buff[-3:] == "://":
            a = string[i+1:]
            b = string[i+1:].split('/')[0]
            return b
    print("domain formating failed for <{0}>".format(string))


def getFeatureMode(opt):
    m = "_"
    if opt.boolFeature:
        m += "b"
    if opt.linkMismatchFeatureB:
        m += "l"
    if opt.linkMismatchFeatureA:
        m += "L"
    if opt.top1Feature:
        m += "t"
    if opt.top5Feature:
        m += "T"
    if opt.removeOriginalFeatures:
        m += "x"
    return m


def boolFeature(targetData):
    if len(targetData["targets"]) != 0:
        return True
    return False


TARGETS_DICT = {}
NEXT_TARGET_ID = 0
def topNFeature(targetData, TARGETS_DICT, NEXT_TARGET_ID, n):
    feature = {}
    for x,pair in enumerate(targetData["targets"][:n]):
        target = pair[0]
        if target not in TARGETS_DICT:
            TARGETS_DICT[target] = NEXT_TARGET_ID
            NEXT_TARGET_ID += 1
        feature[str(n)+"_top_domains_id_"+str(x)] = TARGETS_DICT[target]
        feature[str(n)+"_top_domains_percent_"+str(x)] = pair[1]
    return feature

def linkMismatchFeatureA(targetData, links, HIST_HREF, HIST_SRC):
    if not len(links):
        # no links -> no bad links
        return 0
    targets = []
    for pair in targetData["targets"]:
        if pair[1] < 0.4:
            break
        target = pair[0]
        if target in HIST_HREF:
            targets.append(target)

    if not len(targets):
        # no target -> no feature
        return -1
    for link in links:
        if not len(link):
            continue
        linkFeature = 1
        for target in targets:
            hrefs = HIST_HREF[target]
            #srcs = HIST_SRC[target]
            lookupLen = len(hrefs)
            if lookupLen > 10:
                lookupLen = int(lookupLen/2)
            if formatDomain(link) in hrefs[:lookupLen]:
                linkFeature = 0
                break
        if linkFeature:
            # link does not match any domain 
            return 1
    return 0
    

def linkMismatchFeatureB(targetData, links, HIST_HREF, HIST_SRC):
    if not len(links):
        # no links -> no bad links
        return 0
    targets = []
    for pair in targetData["targets"]:
        if pair[1] < 0.4:
            break
        target = pair[0]
        if target in HIST_HREF:
            targets.append(target)

    if not len(targets):
        # no target -> no feature
        return -1
    for link in links:
        if not len(link):
            continue
        for target in targets:
            hrefs = HIST_HREF[target]
            #srcs = HIST_SRC[target]
            lookupLen = len(hrefs)
            if lookupLen > 10:
                lookupLen = int(lookupLen/2)
            if formatDomain(link) in hrefs[:lookupLen]:
                return 0
    return 1
    



SRC_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(SRC_PATH,"../../data/feature_data")

HIST_PATH = "/home/simonlet/git/nametag/historical_data_phishable"
HIST_HREF = json.load(open(os.path.join(HIST_PATH,"sorted_href.json"))) 
HIST_SRC = json.load(open(os.path.join(HIST_PATH,"sorted_src.json"))) 

# argument parsing
parser = argparse.ArgumentParser()
# required options
parser.add_argument("-v","--dataVersion", type=int, default=None, 
                    help="Data version to count feature data for. (eg. 1)",
                    required=True)
# features
parser.add_argument("-b", "--boolFeature", action="count", default=0,
                    help="Add bool feature")
parser.add_argument("-l", "--linkMismatchFeatureB", action="count", default=0,
                    help="Add benevolent link mismatch feature")
parser.add_argument("-L", "--linkMismatchFeatureA", action="count", default=0,
                    help="Add agressive link mismatch feature")
parser.add_argument("-t", "--top1Feature", action="count", default=0,
                    help="Add top 1 target feature")
parser.add_argument("-T", "--top5Feature", action="count", default=0,
                    help="Add top 5 target feature")
parser.add_argument("-x", "--removeOriginalFeatures", action="count", default=0,
                    help="Remove original features")
parser.add_argument("-d", "--debug", action="count", default=0,
                    help="Debug mode - write debug prints, "
                         "'-dd' - write more debug prints.")
# debugging/advanced options
parser.add_argument("-n","--numberOfFiles", type=int, default=999999, 
                    help="Test X first domains - for debugging.")
parser.add_argument("-s","--skipFiles", type=int, default=None, 
                    help="Skip X first files - "
                         "can be used to 'resume' previous run")
parser.add_argument("-y", "--dryRun", action="count", default=None,
                    help="Don't write anything")
parser.add_argument("-e", "--noOverwrite", action="count", default=0,
                    help="Do not overwrite")

opt = parser.parse_args()

version = "v" + str(opt.dataVersion)
featureMode = getFeatureMode(opt)
if featureMode == "_":
    print("Choose at least one feature! (eg. '-b', '-t', '-blLtTx', ...)")
    sys.exit(3)

path = os.path.join(DATA_PATH, version)
targetPath = os.path.join(DATA_PATH, "targets", version)
outPath = os.path.join(DATA_PATH, version + featureMode)
if not os.path.exists(path):
    print("Data path does not exist <{0}>".format(path))
if not os.path.exists(targetPath):
    print("Target data path does not exist <{0}>".format(targetPath))
if not os.path.exists(outPath):
    os.makedirs(outPath)

noProcessed = 0
noFiles = opt.numberOfFiles
if opt.skipFiles:
    noFiles += opt.skipFiles
for x,dirName in enumerate(sorted(os.listdir(targetPath))):
    for name in os.listdir(os.path.join(targetPath,dirName)):
        f = os.path.join(dirName,name)
        if not os.path.isfile(os.path.join(path, f)):
            continue

        noProcessed += 1
        if opt.skipFiles and noProcessed < opt.skipFiles:
            continue

        if noProcessed > noFiles:
            break

        if opt.debug:
            print("Progress: {0} / cca 15000"
                      .format(noProcessed))

        filePath = os.path.join(path, f)
        targetFilePath = os.path.join(targetPath, f)
        outFilePath = os.path.join(outPath, f)
        
        if opt.noOverwrite and os.path.exists(outFilePath):
            if opt.debug:
                print("Skipping - output file already exists <{0}>"
                          .format(outFilePath))
            continue

        # read data
        with open(filePath,'r') as json_file:    
            data = json.load(json_file)
        
        # read target data
        with open(targetFilePath,'r') as target_file:    
            targetData = json.load(target_file)

        # remove all original features 
        if opt.removeOriginalFeatures:
            data["phishing"].clear()

        # add bool feature
        if opt.boolFeature: 
            data["phishing"]["ner_domain_detected"] = boolFeature(targetData)

        # add top 1 target feature
        if opt.top1Feature: 
            data["phishing"].update(topNFeature(targetData,
                                                TARGETS_DICT,
                                                NEXT_TARGET_ID,
                                                1))
        # add top 5 target feature
        if opt.top5Feature: 
            data["phishing"].update(topNFeature(targetData,
                                                TARGETS_DICT,
                                                NEXT_TARGET_ID,
                                                5))
        if opt.linkMismatchFeatureA:
            data["phishing"]["argessive_link_mismatch"] = linkMismatchFeatureA(
                                                      targetData,
                                                      data["extractedHrefUrls"],
                                                      HIST_HREF, HIST_SRC)

        if opt.linkMismatchFeatureB:
            data["phishing"]["benevolent_link_mismatch"] = linkMismatchFeatureB(
                                                      targetData,
                                                      data["extractedHrefUrls"],
                                                      HIST_HREF, HIST_SRC)
        if opt.debug > 1: 
            print("Feature data:") 
            pprint.pprint(data["phishing"])

        if not opt.dryRun:
            outParent = os.path.dirname(outFilePath)
            if not os.path.exists(outParent):
                os.makedirs(outParent)
            print("Writing output to:") 
            print(outFilePath) 
            with open(outFilePath, 'w') as out_file:
                json.dump(data, out_file, indent=4)

