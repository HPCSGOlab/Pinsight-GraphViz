from operator import contains
from re import S
from unittest.mock import DEFAULT
import bt2
import json
import pickle
import datetime
import networkx as nx
import cProfile


DEFAULT_STREAM = 7
class memoryNode:
    id: int
    addr: int
    iteration: int
    def __init__(self, id, addr) -> None:
        self.id = id
        self.addr = addr
        self.iteration = 0
    @classmethod
    def fromNode (cls, otherNode):
        return cls(otherNode.id, otherNode.addr)
    def updated(self):
        self.iteration += 1
    def allocRepr(self) -> str:
        return f"GENERIC {self.addr}"
    def __repr__(self) -> str:
        return f"g{self.addr}"

class deviceMemoryNode(memoryNode):
    stream: int
    def __init__(self, id, addr, stream):
        super().__init__(id, addr)
        self.stream = stream
    def allocRepr(self) -> str:
        return f"DEVICE {self.addr}"
    def __repr__(self) -> str:
        return f"z{self.addr}i{self.iteration}s{self.stream}"
    
class hostMemoryNode(memoryNode):
    def __init__(self, id, addr):
        super().__init__(id, addr)
    def allocRepr(self) -> str:
        return f"HOST {self.addr}"
    def __repr__(self) -> str:
        return f"z{self.addr}i{self.iteration}"

class kernelNode:
    id: int
    devId: int
    time: int
    stream: int
    count: int
    def __init__(self, id, devId, stream, count):
        self.id = id
        self.devId = devId
        
        self.stream = stream
        self.count = count
    def __repr__(self) -> str:
        return f"k{self.id}"

class Pair():
    node1: memoryNode
    node2: memoryNode
    def reset(self):
        self.node1.iteration = 0
        self.node2.iteration = 0
    def __init__ (self, node1=None, node2=None):
        if node1 != None and node2 != None:
            self.node1 = node1
            self.node2 = node2
        elif (node1 != None and node2 == None) or (node1 == None and node2 != None):
            raise Exception("Bad constructor parameters")
    def __repr__(self) -> str:
        return f"{self.node1} ==> {self.node2}"

class HtDPair(Pair):
    def reset(self):
        self.node1.iteration = 0
        self.node2.iteration = 0
    def updateNodes(self):
        self.node2.iteration += 1
    def _init__ (self, node1=None, node2=None):
        super().__init__(node1, node2)
    def __repr__(self) -> str:
        return f"HtD : {self.node1} ==> {self.node2}"

class DtHPair(Pair):
    def reset(self):
        self.node1.iteration = 0
        self.node2.iteration = 0
    def updateNodes(self):
        self.node1.iteration += 1
        self.node2.iteration += 1
    def __init__(self, node1=None, node2=None):
        super().__init__(node1, node2)
    def __repr__(self) -> str:
        return f"DtH : {self.node1} ==> {self.node2}"

class DtDPair(Pair):
    def reset(self):
        self.node1.iteration = 0
        self.node2.iteration = 0
    def updateNodes(self):
        self.node2.iteration += 1
    def __init__(self, node1=None, node2=None):
        super().__init__(node1, node2)
    def __repr__(self) -> str:
        return f"DtD : {self.node1} ==> {self.node2}"

class Graph:
    opener = "digraph G{\n"
    body = ""
    closer = "}"
    kernel_iterations = False
    kernel_color = "chartreuse4"
    kernel_shape = "ellipse"
    device_alloc_color = "chartreuse3"
    host_alloc_color = "deepskyblue2"
    
    def __init__(self,show_kernal_oterations=False, kernel_node_shape="ellipse"):
        self.kernel_shape = kernel_node_shape
        self.kernel_iterations = show_kernal_oterations
        pass
        
    def add_pair_edge(self, pair: Pair):
        self.add_edge(pair.node1, pair.node2)
        
    def add_edge(self, edge1, edge2):
        if (self.kernel_iterations == False):
            if isinstance(edge1, memoryNode) and isinstance(edge2, memoryNode):
                self.body += f"{edge1} [label=b{hex(edge1.addr)} color={self.getColor(edge1)}];"
                self.body += f"{edge2} [label=b{hex(edge2.addr)} color={self.getColor(edge2)}];\n"
                self.body += f"{edge1} -> {edge2};\n"
            elif isinstance(edge1, kernelNode) and isinstance(edge2, memoryNode):
                self.body += f"{edge1} [label=k{edge1.id} color={self.kernel_color} shape={self.kernel_shape}];"
                self.body += f"{edge2} [label = b{hex(edge2.addr)} color={self.getColor(edge2)}];\n"
                self.body += f"{edge1}-> {edge2};\n"
            elif isinstance(edge1, memoryNode) and isinstance(edge2, kernelNode):
                self.body += f"{edge1} [label=b{hex(edge1.addr)} color={self.getColor(edge1)}];"
                self.body += f"{edge2} [label=k{edge2.id} color={self.kernel_color} shape={self.kernel_shape}];\n"
                self.body += f"{edge1} -> {edge2};\n"
            elif isinstance(edge1, kernelNode) and isinstance(edge2, kernelNode):
                self.body += f"{edge1} [label=k{edge1.id} color={self.kernel_color} shape={self.kernel_shape}];"
                self.body += f"{edge2} [label=k{edge2.id} color={self.kernel_color} shape={self.kernel_shape}];\n"
                self.body += f"{edge1} -> {edge2};\n"
            else:
                raise Exception("Error while adding edge")
        else:
            if isinstance(edge1, memoryNode) and isinstance(edge2, memoryNode):
                self.body += f"{edge1} [label=b{hex(edge1.addr)} color={self.getColor(edge1)}];"
                self.body += f"{edge2} [label=b{hex(edge2.addr)} color={self.getColor(edge2)}];\n"
                self.body += f"{edge1} -> {edge2};\n"
            elif isinstance(edge1, kernelNode) and isinstance(edge2, memoryNode):
                self.body += f"{edge2} [label = b{hex(edge2.addr)} color={self.getColor(edge2)}];\n"
                for i in range(0, edge1.count):
                    self.body += f"{edge1}vb{i} [label=k{edge1.id} color={self.kernel_color} shape={self.kernel_shape}];"
                    self.body += f"{edge1}vb{i}-> {edge2};\n"
            elif isinstance(edge1, memoryNode) and isinstance(edge2, kernelNode):
                self.body += f"{edge1} [label=b{hex(edge1.addr)} color={self.getColor(edge1)}];"
                for i in range(0, edge2.count):
                    self.body += f"{edge2}vb{i} [label=k{edge2.id} color={self.kernel_color} shape={self.kernel_shape}];\n"
                    self.body += f"{edge1} -> {edge2}vb{i};\n"
            elif isinstance(edge1, kernelNode) and isinstance(edge2, kernelNode):
                self.body += f"{edge1} [label=k{edge1.id} color={self.kernel_color} shape={self.kernel_shape}];"
                self.body += f"{edge2} [label=k{edge2.id} color={self.kernel_color} shape={self.kernel_shape}];\n"
                self.body += f"{edge1} -> {edge2};\n"
            else:
                raise Exception("Error while adding edge")
            

    def getColor(self, node):
        if type(node) == hostMemoryNode:
            return self.host_alloc_color
        else:
            return self.device_alloc_color

    def write(self, path):
        f = open(path, "w")
        f.write(f"{self.opener}{self.body}{self.closer}")
        f.close()
    def __repr__(self):
        return self.opener + self.body + self.closer

#resets the iterations on memory nodes
def resetNodes(events):
    for event in events:
        if issubclass(type(event), Pair):
            event.reset()

#generates dependencies based on parsed events. returns a dependency grpah
def generateDependencGraph(events, streams):
    streams.append(-1)
    g = Graph(False, 'rectangle')
    for knownStream in streams:
        print(f"========== ...STREAM {knownStream}... ==========")
        previousKernel = None
        lastEvent = None
        preMemoryNodes: list[Pair] = []
        for event in events:
            if type(event) == kernelNode and event.stream == knownStream and type(lastEvent) == kernelNode:
                g.add_edge(lastEvent, event)
                lastEvent = event
                print(event)
                
            elif type(event) == kernelNode and event.stream == knownStream:
                for e in preMemoryNodes:
                    e.node2.iteration += 1
                    g.add_edge(e.node1, e.node2)
                    g.add_edge(e.node2, event)
                preMemoryNodes.clear()
                previousKernel = event
                lastEvent = event
                print(event)

            if type(event) == DtHPair and previousKernel != None:
                stream = -1
                if type(event.node1) == deviceMemoryNode:
                    stream = event.node1.stream
                if stream == knownStream:
                    event.updateNodes()
                    g.add_edge(previousKernel, event.node1)
                    g.add_edge(event.node1, event.node2)
                    lastEvent = event
                    print(event)

            elif type(event) == HtDPair:
                stream = -1
                if type(event.node2) == deviceMemoryNode:
                    stream = event.node2.stream
                if stream == knownStream:
                    preMemoryNodes.append(event)
                    lastEvent = event
                    print(event)


            elif type(event)== DtDPair:
                if type(event.node1) == deviceMemoryNode:
                    stream = event.node1.stream
                if stream == knownStream:
                    if previousKernel != None:
                        event.updateNodes()
                        g.add_edge(previousKernel, event.node1)
                    g.add_edge(event.node1, event.node2)
                    lastEvent = event
                    print(event)

        #reset to resimulate data from the beginning for each stram
        resetNodes(events)
    g.write('./data')
    return g


def generateDependencGraphV2(events, streams):
    streams.append(-1)
    g = Graph(False, 'rectangle')
    
    previousKernel = None
    lastEvent = None
    preMemoryNodes: list[Pair] = []
    for event in events:
        if type(event) == kernelNode and type(lastEvent) == kernelNode:
            g.add_edge(lastEvent, event)
            lastEvent = event
            print(event)
            
        elif type(event) == kernelNode:
            for e in preMemoryNodes:
                e.node2.iteration += 1
                g.add_edge(e.node1, e.node2)
                g.add_edge(e.node2, event)
            preMemoryNodes.clear()
            previousKernel = event
            lastEvent = event
            print(event)

        if type(event) == DtHPair and previousKernel != None:
            if type(event.node1) == deviceMemoryNode:
                event.updateNodes()
                g.add_edge(previousKernel, event.node1)
                g.add_edge(event.node1, event.node2)
                lastEvent = event
                print(event)

        elif type(event) == HtDPair:
            if type(event.node2) == deviceMemoryNode:
                preMemoryNodes.append(event)
                lastEvent = event
                print(event)


        elif type(event)== DtDPair:
            if type(event.node1) == deviceMemoryNode:
                if previousKernel != None:
                    event.updateNodes()
                    g.add_edge(previousKernel, event.node1)
                g.add_edge(event.node1, event.node2)
                lastEvent = event
                print(event)

    #reset to resimulate data from the beginning for each stram
    
    g.write('./data')
    return g

def generateStreams(tracepath):
    streams = []
    #append default streams
    streams.append(7)
    for msg in bt2.TraceCollectionMessageIterator(tracepath):
        if type(msg) is bt2._EventMessageConst:
            event = msg.event
            if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin' or event.name == 'cupti_pinsight_lttng_ust:cudaKernelLaunch_begin':
                stream = event['streamId'] 
                if stream not in streams:
                    streams.append(stream)
    return streams

def generateAllocations(tracepath):
    allocations = {}
    for msg in bt2.TraceCollectionMessageIterator(tracepath):
        if type(msg) is bt2._EventMessageConst:
            event = msg.event
            stream = DEFAULT_STREAM
            if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin' or event.name == 'cupti_pinsight_lttng_ust:cudaMemcpy_begin':
                eventType = event['cudaMemcpyKind']._value
                if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin':
                    stream = event['streamId']
                if eventType == 1:
                    alloc1 = hostMemoryNode(event['correlationId'], event['src'])
                    alloc2 = deviceMemoryNode(event['correlationId'], event['dst'], stream)
                    if alloc1.allocRepr not in allocations:
                        allocations[alloc1.allocRepr()] = alloc1
                    if alloc2.allocRepr not in allocations:
                        allocations[alloc2.allocRepr()] = alloc2

                elif eventType == 2:
                    alloc1 = deviceMemoryNode(event['correlationId'], event['src'], stream)
                    alloc2 = hostMemoryNode(event['correlationId'], event['dst'])
                    if alloc1.allocRepr not in allocations:
                        allocations[alloc1.allocRepr()] = alloc1
                    if alloc2.allocRepr not in allocations:
                        allocations[alloc2.allocRepr()] = alloc2
    
                elif eventType == 3:
                    alloc1 = deviceMemoryNode(event['correlationId'], event['src'], stream)
                    alloc2 = deviceMemoryNode(event['correlationId'], event['dst'], stream)
                    if alloc1.allocRepr not in allocations:
                        allocations[alloc1.allocRepr()] = alloc1
                    if alloc2.allocRepr not in allocations:
                        allocations[alloc2.allocRepr()] = alloc2
    return allocations


def generateEvents(tracepath, allocations):
    events = []
    for msg in bt2.TraceCollectionMessageIterator(tracepath):
        if type(msg) is bt2._EventMessageConst:
            event = msg.event
            if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin' or event.name =='cupti_pinsight_lttng_ust:cudaMemcpy_begin':
                generateFromMemoryEvent(event, events, allocations)
            if event.name == 'cupti_pinsight_lttng_ust:cudaKernelLaunch_begin':
                generateFromKernelEvent(event, events)
    return events

#Adds a memory pair to the events from an event
def generateFromMemoryEvent(event, events, allocations):
    stream = DEFAULT_STREAM
    if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin':
        stream = event['streamId']
    cid = event['correlationId']
    src = event['src']
    dst = event['dst']
    cpytype = event['cudaMemcpyKind']._value

    #try to add allocation to global scope allocations
    pair = attemptAdd(cid, src, dst, cpytype, events, allocations,stream)
    if pair != None:
        events.append(pair)

def generateFromKernelEvent(event, events):
#Adds a kernel event to events
    for kernel in events:
        if type(kernel) == kernelNode and kernel.id == event['correlationId']:
            return    
    threads = (event['blockDimX'] * event['blockDimY'] * event['blockDimZ']) * (event['gridDimX'] * event['gridDimY'] * event['gridDimZ']) 
    events.append(kernelNode(event['correlationId'], event['devId'], event['streamId'], threads))

#checks to see if allocation exists in allocations list.
#returns true of allocation exists, false otherwise
def containsEvent(addr, location, events):
    for allocation in events:
        if location == 0:
            if type(allocation) == hostMemoryNode and allocation.addr == addr:
                return True 
        else:
            if type(allocation) == deviceMemoryNode and allocation.addr == addr:
                return True
    return False

#Returns a node pair based on copy type if it doesn't exist in events list
def attemptAdd(cid, src, dst, cpytype, events, allocations, stream = DEFAULT_STREAM):
    tempNode1 = None
    tempNode2 = None
    if cpytype == 1:
        pair = HtDPair()
        if not containsEvent(src, 0, events):
            tempNode1 = hostMemoryNode(cid, src)
            if  tempNode1.allocRepr() not in allocations:
                raise Exception("Allocation of address not preset in dictionary")
            else:
                pair.node1 = allocations.get(tempNode1.allocRepr())
        if not containsEvent(dst, 1, events):
            tempNode2 = deviceMemoryNode(cid, dst, stream)
            if  tempNode2.allocRepr() not in allocations:
                raise Exception("Allocation of address not preset in dictionary")
            else:
                pair.node2 = allocations.get(tempNode2.allocRepr())
        return pair
    elif cpytype == 2:
        pair = DtHPair()
        if not containsEvent(src, 1, events):
            tempNode1 = deviceMemoryNode(cid, src, stream)
            if  tempNode1.allocRepr() not in allocations:
                raise Exception("Allocation of address not preset in dictionary")
            else:
                pair.node1 = allocations.get(tempNode1.allocRepr())
        if not containsEvent(dst, 0, events):
            tempNode2 = hostMemoryNode(cid, dst)
            if tempNode2.allocRepr() not in allocations:
                raise Exception("Allocation of address not preset in dictionary")
            else:
                pair.node2 = allocations.get(tempNode2.allocRepr())
        return pair
    elif cpytype == 3:
        pair = DtDPair()
        if not containsEvent(src, 1, events):
            tempNode1 = deviceMemoryNode(cid, src, stream)
            if tempNode1.allocRepr() not in allocations:
                raise Exception("Allocation of address not preset in dictionary")
            else:
                pair.node1 = allocations.get(tempNode1.allocRepr())
        if not containsEvent(dst, 1, events):
            tempNode2 = deviceMemoryNode(cid, dst, stream)
            if  tempNode2.allocRepr() not in allocations:
                raise Exception("Allocation of address not preset in dictionary")
            else:
                pair.node2 = allocations.get(tempNode2.allocRepr())
        return DtDPair(tempNode1, tempNode2)
    

#create objects from data and add them to a list

#generate streams from the data
#geneate dependencies
def test(tracepath):
    streams = generateStreams(tracepath)
    print("========== streams ==========")
    for stream in streams:
        print(stream)

    allocs = generateAllocations(tracepath)
    print("========== allocations ==========")


    for alloc in allocs:
        print(alloc)

    events = generateEvents(tracepath, allocs)
    print("========== events ==========")
    for event in events:
        print(event)


    for key in allocs:
        allocs[key].updated()
        #print(allocs[key])

    print("========== events ==========")
    for event in events:
        print(event)


    for key in allocs:
        allocs[key].updated()
        #print(allocs[key])

    print("========== events ==========")
    for event in events:
        print(event)


    resetNodes(events)
        #print(allocs[key])

    print("==========(POST RESET) events ==========")
    for event in events:
        print(event)
def main():
    tracepath = '../streamtraces'
    streams = generateStreams(tracepath)
    allocs = generateAllocations(tracepath)
    events = generateEvents(tracepath, allocs)

    for event in events:
        print(event)
    #g = generateDependencGraph(events, streams)
    g = generateDependencGraphV2(events, streams)
    #test(tracepath)


main()
