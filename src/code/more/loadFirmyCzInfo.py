
import json

PATH_OUT = "/home/simonlet/git/nametag/organizations/firmyCzInfoJsons_fixed.txt"

with open(PATH_OUT, "r") as jsons:
    for line in jsons:
        data = json.loads(line)
        print(data)

    

