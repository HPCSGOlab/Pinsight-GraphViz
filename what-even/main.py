from operator import contains
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

class deviceMemoryNode(memoryNode):
    stream: int
    def __init__(self, id, addr, stream):
        super().__init__(id, addr)
        self.stream = stream
    def __repr__(self) -> str:
        return f"z{self.addr}i{self.iteration}s{self.stream}"
    
class hostMemoryNode(memoryNode):
    def __init__(self, id, addr):
        super().__init__(id, addr)
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
    def updateNodes(self):
        self.node1.iteration += 1
        self.node2.iteration += 1
    def __init__ (self, node1, node2):
        self.node1 = node1
        self.node2 = node2
    def __repr__(self) -> str:
        return f"{self.node1} ==> {self.node2}"

class HtDPair(Pair):
    def _init__ (self, node1, node2):
        super().__init__(node1, node2)
    def __repr__(self) -> str:
        return f"HtD : {self.node1} ==> {self.node2}"

class DtHPair(Pair):
    def __init__(self, node1, node2):
        super().__init__(node1, node2)
    def __repr__(self) -> str:
        return f"DtH : {self.node1} ==> {self.node2}"

class DtDPair(Pair):
    def __init__(self, node1, node2):
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
        if type(event) == Pair:
            event.reset()

#generates dependencies based on parsed events. returns a dependency grpah
def generateDependencGraph(events, streams):
    g = Graph()
    for knownStream in streams:
        previousKernel = None
        preMemoryNodes = []
        for event in events:
            if type(event) == DtHPair and previousKernel != None:
                event.updateNodes()
                g.add_pair_edge(previousKernel, event)
            if type(event) == HtDPair:
                preMemoryNodes.append(event)

        #reset to resimulate data from the beginning for each stram
        resetNodes(events)
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

def generateEvents(tracepath):
    events = []
    for msg in bt2.TraceCollectionMessageIterator(tracepath):
        if type(msg) is bt2._EventMessageConst:
            event = msg.event
            if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin' or event.name =='cupti_pinsight_lttng_ust:cudaMemcpy_begin':
                generateFromMemoryEvent(event, events)
            if event.name == 'cupti_pinsight_lttng_ust:cudaKernelLaunch_begin':
                generateFromKernelEvent(event, events)
    return events

#Adds a memory pair to the events from an event
def generateFromMemoryEvent(event, events):
    stream = DEFAULT_STREAM
    if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin':
        stream = event['streamId']
    cid = event['correlationId']
    src = event['src']
    dst = event['dst']
    cpytype = event['cudaMemcpyKind']._value
    pair = attemptAdd(cid, src, dst, cpytype, events, stream)
    if pair != None:
        events.append(pair)

#Adds a kernel event to events
def generateFromKernelEvent(event, events):
    for kernel in events:
        if type(kernel) == kernelNode and kernel.id == event['correlationId']:
            return    
    threads = (event['blockDimX'] * event['blockDimY'] * event['blockDimZ']) * (event['gridDimX'] * event['gridDimY'] * event['gridDimZ']) 
    events.append(kernelNode(event['correlationId'], event['devId'], event['streamId'], threads))

#checks to see if allocation exists in allocations list.
#returns true of allocation exists, false otherwise
def containsAllocation(addr, location, events):
    for allocation in events:
        if location == 0:
            if type(allocation) == hostMemoryNode and allocation.addr == addr:
                return True 
        else:
            if type(allocation) == deviceMemoryNode and allocation.addr == addr:
                return True
    return False

#Returns a node pair based on copy type if it doesn't exist in events list
def attemptAdd(cid, src, dst, cpytype, allocations, stream = DEFAULT_STREAM):
    node1 = None
    node2 = None
    if cpytype == 1:
        if not containsAllocation(src, 0, allocations):
            node1 = hostMemoryNode(cid, src)
        if not containsAllocation(dst, 1, allocations):
            node2 = deviceMemoryNode(cid, dst, stream)
        return HtDPair(node1, node2)
    elif cpytype == 2:
        if not containsAllocation(src, 1, allocations):
            node1 = deviceMemoryNode(cid, src, stream)
        if not containsAllocation(dst, 0, allocations):
            node2 = hostMemoryNode(cid, dst)
        return DtHPair(node1, node2)
    elif cpytype == 3:
        if not containsAllocation(src, 1, allocations):
            node1 = deviceMemoryNode(cid, src, stream)
        if not containsAllocation(dst, 1, allocations):
            node2 = deviceMemoryNode(cid, dst, stream)
        return DtDPair(node1, node2)
    

#create objects from data and add them to a list

#generate streams from the data
#geneate dependencies




def main():
    tracepath = '../testtracesv2'
    streams = generateStreams(tracepath)
    events = generateEvents(tracepath)
    for stream in streams:
        print(stream)
    for event in events:
        print(event)

main()
