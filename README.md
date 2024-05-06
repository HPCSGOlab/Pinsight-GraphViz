# Pinsight-GraphViz: Dependecy graph generation tool

This tool is designed to generate dependency CUDA graphs from traces collected with the[pinsight](https://github.com/passlab/pinsight) tool. We use the GraphViz visualization software to generate the dependecy graphs.

## Installation
Simply clone this repository, no build necessary.

## Generating graphs
In order to generate the graphs, execute run.sh inside of the /src folder. The script parses whatever traces are present inside of the /traces folder and generates an SVG of the depdendency graph.
