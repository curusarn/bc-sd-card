# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import sys, argparse
import os
import pprint


def getFeatureMode(opt):
    m = "_"
    if opt.removeOriginalFeatures:
        m += "x"
    if opt.boolFeature:
        m += "b"
    if opt.targetFeature:
        m += "T"
    return m

def isDomainDetected(targetData):
    if len(targetData["targets"]) != 0:
        return True
    return False

TARGETS_DICT = {}
NEXT_TARGET_ID = 0

def generateTargetFeature(targetData, TARGETS_DICT, NEXT_TARGET_ID):
    feature = {}
    for x,pair in enumerate(targetData["targets"][:5]):
        target = pair[0]
        if target not in TARGETS_DICT:
            TARGETS_DICT[target] = NEXT_TARGET_ID
            NEXT_TARGET_ID += 1
        feature["5_top_domains_id_"+str(x)] = TARGETS_DICT[target]
        feature["5_top_domains_percent_"+str(x)] = pair[1]
    return feature

SRC_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(SRC_PATH,"../../data/feature_data")

# argument parsing
parser = argparse.ArgumentParser()
# required options
parser.add_argument("-v","--dataVersion", type=int, default=None, 
                    help="Data version to count feature data for. (eg. 1)",
                    required=True)
# features
parser.add_argument("-b", "--boolFeature", action="count", default=0,
                    help="Add bool feature")
parser.add_argument("-t", "--targetFeature", action="count", default=0,
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
    print("Choose at least one feature! (eg. '-b', '-t', '-bt', ...)")
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
            data["phishing"]["ner_domain_detected"] = isDomainDetected(
                                                                targetData)

        # add top 5 target feature
        if opt.targetFeature: 
            data["phishing"].update(generateTargetFeature(targetData,
                                                          TARGETS_DICT,
                                                          NEXT_TARGET_ID))
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

