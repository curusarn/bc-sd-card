from __future__ import print_function

import orgExtractor
import sys, argparse
from os import listdir
from os.path import isfile, join

import pickle

DOM_PATH = "/mfs/replicated/datasets/domain_mail_eml/"
PHISHABLE_DOM_PATH = "/home/simonlet/git/nametag/domains/phishable.pkl"

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("-k", "--keepServerUp", action="count", default=0,
                    help="Keeps nametag server alive")
parser.add_argument("-x", "--killAndExit", action="count", default=0,
                    help="Kills nametag server and exits the program!")
parser.add_argument("-d", "--debug", action="count", default=0,
                    help="Debug mode - write debug prints")
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
parser.add_argument("domains",
                    type=str,
                    nargs="+",
                    help="Domain directories")
opt = parser.parse_args()

print("pickle loading phishable domains ...")
phishable = pickle.load(open(PHISHABLE_DOM_PATH)) 
print("done.")

print("pickle loading phishable domains ...")

if opt.domains[0] == "ALL":
    print("listing all domains dirs ...")
    domains = listdir(DOM_PATH) 
    print("done.")
    print("sorting domains ...")
    domains.sort()
    print("done.")
else:
    domains = opt.domains

notPhishableCount = 0

for domain in domains:
     
    if opt.absPath:
        domainPath = domain
    else:
        domainPath = DOM_PATH + domain

    emails = [f for f in listdir(domainPath) if isfile(join(domainPath, f))]
    emails.sort()

    if domain not in phishable:
        notPhishableCount += 1
        continue

    print("################### DOMAIN: <{0}>".format(domain))

    x = 0
    for mail in emails:

        mailPath = domainPath + "/" + mail

        x += 1
        if x > opt.numberOfLines:
            break

        res = orgExtractor.extract([mailPath],
                               model=opt.model, lang=opt.lang,
                               killAndExit=opt.killAndExit,
                               keepServerUp=opt.keepServerUp,
                               raw=opt.raw, debug=opt.debug)

        for r in res:
            #print("##################### TEXT:")
            #print(r["text"])
            #print("##################### TAGGED:")
            #print(r["tagged"])
            #print("##################### LANG, MODEL, RESULT:")
            #print(r["lang"])
            #print(r["model"])
            print(r["result"])



print("not phishable: {0}".format(notPhishableCount))
