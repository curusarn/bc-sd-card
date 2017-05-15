# server start, server kill
import runCmd as rc
# rest server call - ner 
import json
import urllib2


# needs to be static because of killAndExit option
def killServer(quiet=True):
    cmd = "pkill nametag_server"
    rc.runCmd(cmd, quiet)


class nametagServer:
    def getModelCfg(self, m):
        return " " + m + " trained/" + m + ".ner random_acknoledgement"


    def launchServer(self):
        cmd = "src/rest_server/nametag_server --daemon " + self.port 
        for m in self.models:
            cmd += self.getModelCfg(m)

        rc.runCmd(cmd, self.quiet)


    def isServerUp(self):
        url = "http://localhost:" + self.port + "/models"
              
        try:
            res = json.load(urllib2.urlopen(url))
        except Exception as e:
            return False 

        return True


    def hasModel(self, model):
        url = "http://localhost:" + self.port + "/models"
              
        try:
            res = json.load(urllib2.urlopen(url))
            models = res["models"]
            if model not in models.keys():
                return False
        except Exception as e:
            return False 

        return True


    def __init__(self, keepAlive, quiet=False, models=None):
        self.port = "8080"
        self.keepAlive = keepAlive
        self.quiet = quiet
        self.models = [ 
            #"cnec2",
            #"cnec2-orgsTitles_hasUrl",
            #"cnec2-phishableOrgTitles",
            #"cnec2-phishableOrgTitles2",
            "cnec2-phishableOrgTitles3_all",
            #"cnec2-allOrgs",
            "conll"
            #"conll-notExtended"
            ]

        if models is not None:
            self.models = models

        # launch server only if it's not already up
        if not self.isServerUp():
            self.launchServer()


    def __del__(self):
        # dont kill the server if keep-alive option is present
        if not self.keepAlive:
            # passing argument to killServer because it's static method
            #   needed for killing already running server w/o instance of nametagServer
            killServer(self.quiet)


    def tagText(self, text, model):
        data = urllib2.quote(text)
        url = "http://localhost:" + self.port +\
              "/recognize?output=vertical&model=" + model + "&data=" + data
              
        try:
            res = json.load(urllib2.urlopen(url))
            res = res["result"]
        except Exception as e:
            # TODO: better error handling
            res = "" 

        return res


