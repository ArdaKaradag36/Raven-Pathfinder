import numpy as np
import heapq
from typing import Optional # Pylance hatası çözümü için
from scipy.ndimage import distance_transform_edt # type: ignore

def heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
    return float(np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2))

def astar(grid: np.ndarray, start: tuple[int, int], goal: tuple[int, int], dist_map: Optional[np.ndarray] = None):
    # ✅ HIZIN ANAHTARI: Eğer dışarıdan dist_map gelmişse (GCS'den gelir), EDT hesaplamasını ATLA!
    if dist_map is None:
        radar_mask = np.where(grid == 2, 0, 1)
        dist_map = np.asarray(distance_transform_edt(radar_mask)).astype(float)
    
    neighbors = [(0,1,1.0), (0,-1,1.0), (1,0,1.0), (-1,0,1.0), 
                 (1,1,1.41), (1,-1,1.41), (-1,1,1.41), (-1,-1,1.41)]
    
    close_set = set()
    came_from = {}
    gscore = {start: 0.0}
    fscore = {start: heuristic(start, goal)}
    oheap = []
    heapq.heappush(oheap, (fscore[start], start))
    
    while oheap:
        current = heapq.heappop(oheap)[1]
        if current == goal:
            data = []
            while current in came_from:
                data.append(current)
                current = came_from[current]
            return data[::-1]

        close_set.add(current)
        for i, j, cost in neighbors:
            neighbor = (int(current[0] + i), int(current[1] + j))
            
            if 0 <= neighbor[0] < grid.shape[0] and 0 <= neighbor[1] < grid.shape[1]:
                if grid[neighbor[0], neighbor[1]] == 1: continue
            else: continue
            
            # ✅ O(1) ERİŞİM: Önbelleğe alınmış haritadan direkt veri okuma
            min_dist = float(dist_map[neighbor[0], neighbor[1]])
            
            if min_dist < 5.5: continue 
            
            penalty = 200.0 / (min_dist + 0.1) if min_dist < 8.0 else 0.0
            tentative_g_score = gscore[current] + cost + penalty
            
            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0.0): continue
                
            if tentative_g_score < gscore.get(neighbor, float('inf')):
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score
                fscore[neighbor] = gscore[neighbor] + heuristic(neighbor, goal)
                heapq.heappush(oheap, (fscore[neighbor], neighbor))
                
    return False