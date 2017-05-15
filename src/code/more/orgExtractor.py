from __future__ import print_function
# eml2text 
import mime, html5, sys
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


def dbgPrint(out, debug):
    if debug: 
        print(out)


def printNonEmptyLines(text):
    for line in text.split('\n'):
        if line.lstrip():
            print(line)


def stripEmptyLines(text):
    newText = ""
    for line in text.split('\n'):
        if line.lstrip():
            newText += line + "\n"
    return newText


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
    return "cnec2-phishableOrgTitles3_all"


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
    

def extract(emails, 
            model=None, lang=None,
            killAndExit=False, keepServerUp=False,
            raw=False, debug=False):

    if killAndExit:
        killServerAndExit()

    server = getServer(keepServerUp, model)

    results = []
    for eml in emails:

        try:
            text = stripEmptyLines(parseEml(eml))
            dbgPrint("##################### TEXT:", debug)
            dbgPrint(text, debug)

            if not lang:
                # guess language when unspecified
                try:
                    lang = guessLanguage(text)
                except Exception:
                    lang = "cs"

            if not model:
                # detect model when unspecified
                model = detectModel(lang)

            dbgPrint("##################### LANG:", debug)
            dbgPrint(lang, debug)

            dbgPrint("##################### MODEL:", debug)
            dbgPrint(model, debug)
            
            tagged = server.tagText(text, model).encode('utf-8')
            dbgPrint("##################### TAGGED:", debug)
            dbgPrint(tagged, debug)

            if raw:
                print("#### TEXT:")
                print(text)
                #printNonEmptyLines(text)
                print("#### OUTPUT:")
                print(tagged)                

            entities = preformatTaggedData(tagged) 
            dbgPrint("##################### FORMATED:", debug)
            dbgPrint(entities, debug)

            wantedEnt = extractEnt(entities)
            dbgPrint("##################### WANTED ENTITIES:", debug)
            dbgPrint(wantedEnt, debug)

            result = sorted(wantedEnt.items(), key=lambda item : item[1],
                            reverse=True)
            dbgPrint("##################### WANTED ENTITIES - SORTED:", debug)
            dbgPrint(result, debug)

            #dbgPrint("##################### OUTPUT:")
            ## print metadata
            #print(lang)
            #print(model)
            #
            #print("#DATA")
            ## print nice result  
            #i=0
            #for r in result:
            #    i += 1
            #    print(r[0].encode('utf-8'))

            data = {
                    "eml": eml,
                    "text": text,
                    "lang": lang,
                    "model": model,
                    "tagged": tagged,
                    "entities": entities,
                    "wantedEnt": wantedEnt,
                    "result": result
                    }

            results.append(data)

        except Exception as e:
            print(e)
            pass

    return results

