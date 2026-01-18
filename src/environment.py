import numpy as np

def create_mission_map(size=80): # Boyutu ana GCS ile uyumlu 80 yaptık
    grid = np.zeros((size, size))
    # Dağlar/Engeller
    for _ in range(15):
        x, y = np.random.randint(2, size-2), np.random.randint(2, size-2)
        grid[x-1:x+1, y-1:y+1] = 1 
    # Radarları 15
    for _ in range(15):
        x, y = np.random.randint(5, size-5), np.random.randint(5, size-5)
        if grid[x, y] == 0: grid[x, y] = 2 
    return grid