import time
import numpy as np
from environment import create_mission_map
from algorithms import astar
from scipy.ndimage import distance_transform_edt # type: ignore

def run_test():
    size = 100
    grid = create_mission_map(size)
    start = (5, 5)
    goal = (90, 90)
    
    # ⚡ ÖN HESAPLAMA (GCS'deki gibi)
    radar_mask = np.where(grid == 2, 0, 1)
    dist_map = np.asarray(distance_transform_edt(radar_mask)).astype(float)
    
    start_time = time.time()
    # ✅ dist_map 
    path = astar(grid, start, goal, dist_map=dist_map)
    end_time = (time.time() - start_time) * 1000
    
    print(f"⚡ Hesaplama Süresi: {end_time:.2f} ms")
    if end_time < 15:
        print("🥇 Verimlilik Skoru: ELITE (Extreme Speed)")
    else:
        print("⚠️ Verimlilik Skoru: GELİŞTİRİLMELİ")

if __name__ == "__main__":
    run_test()