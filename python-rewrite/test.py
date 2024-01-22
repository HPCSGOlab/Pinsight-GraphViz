import bt2
import json
import pickle
import datetime
import networkx as nx

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
    

    def add_edge(self, edge1, edge2):
        if self.kernel_iterations:
            if isinstance(edge1, memoryNode) and isinstance(edge2, memoryNode):
                self.body += f"{edge1} [label=b{hex(edge1.addr)} color={self.getColor(edge1)}]; {edge2} [label=b{hex(edge2.addr)} color={self.getColor(edge2)}];\n"
                self.body += f"{edge1} -> {edge2};\n"
            elif isinstance(edge1, kernelNode) and isinstance(edge2, memoryNode):
                for i in range(1, edge1.count+1):
                    self.body += f"{edge1}i{i} [label=k{edge1.id} color={self.kernel_color} shape={self.kernel_shape}]; {edge2} [label = b{hex(edge2.addr)} color={self.getColor(edge2)}];\n"
                    self.body += f"{edge1}i{i} -> {edge2};\n"
            elif isinstance(edge1, memoryNode) and isinstance(edge2, kernelNode):
                for i in range (1, edge2.count+1):
                    self.body += f"{edge1} [label=b{hex(edge1.addr)} color={self.getColor(edge1)}]; {edge2}i{i} [label=k{edge2.id} color={self.kernel_color} shape={self.kernel_shape}];\n"
                    self.body += f"{edge1} -> {edge2}i{i};\n"
            elif isinstance(edge1, kernelNode) and isinstance(edge2, kernelNode):
                self.body += f"{edge1} [label=k{edge1.id} color={self.kernel_color} shape={self.kernel_shape}]; {edge2} [label=k{edge2.id} color={self.kernel_color} shape={self.kernel_shape}];\n"
                self.body += f"{edge1} -> {edge2};\n"
            else:
                raise Exception("Error whiel adding edge")
        else:
            if isinstance(edge1, memoryNode) and isinstance(edge2, memoryNode):
                self.body += f"{edge1} [label=b{hex(edge1.addr)} color={self.getColor(edge1)}]; {edge2} [label=b{hex(edge2.addr)} color={self.getColor(edge2)}];\n"
                self.body += f"{edge1} -> {edge2};\n"
            elif isinstance(edge1, kernelNode) and isinstance(edge2, memoryNode):
                self.body += f"{edge1} [label=k{edge1.id} color={self.kernel_color} shape={self.kernel_shape}]; {edge2} [label = b{hex(edge2.addr)} color={self.getColor(edge2)}];\n"
                self.body += f"{edge1}-> {edge2};\n"
            elif isinstance(edge1, memoryNode) and isinstance(edge2, kernelNode):
                self.body += f"{edge1} [label=b{hex(edge1.addr)} color={self.getColor(edge1)}]; {edge2} [label=k{edge2.id} color={self.kernel_color} shape={self.kernel_shape}];\n"
                self.body += f"{edge1} -> {edge2};\n"
            elif isinstance(edge1, kernelNode) and isinstance(edge2, kernelNode):
                self.body += f"{edge1} [label=k{edge1.id} color={self.kernel_color} shape={self.kernel_shape}]; {edge2} [label=k{edge2.id} color={self.kernel_color} shape={self.kernel_shape}];\n"
                self.body += f"{edge1} -> {edge2};\n"
            else:
                raise Exception("Error whiel adding edge")

    def getColor(self, node):
        if node.location == 0:
            return self.host_alloc_color
        else:
            return self.device_alloc_color

    def write(self, path):
        f = open(path, "w")
        f.write(f"{self.opener}{self.body}{self.closer}")
        f.close()
    def __repr__(self):
        return self.opener + self.body + self.closer

class node:
    pass

class memoryNode:
    id: int
    addr: int
    location: int
    iteration: int
    def __init__(self, id, addr, location) -> None:
        self.id = id
        self.addr = addr
        self.iteration = 0
        self.location = location
    @classmethod
    def fromNode (cls, otherNode):
        return cls(otherNode.id,otherNode.src, otherNode.location)
    def updated(self):
        self.iteration += 1;
    def __str__(self) -> str:
        #return f"{hex(self.addr)}i{self.iter}"
        return f"a{self.addr}i{self.iteration}"
    #def __str__(self):
        #return f"{self.addr} {self.location}"
    
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
        
    def __repr__(self) -> str:
        return f"k{self.id}"


def generateNodesv2(tracepath, allocations, T):
    previousKernal = None
    postNodes = []
    preNodes = []
    for msg in bt2.TraceCollectionMessageIterator(tracepath):
        if type(msg) is bt2._EventMessageConst:
            event = msg.event
            if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin' or 'cupti_pinsight_lttng_ust:cudaMemcpy_begin':
                '''
                cid = None
                if 'cupti_pinsight_lttng_ust:cudaMemcpy_begin':
                    cid = 0
                else:
                    cid = event['correlationId']
                
                cid = event['correlationId']
                src = event['src']
                dst = event['dst']
                direction = event['cudaMemcpyKind']._value

                if direction == 2 and previousKernal != None:
                    sourceNode = None;
                    for allocation in allocations:
                        if allocation.addr == src and allocation.location == 1:
                            allocation.updated()
                            T.add_edge(previousKernal, allocation)
                            sourceNode = allocation
                            break
                    for allocation in allocations:
                        if allocation.addr == dst and allocation.location == 0:
                            allocation.updated()
                            T.add_edge(sourceNode, allocation)
                            sourceNode = None
                            break

                if direction == 1:
                    sourceNode = None;
                    for allocation in allocations:
                        if allocation.addr == src and allocation.location == 0:
                            sourceNode = allocation
                            break
                    for allocation in allocations:
                        if allocation.addr == dst and allocation.location == 1:
                            preNodes.append(allocation)
                            T.add_edge(sourceNode, allocation)
                            sourceNode = None
                            break
                '''
            if event.name == 'cupti_pinsight_lttng_ust:cudaKernelLaunch_begin':
                cid = event['correlationId']
                time = msg.default_clock_snapshot.value
                stream = event['streamId']
                threads = (event['blockDimX'] * event['blockDimY'] * event['blockDimZ']) * (event['gridDimX'] * event['gridDimY'] * event['gridDimZ']) 
                node = kernelNode(cid, time, stream, threads)
                #T.add_node(node)
                for mn in preNodes:
                    T.add_edge(mn, node)
                previousKernal = node
                preNodes = []
                print(msg.event.name)
                print(node.__dict__)
    return T

def generateAllocations(tracepath):
    allocations = []
    for msg in bt2.TraceCollectionMessageIterator(tracepath):
        if type(msg) is bt2._EventMessageConst:
            event = msg.event
            if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin' or 'cupti_pinsight_lttng_ust:cudaMemcpy_begin':
            
                '''
                cid = None
                if 'cupti_pinsight_lttng_ust:cudaMemcpy_begin':
                    cid = 0
                else:
                    cid = event['correlationId']

                src = event['src']
                dst = event['dst']
                direction = event['cudaMemcpyKind']._value
                if direction == 1:
                    attemptAdd(cid,src, 0, allocations)
                    attemptAdd(cid,dst, 1, allocations)
                else: 
                    attemptAdd(cid, src, 1, allocations)
                    attemptAdd(cid, dst, 0, allocations)
                '''

    return allocations

def attemptAdd(cid, addr, location, allocationsList):
    node = memoryNode(cid, addr, location)
    if not containsAllocation(allocationsList, node):
        allocationsList.append(node)
      
def containsAllocation(list, node: memoryNode):
    for existingNode in list:
       if isinstance(existingNode, memoryNode):
            if existingNode.addr == node.addr and existingNode.location == node.location:
                return True
    return False

def updateAllocation(addr, location, allocationsList):
    pass

G = Graph(False, "box")
allocations = generateAllocations('../testtraces')
generateNodesv2('../testtraces', allocations, G)
print(G)
G.write('./data')