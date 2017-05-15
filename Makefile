
readme:
	cat readme.md

all: train

train:
	echo "Using baseline set of features"
	python3 src/code/train.py v2
	echo "Using all available features"
	python3 src/code/train.py v2_blLtT
	echo "Using the best feature from baseline solution"
	python3 src/code/train.py v2_blLtT -o 44 
	echo "Using the best target-based feature"
	python3 src/code/train.py v2_blLtT -o 29


clean:
	rm results/*
