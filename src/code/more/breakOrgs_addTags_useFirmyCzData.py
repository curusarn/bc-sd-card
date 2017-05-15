
import json


PATH_OUT = "/home/simonlet/git/nametag/organizations/firmyCzInfoJsons_fixed.txt"

def getFirmyCzDict(key = None):
    with open(PATH_OUT, "r") as jsons:
        result = {}
        for line in jsons:
            data = json.loads(line)
            if not data["_FOUND"] or not data["_HAS_URL"]:
                continue
            if not key:
                result[data["_ORGANIZATION"]] = data
            else:
                result[data["_ORGANIZATION"]] = data[key]
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

firmyCzData = getCommonNames() 


for line in firmyCzData:
    #line = line.strip(' \t\n\r')
    #shift = 0 # shifts B-ORG tag if first word is empty
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
        


