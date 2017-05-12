import json
from glob import glob
import sys
import os
import pickle
import argparse
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
from sklearn.metrics import precision_score
from sklearn.metrics import accuracy_score

class ShowHelpOnErrorParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

DATA_PATH = "/home/simonlet/git/nametag/feature_data"

parser = ShowHelpOnErrorParser()
parser.add_argument("data", type=str,
                    help="data to use, from directory: <{0}>".format(DATA_PATH))
opt = parser.parse_args()

SUFFIX = "_" + opt.data 
DATA_VERSION = opt.data
PATH = os.path.join(DATA_PATH, DATA_VERSION)
if not os.path.exists(PATH):
    print("Data not found - directory does not exist <{0}>".format(PATH))
    sys.exit(3)

def load_data():
    data = []
    for cls, pth in [(0, "negative"), (1, "positive")]:
        for i in glob(os.path.join(PATH, pth, "*")):
            try:
                d = json.load(open(i, "r"))
                phish = d.get("phishing", {})
                phish.pop("suspicious_links")
                data.append((phish, cls))
            except Exception as e:
                print(e, file=sys.stderr)
    return data


def vectorize(x):
    dv = DictVectorizer()
    arr = dv.fit_transform(x)
    feature_names = dv.get_feature_names()
    print("features {}".format(feature_names))
    filename = "feature_names"+SUFFIX+".json"
    with open(filename, "w") as f:
        f.write(json.dumps(dv.get_feature_names()))
        print("Features stored to {}".format(filename))
    return arr.toarray()


if __name__ == "__main__":
    data = load_data()
    xd = [i[0] for i in data]
    y = [i[1] for i in data]
    print("Data loaded, samples {}".format(len(data)))
    x = vectorize(xd)
    print("x data")
    print(x)
    x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=42)
    clf = RandomForestClassifier(n_estimators=20)
    #RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1)
    print("Starting training")
    model = clf.fit(x_train, y_train)
    print("Model trained")
    model_file = "model"+SUFFIX+".pkl"
    pickle.dump(model, open(model_file, "wb"))
    print("Model stored to {}".format(model_file))
    print()
    predicted = model.predict(x_test)
    report = ""
    report += 'Precision:\t{}\n'.format(precision_score(y_test, predicted,
                                           average='weighted'))
    report += 'Accuracy:\t{}\n'.format(accuracy_score(y_test, predicted))
    report += '\n'
    report += classification_report(y_test, predicted)
    print(report)
    report_file = "report"+SUFFIX+".txt"
    with open(report_file, "w") as f:
        f.write(report)
    print("Report stored to {}".format(report_file))
