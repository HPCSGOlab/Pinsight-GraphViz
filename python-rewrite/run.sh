#!/bin/bash
#cleanup old files
rm data

#python script genreates DOT file
python3 ./main.py

#created png fromt DOt file
dot -Tsvg data -O
