import matplotlib
# Must use 'Agg' since we are running matplotlib in a QThread background thread
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
import pandas as pd
import numpy as np
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

# Cache directory and graph output path
CACHE_DIR = Path(__file__).parent.parent.parent / 'f1_cache'
GRAPH_PATH = Path(__file__).parent.parent / 'telemetry_graph.png'


class TelemetryThread(QThread):
    # QThread to load telemetry data in the background and plot it with matplotlib
    finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)

    def __init__(self, year: int = 2024, gp: str = 'Belgian Grand Prix', session_type: str = 'R'):
        super().__init__()
        self.year = year
        self.gp = gp
        self.session_type = session_type

    def run(self):
        try:
            print("Fetching telemetry data...")
            self.status_updated.emit('Loading FastF1 session data...')
            
            # Fetch telemetry dataframe and fastest lap info
            df, driver, lap_time = self._fetch_telemetry()
            
            self.status_updated.emit('Generating chart...')
            self._render_chart(df, driver, lap_time)
            
            # Send file path back to UI
            self.finished.emit(str(GRAPH_PATH))
            print("Finished generating telemetry!")
        except ImportError:
            # Fallback if fastf1 is not installed (e.g. offline testing)
            print("FastF1 not found. Using demo graph instead.")
            self.status_updated.emit('FastF1 not found — generating demo chart...')
            self._render_demo_chart()
            self.finished.emit(str(GRAPH_PATH))
        except Exception as e:
            print(f"Error in telemetry thread: {e}")
            self.error_occurred.emit(str(e))

    def _fetch_telemetry(self):
        import fastf1
        
        # Create cache directory if it's missing
        if not CACHE_DIR.exists():
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(CACHE_DIR))

        # Fetch GP session data
        session = fastf1.get_session(self.year, self.gp, self.session_type)
        session.load(telemetry=True, laps=True)

        # Get fastest lap details
        fastest = session.laps.pick_fastest()
        driver = fastest['Driver']
        
        # Clean up lap time text
        lap_time = 'N/A'
        if pd.notna(fastest['LapTime']):
            parts = str(fastest['LapTime']).split('.')
            if len(parts) >= 2:
                lap_time = parts[-2]
            else:
                lap_time = str(fastest['LapTime'])
        
        # Pull speed, throttle, and brake profiles
        car_data = fastest.get_car_data().add_distance()

        # Build dataframe
        df = pd.DataFrame({
            'Distance_m': car_data['Distance'],
            'Speed_kmh': car_data['Speed'],
            'Throttle_pct': car_data['Throttle'],
            'Brake_pct': car_data['Brake'].astype(int) * 100
        })
        return df, driver, lap_time

    def _render_chart(self, df: pd.DataFrame, driver: str, lap_time: str):
        # Configure matplotlib style
        mplstyle.use('dark_background')
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True, facecolor='#0f0f0f')
        fig.subplots_adjust(hspace=0.08, left=0.08, right=0.97, top=0.92, bottom=0.08)

        # Speed plot (cyan)
        axes[0].plot(df['Distance_m'], df['Speed_kmh'], color='#00d2ff', linewidth=1.5)
        axes[0].fill_between(df['Distance_m'], df['Speed_kmh'], alpha=0.08, color='#00d2ff')
        axes[0].set_ylabel('Speed (km/h)', color='#aaaaaa', fontsize=10)
        axes[0].set_title(
            f'Spa 2024 — Fastest Race Lap  |  Driver: {driver}  |  Time: {lap_time}',
            color='white', fontsize=12, fontweight='bold', pad=12
        )

        # Throttle plot (green)
        axes[1].plot(df['Distance_m'], df['Throttle_pct'], color='#00e676', linewidth=1.5)
        axes[1].fill_between(df['Distance_m'], df['Throttle_pct'], alpha=0.08, color='#00e676')
        axes[1].set_ylabel('Throttle (%)', color='#aaaaaa', fontsize=10)
        axes[1].set_ylim(-5, 110)

        # Brake plot (red)
        axes[2].plot(df['Distance_m'], df['Brake_pct'], color='#e10600', linewidth=1.5)
        axes[2].fill_between(df['Distance_m'], df['Brake_pct'], alpha=0.15, color='#e10600')
        axes[2].set_ylabel('Brake (%)', color='#aaaaaa', fontsize=10)
        axes[2].set_xlabel('Distance (m)', color='#aaaaaa', fontsize=10)
        axes[2].set_ylim(-5, 110)

        # Styling margins and grid lines
        for ax in axes:
            ax.set_facecolor('#111111')
            ax.tick_params(colors='#666666', labelsize=9)
            ax.grid(True, alpha=0.15, color='#444444')
            for spine in ax.spines.values():
                spine.set_color('#333333')

        # Save to local PNG
        plt.savefig(str(GRAPH_PATH), dpi=120, bbox_inches='tight', facecolor='#0f0f0f')
        plt.close(fig)

    def _render_demo_chart(self):
        # Generate dummy data for testing without FastF1
        mplstyle.use('dark_background')
        
        dist = np.linspace(0, 7000, 500)
        speed = np.clip(200 + 80 * np.sin(dist / 500) + 20 * np.random.randn(500), 60, 340)
        throttle = np.clip(90 - 40 * np.abs(np.sin(dist / 300)), 0, 100)
        brake = np.clip(60 * np.abs(np.sin(dist / 300)) - 30, 0, 100)

        fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True, facecolor='#0f0f0f')
        fig.subplots_adjust(hspace=0.08, left=0.08, right=0.97, top=0.92, bottom=0.08)

        plots = [
            (speed, '#00d2ff', 'Speed (km/h)'),
            (throttle, '#00e676', 'Throttle (%)'),
            (brake, '#e10600', 'Brake (%)')
        ]

        for i in range(3):
            ax = axes[i]
            data, color, label = plots[i]
            ax.plot(dist, data, color=color, linewidth=1.5)
            ax.set_ylabel(label, color='#aaaaaa')
            ax.set_facecolor('#111111')
            ax.tick_params(colors='#666666')
            ax.grid(True, alpha=0.15, color='#444444')
            for spine in ax.spines.values():
                spine.set_color('#333333')

        axes[0].set_title('Demo Telemetry (install FastF1 for real data)', color='#ff8c00', fontsize=12)
        axes[2].set_xlabel('Distance (m)', color='#aaaaaa')

        plt.savefig(str(GRAPH_PATH), dpi=120, bbox_inches='tight', facecolor='#0f0f0f')
        plt.close(fig)
