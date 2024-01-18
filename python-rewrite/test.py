import bt2
import json
import pickle
import datetime
import networkx as nx

class node:
    pass

class memoryNode:
    id: int
    addr: int
    def __init__(self, id, addr) -> None:
        self.id = id
        self.addr = addr
    
    @classmethod
    def fromNode (cls, otherNode):
        return cls(otherNode.id,otherNode.src)

    def __repr__(self) -> str:
        return f"{hex(self.addr)}i{self.id}"
    
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
        
    def __repr__(self) -> str:
        return f"{self.id}"

#generates node from a path to CTF format traces
def generateNodes(tracepath):
    nodes = []
    for msg in bt2.TraceCollectionMessageIterator(tracepath):
        if type(msg) is bt2._EventMessageConst:
            event = msg.event
            if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin':
                cid = event['correlationId']
                src = event['src']
                dst = event['dst']
             
                node1 = memoryNode(cid, src)
                if not containsAllocation(nodes, node1):
                    nodes.append(node1)
                node2 = memoryNode(cid, dst)
                if not containsAllocation(nodes, node2):
                    nodes.append(node2)
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


def generateNodesv2(tracepath, T):
    nodes = []
    preLaunch = []
    postLaunch = []
    previous_kernel = None

    for msg in bt2.TraceCollectionMessageIterator(tracepath):
        if type(msg) is bt2._EventMessageConst:
            event = msg.event
            if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin':
                cid = event['correlationId']
                src = event['src']
                dst = event['dst']
                direction = event['cudaMemcpyKind']._value

                node1 = memoryNode(cid, src)
                if not containsAllocation(nodes, node1):
                    T.add_node(node1)
                node2 = memoryNode(cid, dst)
                if not containsAllocation(nodes, node2):
                    T.add_node(node2)
                T.add_edge(node1, node2)
               
                if previous_kernel != None and direction == 2:
                    T.add_edge(previous_kernel, node1)
                elif direction == 1:
                    preLaunch.append(node2)

                #debug prints
                print(msg.event.name)
                
            if event.name == 'cupti_pinsight_lttng_ust:cudaKernelLaunch_begin':
                cid = event['correlationId']
                time = msg.default_clock_snapshot.value
                stream = event['streamId']
                threads = (event['blockDimX'] * event['blockDimY'] * event['blockDimZ']) * (event['gridDimX'] * event['gridDimY'] * event['gridDimZ']) 
                #create node object and add to list
                node = kernelNode(cid, time, stream, threads)
                nodes.append(node)
                T.add_node(node)
                for mn in preLaunch:
                    T.add_edge(mn, node)
                preLaunch = []
                previous_kernel = node

                #debug prints
                print(msg.event.name)
                print(node.__dict__)
    return T


def generateEdges(tracepath, nodes, graph):
    for msg in bt2.TraceCollectionMessageIterator(tracepath):
        if type(msg) is bt2._EventMessageConst:
            event = msg.event
            if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin':
                cid = event['correlationId']
                src = event['src']
                dst = event['dst']
                pass
            if event.name == 'cupti_pinsight_lttng_ust:cudaKernelLaunch_begin':
                pass
        
def containsAllocation(list, node: memoryNode):
    for existingNode in list:
       if isinstance(existingNode, memoryNode):
            if existingNode.addr == node.addr:
                return True
    return False

def getAllocation(addr):
    pass
#def testBehavtion(list: list[int]):
    #list.clear()
#testinglist = []
#testinglist.append(1)
#testinglist.append(3)
#print(testinglist)
#testBehavtion(testinglist)
G = nx.Graph()
generateNodesv2('../testtraces', G)
nx.nx_agraph.write_dot(G, './data.dot')