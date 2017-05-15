import mime, html5, sys, argparse
import os, subprocess

def parseMsg(msg):
    root = mime.tree.parse(open(msg).read())
    root.repair_mime_types()
    root.repair_charset()
    root.choose_text_candidates()

#    print(root.subject)
#    print(root.from)
    #TODO: add subject and from field (maybe twice)
    email = "" 
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


# parse args
parser = argparse.ArgumentParser()
parser.add_argument("messages",
                    type=str,
                    nargs="+",
                    help="Messages that should be converted.")
options = parser.parse_args()


for msg in options.messages:
    email = parseMsg(msg)
    print(email)
    #call.subprecess(""
    #break
