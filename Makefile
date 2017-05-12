
readme:
	cat readme.txt

all: train

train:
	echo "Using baseline set of features"
	python3 src/code/train.py v1
	echo "Using binary target feature"
	python3 src/code/train.py v1_b
	echo "Using top5 target feature"
	python3 src/code/train.py v1_T
	echo "Using top5 and binary target feature"
	python3 src/code/train.py v1_bT
	echo "Using binary target feature, REMOVE original features"
	python3 src/code/train.py v1_xb
	echo "Using top5 target feature, REMOVE original features"
	python3 src/code/train.py v1_xT
	echo "Using top5 and binary target feature, REMOVE original features"
	python3 src/code/train.py v1_xbT


clean:
	rm results/*
