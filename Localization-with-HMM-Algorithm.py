from enum import Enum

# Each grid cell stores whether it is a wall and the probabilities used by HMM updates.
class Cell:
    def __init__(self, isWall: bool, prob: float):
        self.isWall = isWall
        self.posterior = prob   # Belief after incorporating sensor evidence P(s_t | z_1:t)
        self.prior = prob       # Belief before current sensing step (or after previous update)
        self.prediction = 0.00  # Temporary buffer for motion model output
        pass

#Globals
# Cardinal directions for control commands in the motion model.
class Direction(Enum):
    N = "Northward"
    S = "Southward"
    E = "Eastward"
    W = "Westward"

map = []  # 2D matrix of Cell objects built from grid + initial probabilities

# 1 = wall cell (not traversable), 0 = free cell.
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

# Measurement update (Bayes filter):
# 1) Compute unnormalized posterior = P(z_t | s_t) * prior for each free cell
# 2) Normalize so all free-cell probabilities sum to 1
def sensing(W: bool, N: bool, E: bool, S: bool):
    z = [W,N,E,S]  # Sensor reading ordered as [West, North, East, South]
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
           
# For a hypothetical robot location (i, j), infer whether each adjacent side is a wall.
# Then return the per-direction sensing likelihood terms.
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
    

# Sensor model probabilities:
# senses = what robot reports (1 wall, 0 free)
# actual = ground truth in that direction (1 wall, 0 free)
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

# Motion prediction update:
# Applies commanded direction with stochastic drift:
#   straight = 0.75, left drift = 0.15, right drift = 0.10.
# If motion would hit a wall/boundary, that probability "bounces" and stays in place.
def moving(direction: Direction):
    probLeft = .15
    probRight = .1
    probStraight = .75
    if direction == Direction.N:
        # Move north
        print("Moving: N")
        for i in range(len(map)):
            for j in range(len(map)):
                if map[i][j].isWall: # Its a wall
                    continue
                if j - 1 < 0 or map[i][j-1].isWall: # Wall
                    map[i][j].prediction += probLeft * map[i][j].posterior # Drifting left (bounce)
                else:
                    map[i][j-1].prediction += probLeft * map[i][j].posterior # Drifting left
                if j + 1 > len(map[0]) - 1 or map[i][j+1].isWall: # Wall
                    map[i][j].prediction += probRight * map[i][j].posterior # Drifting right (bounce)
                else:
                    map[i][j+1].prediction += probRight * map[i][j].posterior # Drifting right
                if i - 1 < 0 or map[i-1][j].isWall: # Wall
                    map[i][j].prediction += probStraight * map[i][j].posterior # Straight (bounce)
                else:
                    map[i-1][j].prediction += probStraight * map[i][j].posterior # Straight
    if direction == Direction.W:
        print("Moving: W")
        for i in range(len(map)):
            for j in range(len(map[i])):
                if map[i][j].isWall:
                    continue
                # Straight (west)
                if j - 1 < 0 or map[i][j-1].isWall:
                    map[i][j].prediction += probStraight * map[i][j].posterior
                else:
                    map[i][j-1].prediction += probStraight * map[i][j].posterior
                # Left drift (south when moving west)
                if i + 1 > len(map) - 1 or map[i+1][j].isWall:
                    map[i][j].prediction += probLeft * map[i][j].posterior
                else:
                    map[i+1][j].prediction += probLeft * map[i][j].posterior
                # Right drift (north when moving west)
                if i - 1 < 0 or map[i-1][j].isWall:
                    map[i][j].prediction += probRight * map[i][j].posterior
                else:
                    map[i-1][j].prediction += probRight * map[i][j].posterior

    if direction == Direction.E:
        print("Moving: E")
        for i in range(len(map)):
            for j in range(len(map[i])):
                if map[i][j].isWall:
                    continue
                # Straight (east)
                if j + 1 > len(map[0]) - 1 or map[i][j+1].isWall:
                    map[i][j].prediction += probStraight * map[i][j].posterior
                else:
                    map[i][j+1].prediction += probStraight * map[i][j].posterior
                # Left drift (north when moving east)
                if i - 1 < 0 or map[i-1][j].isWall:
                    map[i][j].prediction += probLeft * map[i][j].posterior
                else:
                    map[i-1][j].prediction += probLeft * map[i][j].posterior
                # Right drift (south when moving east)
                if i + 1 > len(map) - 1 or map[i+1][j].isWall:
                    map[i][j].prediction += probRight * map[i][j].posterior
                else:
                    map[i+1][j].prediction += probRight * map[i][j].posterior

    if direction == Direction.S:
        print("Moving: S")
        for i in range(len(map)):
            for j in range(len(map[i])):
                if map[i][j].isWall:
                    continue
                # Straight (south)
                if i + 1 > len(map) - 1 or map[i+1][j].isWall:
                    map[i][j].prediction += probStraight * map[i][j].posterior
                else:
                    map[i+1][j].prediction += probStraight * map[i][j].posterior
                # Left drift (east when moving south)
                if j + 1 > len(map[0]) - 1 or map[i][j+1].isWall:
                    map[i][j].prediction += probLeft * map[i][j].posterior
                else:
                    map[i][j+1].prediction += probLeft * map[i][j].posterior
                # Right drift (west when moving south)
                if j - 1 < 0 or map[i][j-1].isWall:
                    map[i][j].prediction += probRight * map[i][j].posterior
                else:
                    map[i][j-1].prediction += probRight * map[i][j].posterior
    # Commit predicted distribution as the new belief state.
    for row in map:
        for element in row:
            if element.isWall:
                print("####", end="    ")
                continue
            else:
                print(f"{element.prediction*100:.2f}", end="    ")
            element.posterior = element.prediction
            element.prior = element.prediction
            element.prediction = 0.0
        print()





# Utility printer for current belief (in percent) over free cells.
def print_probabilties():
    for row in map:
        for element in row:
            if element.isWall:
                print("####", end="    ")
            else:
                print(f"{element.posterior*100:.2f}", end="    ")
        print()


# Program entry:
# 1) Build world from grid and initial belief
# 2) Alternate sensing and movement to perform localization over time
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
    moving(direction.N)
    sensing(0,0,1,0)
    moving(direction.N)
    sensing(0,1,1,0)
    moving(direction.W)
    sensing(0,1,0,0)
    moving(direction.S)
    sensing(0,0,0,0)

if __name__ == "__main__":
    main()
