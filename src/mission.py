import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import contextily as cx
from environment import create_mission_map
from algorithms import astar
from mission_manager import MissionManager
from scipy.ndimage import distance_transform_edt # type: ignore

class RavenGCS_EliteV99:
    def __init__(self, size=100):
        self.size = size
        self.grid = create_mission_map(size)
        
        self.start = (5, 5) 
        self.manager = MissionManager()
        self.running = True
        
        
        radar_mask = np.where(self.grid == 2, 0, 1)
        self.dist_map = np.asarray(distance_transform_edt(radar_mask)).astype(float)
        
        # Ankara / TUSAŞ Bölgesi - Genişletilmiş Görünüm Alanı
        self.west, self.south = 3627000.0, 4842000.0
        self.east, self.north = 3638000.0, 4853000.0
        self.extent = (self.west, self.east, self.south, self.north)

        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(12, 12))
        # HUD üstte, Harita altta
        self.gs = self.fig.add_gridspec(2, 1, height_ratios=[1, 5], hspace=0.15)
        self.ax_hud = self.fig.add_subplot(self.gs[0])
        self.ax_map = self.fig.add_subplot(self.gs[1])
        
        self.fig.canvas.mpl_connect('close_event', self.on_close)
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.draw_interface()

    def on_close(self, event): self.running = False

    def get_real_coords(self, row, col):
        rx = self.west + (float(col) * (self.east - self.west) / self.size)
        ry = self.north - (float(row) * (self.north - self.south) / self.size)
        return rx, ry

    def draw_interface(self, path=None, current_idx=0, warning="", status="NORMAL", goal_real=None):
        if not self.running: return
        self.ax_map.clear()
        self.ax_hud.clear()
        
        # ✅ Harita Arka Planı
        self.ax_map.imshow(self.grid, extent=self.extent, alpha=0.0)
        
        # ✅ PYLANCE HATASINI ÇÖZEN GÜVENLİ ERİŞİM
        try:
            # 
            esri_source = getattr(cx.providers, 'Esri', None)
            if esri_source and hasattr(esri_source, 'WorldImagery'):
                cx.add_basemap(self.ax_map, source=esri_source.WorldImagery, crs="EPSG:3857")
            else:
                cx.add_basemap(self.ax_map, source="Esri.WorldImagery", crs="EPSG:3857")
        except Exception:
            # Fallback URL (İnternet/Kütüphane sorunu için yedek)
            cx.add_basemap(self.ax_map, source="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", crs="EPSG:3857")
        
        # Eksen Bilgileri
        self.ax_map.tick_params(axis='both', colors='cyan', labelsize=8)
        self.ax_map.set_xlabel("EASTING (m)", color='cyan', fontsize=8)
        self.ax_map.set_ylabel("NORTHING (m)", color='cyan', fontsize=8)

        # Radarlar ve Risk Alanları
        radars = np.argwhere(self.grid == 2)
        for r in radars:
            rx, ry = self.get_real_coords(r[0], r[1])
            self.ax_map.plot(rx, ry, 'ro', markersize=6)
            self.ax_map.add_patch(patches.Circle((rx, ry), 500, color='red', fill=True, alpha=0.25))

        # Üs Konumu
        sx, sy = self.get_real_coords(self.start[0], self.start[1])
        self.ax_map.plot(sx, sy, 'cp', markersize=16, markeredgecolor='white')

        curr_x, curr_y, fuel_lvl, dist_km = sx, sy, 100.0, 0.0
        
        if path is not None:
            path_array = np.array(path[:current_idx+1])
            real_pts = np.array([self.get_real_coords(p[0], p[1]) for p in path_array])
            # Rota Çizgisi (Neon Yeşil)
            self.ax_map.plot(real_pts[:, 0], real_pts[:, 1], color='lime', linewidth=3)
            curr_x, curr_y = real_pts[-1]
            fuel_lvl = 100.0 - (current_idx * 0.58) # Yakıt tüketimi
            dist_km = (current_idx * 150) / 1000.0
            self.ax_map.plot(curr_x, curr_y, 'w^', markersize=14, markeredgecolor='lime')

        # --- GELİŞMİŞ HUD PANELİ ---
        self.ax_hud.axis('off')
        # Yakıt %5 altına inerse veya hata durumunda panel kırmızı yanar
        bg = 'red' if (fuel_lvl < 5.0 or status == "ALERT") else '#0a0a0a'
        g_txt = f"{goal_real[0]:.0f}/{goal_real[1]:.0f}" if goal_real else "---"
        
        hud_info = (
            f"RAVEN-1 STRATEJİK KOMUTA MERKEZİ | ANKARA-TUSAŞ SEKTÖRÜ\n"
            f"ÜS: {sx:.0f}/{sy:.0f} | KONUM: {curr_x:.0f}/{curr_y:.0f} | HEDEF: {g_txt}\n"
            f"MESAFE: {dist_km:.2f} KM | YAKIT: %{max(0, fuel_lvl):.1f} | REZERV: %7 | {warning if warning else 'HAZIR'}"
        )
        self.ax_hud.text(0.5, 0.5, hud_info, color='lime', fontsize=11, ha='center', va='center',
                         family='monospace', fontweight='bold', bbox=dict(facecolor=bg, edgecolor='cyan', alpha=0.9, pad=12))

        self.ax_map.set_xlim(self.west, self.east)
        self.ax_map.set_ylim(self.south, self.north)
        plt.draw()

    def on_click(self, event):
        if event.inaxes != self.ax_map: return
        col = int((event.xdata - self.west) * self.size / (self.east - self.west))
        row = int((self.north - event.ydata) * self.size / (self.north - self.south))
        
        
        path = astar(self.grid, self.start, (row, col), dist_map=self.dist_map)
        
        if path:
            path_len = len(path)
            # %7 Rezerv ve %5 Kritik limit hesabı
            needed = (path_len * 2 * 0.58) + 7.0
            if needed > 100.0:
                self.draw_interface(warning=f"⚠️ MENZİL DIŞI: %7 REZERV İHLALİ! (GEREKEN: %{needed:.1f})", 
                                    status="ALERT", goal_real=(event.xdata, event.ydata))
            else:
                self.animate_mission(path, (event.xdata, event.ydata))
        else: 
            self.draw_interface(warning="❌ ROTA BLOKE: RADAR/ENGEL!", status="ALERT")

    def animate_mission(self, path, goal_real):
        # ⚡ 
        step = 10 
        for i in range(0, len(path), step):
            if not self.running: break
            self.draw_interface(path=path, current_idx=i, warning="🚀 OPERASYON DEVAM EDİYOR", goal_real=goal_real)
            plt.pause(0.001)
        if self.running:
            self.draw_interface(path=path, current_idx=len(path)-1, warning="✅ HEDEFE VARIŞ BAŞARILI.", goal_real=goal_real)
            self.manager.save_mission(path[-1], path, self.grid)

if __name__ == "__main__":
    gcs = RavenGCS_EliteV99(size=100)
    plt.show()