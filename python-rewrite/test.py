import bt2
import json
import pickle
import datetime

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
    def __init__ (self, id, time, stream, count):
        self.id = id
        self.time = time
        self.stream = stream
        self.count = count
        inNodes: list[memoryNode] = []
        outNodes: list[memoryNode] = []
    
    def updateInNodes(self, nodes: list[memoryNode]):
        for node in nodes:
            self.inNodes.append(memoryNode(node))

    def updateOutNodes(self, nodes: list[memoryNode]):
        for node in nodes:
            self.outNodes.append(memoryNode(node))

def generateNodes():
    for msg in bt2.TraceCollectionMessageIterator('../testtraces'):
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
                node = memoryNode(cid,time,src,dst,stream,size,direction)
                print(msg.event.name)
                print(node.__dict__)
            if event.name == 'cupti_pinsight_lttng_ust:cudaKernelLaunch_begin':
                cid = event['correlationId']
                time = msg.default_clock_snapshot.value

#def testBehavtion(list: list[int]):
    #list.clear()
#testinglist = []
#testinglist.append(1)
#testinglist.append(3)
#print(testinglist)
#testBehavtion(testinglist)
generateNodes()