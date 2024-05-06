
import string


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
    print("global dict")
    for key in globalDict:
        print(f"{key} {globalDict[key]}")
    print("holder")
    print(holder.point1)
    print(holder.point2)

def updateHolder():
    pass


globalList = [A(1,2), A(3,4)]
globalDict = {}
globalDict['A'] = A(1,2)
globalDict['B'] = A(3,4)



holder = HoldsA()
temp = globalDict.get('A')
if temp != None:
    holder.point1 = temp
temp = globalDict.get('B')
if temp != None:
    holder.point2 = temp

printinfo()

holder.point1.iterate()
holder.point2.iterate()

printinfo()