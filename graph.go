package main

import (
	"bufio"
	"fmt"
	"os"
	"reflect"
	"strconv"
	"strings"
)

type node struct {
	correllationId int
	cpyType        int
	srcAddress     int
	dstAddress     int
	streamID       int
	nodeType       string
}

type graph struct {
	dependencies []string
}

func (g *graph) add(n node) {

}

func (g *graph) addEdge(n1 *node, n2 *node) {

}

// imports data from file as a string array
func importData(file string) ([]string, error) {
	traces := make([]string, 0)
	f, e := os.Open(file)
	if e != nil {
		return nil, e
	}
	scanner := bufio.NewScanner(f)

	for scanner.Scan() {
		traces = append(traces, scanner.Text())
	}
	return traces, nil
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

// returns value extracted from the parameter
func extractParameterValue(parameter string) interface{} {
	param_arr := strings.Split(parameter, "=")
	cleaned := strings.Trim(param_arr[1], " }")

	//check if its a memcpy since that has special formatting
	if strings.Contains(cleaned, "cudaMemcpyDeviceToHost") {
		return 2
	} else if strings.Contains(cleaned, "cudaMemcpyDeviceToHost") {
		return 1
	}

	val, err := strconv.Atoi(cleaned)
	if err != nil {
		if !strings.Contains(parameter, "0x") {
			return cleaned
		} else {
			cleaned, found := strings.CutPrefix(cleaned, "0x")
			if !found {
				panic(err)
			}
			v, err := strconv.ParseInt(cleaned, 16, 64)
			if err != nil {
				panic(err)
			}
			return v
		}
	}

	return val
}

// gemerates node from string data with given parameters
func genderateNode(data string, parameters []string) {
	var n node
	if strings.Contains(data, "Kernel") {
		n.nodeType = "kernel"
	}
	fields := strings.Split(data, ",")
	for _, field := range fields {
		for _, parameter := range parameters {
			if strings.Contains(field, parameter) {
				x := extractParameterValue(field)
				fmt.Println(parameter, ":", x, reflect.TypeOf(x))
			}
		}
	}
	fmt.Println("--------------------------------------------------")
}

func main() {
	data, err := importData("traces.log")
	if err != nil {
		panic(err)
	}
	cleanedData := extractTraces(data)
	for _, v := range cleanedData {
		genderateNode(v, []string{"src", "dst", "correlationId,", "streamId", "cudaMemcpyKind"})
	}
}
