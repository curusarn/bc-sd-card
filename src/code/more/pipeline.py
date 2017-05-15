from __future__ import print_function
# eml2text 
import mime, html5, sys, argparse
import os, subprocess

import nametagServer as ns

from guess_language import guessLanguage

import time

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

def killServerAndExit():
    # kill server option
    allprint("NOTICE: killing nametag server ...")
    ns.killServer(False)
    allprint("NOTICE: exiting")
    sys.exit(42)


def getServer(keepServerUp, model):

    # run server
    server = ns.nametagServer(keepServerUp)

    # check if specified model is available
    if model and not server.hasModel(model):
        # restart server to refresh models
        errprint("WARN: specified model does not exist - restarting server")
        errprint("INFO: killing nametag server ...")
        ns.killServer(False)
        errprint("INFO: done")
        errprint("INFO: launching nametag server ...")
        server = ns.nametagServer(keepServerUp)
        errprint("INFO: done")
        if not server.hasModel(model):
            allprint("ERR: specified model does not exist")
            sys.exit(2)

        errprint("INFO: specified model loaded after restart")

    return server




def parseEml(msg):
    root = mime.tree.parse(open(msg).read())
    root.repair_mime_types()
    root.repair_charset()
    root.choose_text_candidates()

    email = "" 
    for part in root.headers:
        if part.name.lower() == "subject":
            email += part.unpack().value + "\n"
        elif part.name.lower() == "from":
            for x in part.unpack():
                email += x.fullname + " " + x.email + "\n"
                email += " ".join(x.email.split("@")) + "\n"

    # parse parts
    for part in root.texts:
        if part.content_type.type == "text/plain":
            email += part.children[0].text + "\n"
        elif part.content_type.type == "text/html":
            #parser = html5.dom.Parser()
            #doc = parser.parseFromString(part.children[0].text, "text/html")
            #email += doc.body.innerText
            #email += " \n "

            #doc.body.innerHTML = "<a>"
            #aa = doc.getElementsByClassName("aaa")
            #print(aa)
            #print(doc.body.innerHTML)

            omit = False
            for token in html5.Tokenizer(part.children[0].text):
                if token.istag():
                    if token.name().lower() == "head":
                        omit = not token.closing()
                elif token.istext() and not omit:
                    email += str(token.expand()) + "\n"

    return email


def detectModel(lang):
    if lang == "en":
        return "conll"
    #if lang != "cs":
    #    print("unknown language: {0}".format(lang))
    return "cnec2"


def preformatTaggedData(tagged):
    entities = [] 
    for line in tagged.splitlines():
        cols = line.split('\t')
        entities.append((cols[2], cols[1]))
         
    return entities


def extractEnt(entities):
    # lower case word count
    lcWordCount = {}
    wanted = {} 

    wantedTags = ("ORG", "if")
    
    for ent in entities:
       lcWord = ent[0].lower()  
       if lcWord in lcWordCount:
           lcWordCount[lcWord] += 1
       else:
           lcWordCount[lcWord] = 1

       if ent[1] in wantedTags:
           if lcWord in wanted:
               wanted[lcWord] += 1
           else:
               wanted[lcWord] = 1

    for word in wanted:
        wanted[word] = lcWordCount[word]

    return wanted
    

def dbgPrint(str, force = False):
    if options.debug or force: 
        print(str)


def runPipeline(opt):
    if opt["killAndExit"]:
        killServerAndExit()

    server = getServer(opt["keepServerUp"], opt["model"])

    for eml in opt["emails"]:

        try:
            text = parseEml(eml)
            dbgPrint("##################### TEXT:")
            dbgPrint(text)

            if opt["lang"]:
                # specified language overrides language detection
                lang = opt["lang"]
            else:
                lang = guessLanguage(text)

            if opt["model"]:
                # specified model overrides language & model detection
                model = opt["model"]
            else:
                model = detectModel(lang)

            dbgPrint("##################### LANG:")
            dbgPrint(lang)

            dbgPrint("##################### MODEL:")
            dbgPrint(model)
            
            tagged = server.tagText(text, model)
            dbgPrint("##################### TAGGED:")
            dbgPrint(tagged.encode('utf-8'))

            if opt["raw"]:
                print("#### TEXT:")
                printNonEmptyLines(text)
                print("#### OUTPUT:")
                print(tagged.encode('utf-8'))                

            entities = preformatTaggedData(tagged) 
            dbgPrint("##################### FORMATED:")
            dbgPrint(entities)

            wantedEnt = extractEnt(entities)
            dbgPrint("##################### WANTED ENTITIES:")
            dbgPrint(wantedEnt)

            result = sorted(wantedEnt.items(), key=lambda item : item[1],
                            reverse=True)
            dbgPrint("##################### WANTED ENTITIES - SORTED:")
            dbgPrint(result)

            dbgPrint("##################### OUTPUT:")
            # print metadata
            print(lang)
            print(model)
            
            print("#DATA")
            # print nice result  
            i=0
            for r in result:
                i += 1
                print(r[0].encode('utf-8'))

        except Exception as e:
            pass
        

def getDefalutPipelineOpts():
    return {
            "keepServerUp": 0,
            "killAndExit": 0,
            "raw": 0,
            "debug": 0,
            "lang": None,
            "model": None,
            "emails": None
            }

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

options = parser.parse_args()
opt = vars(options)

runPipeline(opt)










