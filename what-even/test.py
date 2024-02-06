
class A:
    x: int
    y: int
    def __init__(self,x, y):
        self.x = x
        self.y = y
    def iterate(self):
        self.x += 1
        self.y += 1
    def __str__(self):
        return f"{self.x} {self.y}"

class HoldsA:
    point1: A
    point2: A
    def __init__(self):
        pass

def printinfo():
    print("global list")
    for item in globalList:
        print(item)
    print("holder")
    print(holder.point1)
    print(holder.point2)

def updateHolder():
    pass


globalList = [A(1,2), A(3,4)]

holder = HoldsA()

holder.point1 = globalList[0]
holder.point2 = globalList[1]

printinfo()

holder.point1.iterate()
holder.point2.iterate()

printinfo()