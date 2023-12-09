package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

type Node struct {
	correllationId int
	address        string
	size           int
	nodeType       string
}

type Graph struct {
}

func (g *Graph) add(n Node) {

}

func (g *Graph) addEdge(n1 *Node, n2 *Node) {

}

// imports data from file as a string array
func importData(file string) []string {
	traces := make([]string, 0)
	f, e := os.Open(file)
	if e != nil {
		panic(e)
	}
	scanner := bufio.NewScanner(f)

	for scanner.Scan() {
		traces = append(traces, scanner.Text())
	}
	return traces
}

// extracts only relevant information from data
func extractTraces(data []string) []string {
	cleanedData := make([]string, 0)
	for _, v := range data {
		if strings.Contains(v, "cudaKernelLaunch") || strings.Contains(v, "cudaMemcpy") {
			cleanedData = append(cleanedData, v)
		}
	}
	return cleanedData
}

func main() {
	fmt.Println("test")
}
