import bt2
import json
import pickle
import datetime
import networkx as nx

class node:
    pass

class memoryNode:
    id: int
    src: int
    time: int
    dst: int
    stream: int
    size: int
    direction: int
    def __init__(self, id, time, src, dst, stream, size, direction) -> None:
        self.id = id
        self.time = time
        self.src = src
        self.dst = dst
        self.stream = stream
        self.size = size
        self.direction = direction

    @classmethod
    def fromNode (cls, otherNode):
        return cls(otherNode.id,otherNode.src, otherNode.dst, otherNode.stream, otherNode.size)

class kernelNode:
    id: int
    time: int
    inNodes: list[memoryNode]
    outNodes: list[memoryNode]
    stream: int
    count: int

    debugInMod: bool = False
    dubugOutMod: bool = False
    def __init__ (self, id, time, stream, count):
        self.id = id
        self.time = time
        self.stream = stream
        self.count = count
        inNodes: list[memoryNode] = []
        outNodes: list[memoryNode] = []
    #updates input nodes with rewrite check
    def updateInNodes(self, nodes: list[memoryNode]):
        if self.debugInMod != True:
            for node in nodes:
                self.inNodes.append(memoryNode(node))
            self.inNodes = True
        else:
            raise Exception("you updated in nodes more than once")
        
    #updates out nodes with rewrite check
    def updateOutNodes(self, nodes: list[memoryNode]):
        if self.debugOutMod == False:
            for node in nodes:
                self.outNodes.append(memoryNode(node))
            self.outNodes = True
        else:
            raise Exception("you updated out nodes more than once")

#generates node from a path to CTF format traces
def generateNodes(tracepath):
    nodes = []
    for msg in bt2.TraceCollectionMessageIterator(tracepath):
        if type(msg) is bt2._EventMessageConst:
            event = msg.event
            if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin':
                cid = event['correlationId']
                time = msg.default_clock_snapshot.value
                src = event['src']
                dst = event['dst']
                stream = event['streamId']
                size = event['count']
                direction = event['cudaMemcpyKind']._value
                #create node object and add to list
                node = memoryNode(cid,time,src,dst,stream,size,direction)
                nodes.append(node)
                #debug prints
                print(msg.event.name)
                print(node.__dict__)
            if event.name == 'cupti_pinsight_lttng_ust:cudaKernelLaunch_begin':
                cid = event['correlationId']
                time = msg.default_clock_snapshot.value
                stream = event['streamId']
                threads = (event['blockDimX'] * event['blockDimY'] * event['blockDimZ']) * (event['gridDimX'] * event['gridDimY'] * event['gridDimZ']) 
                #create node object and add to list
                node = kernelNode(cid, time, stream, threads)
                nodes.append(node)
                #debug prints
                print(msg.event.name)
                print(node.__dict__)

    if len(nodes) > 0 :
        print('==============NODES GENERATED================')
        return nodes
    else:
        raise Exception("Node generation failed or input is empty")
                



#def testBehavtion(list: list[int]):
    #list.clear()
#testinglist = []
#testinglist.append(1)
#testinglist.append(3)
#print(testinglist)
#testBehavtion(testinglist)
G = nx.Graph()
list = generateNodes('../testtraces')
G.add_nodes_from(list)
nx.draw(G)