import numpy as np
from enum import Enum, auto

class Dir(Enum):
    NORTH = 0
    WEST = 1
    SOUTH = 2
    EAST = 3

class DynamicMap:

    def __init__(self, array=None):
        if array is None:
            self.map = np.empty(shape=(3,3), dtype=str)
            self.RADIUS = 1
        else:
            self.map = np.array(array, dtype=str)
            self.RADIUS = len(self.map)//2

    __c2a = lambda self, rc : rc+self.RADIUS # Centered to absolute coordinate
    __a2c = lambda self, ac : ac-self.RADIUS # Absolute to centered coordinate

    def reshape(self, newRadius):
        newMap = np.empty(shape=(2*newRadius+1, 2*newRadius+1), dtype=str)
        if newRadius >= self.RADIUS:
            oldmin, oldmax = -self.RADIUS, self.RADIUS
            self.RADIUS = newRadius
            newMap[self.__c2a(oldmin) : self.__c2a(oldmax)+1 , self.__c2a(oldmin) : self.__c2a(oldmax)+1] = self.map
            self.map = newMap
        else:
            newmin, newmax = -newRadius, newRadius
            self.map = self.map[self.__c2a(newmin) : self.__c2a(newmax) + 1, self.__c2a(newmin) : self.__c2a(newmax) + 1]
            self.RADIUS = newRadius

    def setVal(self, cc_elem, val):
        cx_elem, cy_elem = cc_elem
        if max(abs(cx_elem), abs(cy_elem)) > self.RADIUS:
            self.reshape(max(abs(cx_elem), abs(cy_elem)))
        self.map[self.__c2a(cx_elem), self.__c2a(cy_elem)] = val

    def getVal(self, cc_elem):
        cx_elem, cy_elem = cc_elem
        if max(abs(cx_elem), abs(cy_elem)) > self.RADIUS:
            self.reshape(max(abs(cx_elem), abs(cy_elem)))
        return self.map[self.__c2a(cx_elem), self.__c2a(cy_elem)]

    def shift(self, dir):
        if dir == Dir.NORTH:
            if not(np.all(self.map[-1] == '')):
                self.reshape(self.RADIUS+1)
            self.map = np.concatenate((np.empty((1,2*self.RADIUS+1), dtype=str), self.map), axis=0)[:-1,:]
        elif dir == Dir.SOUTH:
            if not(np.all(self.map[0] == '')):
                self.reshape(self.RADIUS+1)
            self.map = np.concatenate((self.map, np.empty((1,2*self.RADIUS+1), dtype=str)), axis=0)[1:,:]
        elif dir == Dir.EAST:
            if not(np.all(self.map[:,0] == '')):
                self.reshape(self.RADIUS+1)
            self.map = np.concatenate((self.map, np.empty((2*self.RADIUS+1, 1), dtype=str)), axis=1)[:,1:]
        elif dir == Dir.WEST:
            if not(np.all(self.map[:,-1] == '')):
                self.reshape(self.RADIUS+1)
            self.map = np.concatenate((np.empty((2*self.RADIUS+1,1), dtype=str), self.map), axis=1)[:,:-1]

    # The robot trusts its own sensors more than the data received by an other robot
    def __putMap(self, received_map, cc_x, cc_y):
        toMerge = np.empty(self.map.shape, dtype=str)
        toMerge[self.__c2a(cc_x-received_map.RADIUS) : self.__c2a(cc_x+received_map.RADIUS)+1, self.__c2a(cc_y-received_map.RADIUS) : self.__c2a(cc_y+received_map.RADIUS)+1] = received_map.map
        missmatches = np.count_nonzero((self.map != '') * (toMerge != '') * (self.map != toMerge))
        self.map = np.where(self.map == '', toMerge, self.map)
        return missmatches

    def evaluate(self, received_map, cc_x, cc_y):
        toMerge = np.empty(self.map.shape, dtype=str)
        toMerge[self.__c2a(cc_x-received_map.RADIUS) : self.__c2a(cc_x+received_map.RADIUS)+1, self.__c2a(cc_y-received_map.RADIUS) : self.__c2a(cc_y+received_map.RADIUS)+1] = received_map.map
        missmatches = np.count_nonzero((self.map != '') * (toMerge != '') * (self.map != toMerge))
        correctmatches=  np.count_nonzero((self.map != '') * (toMerge != '') * (self.map == toMerge))
        if correctmatches>0:
          return missmatches,correctmatches,missmatches/(missmatches+correctmatches)
        else:
          return 0,0,0

    def mergeApproximateMaps(self, received_map, cc_approx):
        cc_x_approx,cc_y_approx = cc_approx
        if (max(abs(cc_x_approx), abs(cc_y_approx))+1+received_map.RADIUS > self.RADIUS):
            self.reshape(max(abs(cc_x_approx), abs(cc_y_approx))+1+received_map.RADIUS)
        missmatches,correctmatches, ratio=self.evaluate(received_map,cc_x_approx,cc_y_approx)
        for x in [-1,0,1]:
            for y in [-1,0,1]:

                missmatches2,correctmatches2,ratio2 = self.evaluate(received_map,cc_x_approx+x,cc_y_approx+y)
                print(ratio,ratio2,x,y)
                if (ratio2>ratio):
                   print("recursion")
                   self.mergeApproximateMaps(received_map,(cc_x_approx+x,cc_y_approx+y))
                   return True
        self.mergeMaps(received_map,(cc_x_approx,cc_y_approx))

    def mergeMaps(self, received_map, cc_center): # cc for centered coordinates of the emitting robot
        cc_x, cc_y = cc_center
        if (max(abs(cc_x), abs(cc_y))+received_map.RADIUS > self.RADIUS):
            self.reshape(max(abs(cc_x), abs(cc_y))+received_map.RADIUS)
        self.__putMap(received_map, cc_x, cc_y)

    def map_extract(self, radius):
        map_extract = self.map.copy()
        map_extract[self.__c2a(0), self.__c2a(0)] = 'R'
        if radius >= self.RADIUS:
            return map_extract
        return map_extract[self.__c2a(-radius) : self.__c2a(radius) + 1, self.__c2a(-radius) : self.__c2a(radius) + 1]

    def map_opti(self):
        if self.RADIUS > 1 and np.all(self.map[-1] == '') and np.all(self.map[0] == '') and np.all(self.map[:,0] == '') and np.all(self.map[:,-1] == ''):
            self.reshape(self.RADIUS-1)
            self.map_opti()