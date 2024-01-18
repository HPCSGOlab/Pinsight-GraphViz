#!/bin/bash
#cleanup old files
rm data.dot
rm graph.png

#python script genreates DOT file
python3 ./test.py

#created png fromt DOt file
dot -Tpng data.dot -o graph.png 
