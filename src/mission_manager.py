import sqlite3
import json
import numpy as np

class MissionManager:
    def __init__(self, db_name="raven_missions.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        # SQLite 
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Missions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            target_x INTEGER,
                            target_y INTEGER,
                            path_length REAL,
                            fuel_status TEXT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

    def calculate_fuel(self, path, grid):
        # Toplam menzil 120 birim
        total_range = 120.0
        spent_fuel = 0.0
        
        # Radarları tespit et
        radars = np.argwhere(grid == 2)
        
        # Rota üzerindeki her adımı analiz et
        for pos in path:
            x, y = int(pos[0]), int(pos[1])
            step_cost = 1.0 # Temel tüketim
            
            # Radar etki alanı kontrolü: Yakınlık tüketimi artırır
            for r_pos in radars:
                dist = np.sqrt((x - r_pos[0])**2 + (y - r_pos[1])**2)
                if dist < 4.0:
                    step_cost = 2.5 # Manevra maliyeti
                    break
            
            spent_fuel += step_cost

        remaining_fuel = max(0, ((total_range - spent_fuel) / total_range) * 100)
        
        if remaining_fuel > 50:
            status = "GÜVENLİ"
        elif remaining_fuel > 20:
            status = "DİKKAT: DÜŞÜK YAKIT"
        else:
            status = "KRİTİK: ACİL İNİŞ GEREKLİ"
            
        return f"%{remaining_fuel:.1f} ({status})", remaining_fuel > 15

    def save_mission(self, goal, path, grid):
        
        fuel_info, is_safe = self.calculate_fuel(path, grid)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Missions (target_x, target_y, path_length, fuel_status) VALUES (?, ?, ?, ?)",
                       (goal[0], goal[1], len(path), fuel_info))
        conn.commit()
        conn.close()
        
        # JSON Uçuş Planı Çıktısı
        mission_data = {
            "target": goal,
            "waypoints": path,
            "total_distance": len(path),
            "fuel_report": fuel_info
        }
        with open("last_mission_plan.json", "w") as f:
            json.dump(mission_data, f, indent=4)
        
        return fuel_info