#!/bin/bash
#cleanup old files
rm data
rm data.svg

#python script genreates DOT file
python3 ./main.py

#created png fromt DOt file
dot -Tsvg data -O
