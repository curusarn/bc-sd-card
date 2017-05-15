

PATH = "/home/simonlet/git/nametag/organizations/plain_woLikvidaci_stripEscapedApostropes.txt"

with open(PATH, 'r') as plainOrgs:
    for line in plainOrgs:
        line = line.strip(' \t\n\r')
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
            


            
                
        

