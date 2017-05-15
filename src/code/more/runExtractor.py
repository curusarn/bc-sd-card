from __future__ import print_function

import sys, argparse
import orgExtractor


def getTs():
    return int(round(time.time() * 1000))


def printTs():
    print("ts: {0}".format(getTs()))


def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def allprint(*args, **kwargs):
    errprint(*args, **kwargs)
    print(*args, **kwargs)


def printNonEmptyLines(text):
    for line in text.split('\n'):
        if line.lstrip():
            print(line)


def dbgPrint(str, force = False):
    if options.debug or force: 
        print(str)


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
parser.add_argument("emails",
                    type=str,
                    nargs="+",
                    help="Emails that should be tagged.")


opt = parser.parse_args()

for mail in opt.emails:

    res = orgExtractor.extract([mail],
                           model=opt.model, lang=opt.lang,
                           killAndExit=opt.killAndExit,
                           keepServerUp=opt.keepServerUp,
                           raw=opt.raw, debug=opt.debug)

    for r in res:
        print("##################### TEXT:")
        print(r["text"])
        print("##################### TAGGED:")
        print(r["tagged"])
        print("##################### LANG, MODEL, RESULT:")
        print(r["lang"])
        print(r["model"])
        print(r["result"])










