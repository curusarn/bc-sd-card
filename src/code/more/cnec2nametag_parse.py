
import sys
import os.path

def isContainerTag(tag):
    # container tags are one uppercase letter
    if len(tag) == 1 and tag.isupper():
        return True
    return False

def parseLine(ln):
    result = []
    # get rid of the \n, split into words
    word = ""
    taggedWord = ""
    arrayTaggedWord = []
    tag = None
    containerTag = None
    words = ln[:-1].split(' ')
    wordsLen = len(words)
    i = 0
    inContainer = False # ignore containers they are supposedly hardcoded
    ltCount = 0 # how many times is tag nested
    for word in words:
        #print("w:{0}, tag:{1}|{4}, tagW:{2}, ltC:{3}".format(word, tag,
        #                                                 taggedWord, ltCount, containerTag))

        # skip empty words
        if not len(word):
            continue

        # basic no ent words
        if not ltCount and not '<' in word:
            if word[-1] == '>':
                print("ERROR: '>' outside of '<>' - word:{0}".format(word))
            result.append((word, '_'))
            # no need to reset things
            continue

        if '<' in word and '>' in word:
            # special case for fucked up cases such as "9>-<th"
            # no support for ignoring containers in special cases - I'm not a wizard
            tmp = word.split('>')
            tmp2 = tmp[1].split('<') 
            
            if len(tmp) != 2 or len(tmp2) != 2:
                # more than one '<' or '>'
                print("ERROR: special case failed - word:{0}".format(word))
            
            # append rest of first tag
            #OLD
            #result.append((taggedWord[1:] + tmp[0], 'B-' + tag))

            ltCount -= 1
            arrayTaggedWord.append(tmp[0])

            prefix = 'B-' 
            for tWord in arrayTaggedWord:
                result.append((tWord, prefix + tag))
                prefix = 'I-' 
            
            taggedWord = ""
            arrayTaggedWord = []
            tag = None
            containerTag = None

            # append middle part if present
            if len(tmp2[0]):
                result.append((tmp2[0], '_'))

            # handle start of new tag
            ltCount += 1
            tag = tmp2[1]

            continue

        
        if '<' in word:
            tmp = word.split('<')

            if tag is None:
                if not isContainerTag(tmp[1]):
                    tag = tmp[1] # tag after first '<'
                else:
                    if len(tmp) > 2:
                        tag = tmp[2] # first tag in container
                    inContainer = True
                    containerTag = tmp[1]

            ltCount += len(tmp) - 1
            # special case for fucked up cases such as "(<th"
            if len(tmp[0]):
                result.append((tmp[0], '_'))

            continue

        if '>' in word:
            tmp = word.split('>')
            #lenTmp = len(tmp)
            word = tmp[0]
            ltCount -= len(tmp) - 1
                
            
        taggedWord += ' ' + word
        arrayTaggedWord.append(word)
 
        # special condition because containers
        if not inContainer or ltCount != 1:
            # basic old condition
            if ltCount:
                continue

        # OLD WAY:
        #result.append((taggedWord[1:], 'B-' + tag))

        # NEW WAY:
        prefix = 'B-' # first word is B-X all other are I-X
        for tWord in arrayTaggedWord:
            if tag:
                result.append((tWord, prefix + tag))
            else:
                result.append((word, '_'))
                # because inside of container outside of tag is still "_"
                #result.append((tWord, prefix + containerTag))

            prefix = 'I-' 
        
        taggedWord = ""
        arrayTaggedWord = []
        tag = None

        if not ltCount and inContainer:
            inContainer = False
            containerTag = None

    
    if ltCount:
        print("ERROR: expected '>', found EOL instead")
    return result



def printUsage():
    print("USAGE: python cnec2nametag_parser.py CNEC_FILE")


if len(sys.argv) < 1:
    printUsage()
    sys.exit(1)


if not os.path.isfile(sys.argv[1]):
    print("IN_FILE does not exist")
    printUsage()
    sys.exit(1)

ifile = open(sys.argv[1])


for line in ifile:
    ent = parseLine(line)

    for word_tag in ent:
        print("{0}\t{1}".format(word_tag[0], word_tag[1]))
    print('')


sys.exit(0)
            
         

