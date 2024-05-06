#!/bin/bash
#cleanup old files
rm *.dot
rm *.svg
rm debug.log

python3 main.py &> debug.log

#python script genreates DOT file
python3 ./main.py

#created png fromt DOt file
#dot -Tsvg data -O

for i in *.dot; do 
    dot -Tsvg $i -O
done
