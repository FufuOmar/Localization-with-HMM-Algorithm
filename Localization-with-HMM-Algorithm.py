import numpy as np
from enum import Enum

class Cell:
    def __init__(self, isWall: bool, prob: float):
        self.isWall = isWall
        self.posterior = prob
        self.prior = prob
        pass

#Globals
class Direction(Enum):
    NORTH = "North"
    SOUTH = "South"
    EAST = "East"
    WEST = "West"

map = []

grid = [
    [0,0,1,1,1,1,0],
    [0,0,0,1,1,1,1],
    [1,0,0,0,0,1,1],
    [1,1,0,0,0,1,1],
    [1,1,1,0,0,0,1],
    [0,1,1,1,0,0,0]
]
location_probability = [
    [5.00,5.00,0.00,0.00,0.00,0.00,5.00],
    [5.00,5.00,5.00,0.00,0.00,0.00,0.00],
    [0.00,5.00,5.00,5.00,5.00,0.00,0.00],
    [0.00,0.00,5.00,5.00,5.00,0.00,0.00],
    [0.00,0.00,0.00,5.00,5.00,5.00,0.00],
    [5.00,0.00,0.00,0.00,5.00,5.00,5.00]
]

def sensing(W: bool, N: bool, E: bool, S: bool):
    z = [W,N,E,S]
    total = 0
    for i in range(len(map)):
        for j in range(len(map[i])):
            if map[i][j].isWall: # Its a wall
                continue
            # Calculating Unnormalized Posteriors P(z|s)*prior
            west, north, east, south = check_surrounding(i,j,z)
            map[i][j].posterior = west * north * east * south * map[i][j].prior
            total += map[i][j].posterior
    # Normalize (divide posterior by sum)
    for i in range(len(map)):
        for j in range(len(map[i])):
            if map[i][j].isWall: # Its a wall
                continue
            map[i][j].posterior = map[i][j].posterior / total
            map[i][j].prior = map[i][j].posterior
    print(f"Filtering after Evidence [{W},{N},{E},{S}]")
    print_probabilties()
           
def check_surrounding(i,j,z):
    wall: bool
    #West
    if j - 1 < 0:
        wall = True
    elif map[i][j-1].isWall:
        wall = True
    else:
        wall = False
    west = probability_sensing(z[0], wall)
    #North
    if i - 1 < 0:
        wall = True
    elif map[i-1][j].isWall:
        wall = True
    else:
        wall = False
    north = probability_sensing(z[1], wall)
    #East
    if j + 1 > len(grid[0]) - 1:
        wall = True
    elif map[i][j+1].isWall:
        wall = True
    else:
        wall = False
    east = probability_sensing(z[2], wall)
    #South
    if i + 1 > len(grid) - 1:
        wall = True
    elif map[i+1][j].isWall:
        wall = True
    else:
        wall = False
    south = probability_sensing(z[3], wall)
    return west, north, east, south
    

def probability_sensing(senses: bool, actual: bool):
    #If the robot senses a wall and theres actually a wall
    if senses == 1 and actual == 1:
        return .9
    #If the robot senses a open space and theres actually a wall (made mistake)
    if senses == 0 and actual == 1:
        return .1
    #If the robot senses a open space and theres actually a open space
    if senses == 0 and actual == 0:
        return .95
    if senses == 1 and actual == 0:
        return .05
    return -1 # Should never reach here

def moving(direction: Direction):
    if direction == Direction.NORTH:
        # Move north
        print("Moving North")
    return


def print_probabilties():
    for row in map:
        for element in row:
            if element.posterior == 0:
                print("####", end="    ")
            else:
                print(f"{element.posterior*100:.2f}", end="    ")
        print()


def main():
    direction = Direction
    for i in range(len(grid)):
        row = []
        for j in range(len(grid[0])):
            is_wall = (grid[i][j] == 1)
            prob = location_probability[i][j]/100
            row.append(Cell(is_wall, prob))
        map.append(row)
    print("Initial Location Probablilities")
    print_probabilties()
    sensing(0,0,0,0)
    moving(direction.NORTH)


if __name__ == "__main__":
    main()