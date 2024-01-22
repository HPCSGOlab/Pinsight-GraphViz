#!/bin/bash
#cleanup old files
rm data

#python script genreates DOT file
python3 ./test.py

#created png fromt DOt file
dot -Tsvg data -O
