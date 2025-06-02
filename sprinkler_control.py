import tkinter as tk
from tkinter import ttk, messagebox
import time
from datetime import datetime
import threading
import json
import os
from opensprinkler_api import OpenSprinklerAPI

class SprinklerControl:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenSprinkler Control System")
        self.root.geometry("800x600")
        
        try:
            # Initialize OpenSprinkler API from config
            self.api = OpenSprinklerAPI.from_config()
            
            # Get refresh interval from config
            with open("config.json", 'r') as f:
                config = json.load(f)
                self.refresh_interval = config['opensprinkler'].get('refresh_interval', 1)
        except FileNotFoundError:
            messagebox.showerror(
                "Configuration Error",
                "config.json not found. Please create it with your OpenSprinkler settings."
            )
            root.destroy()
            return
        except json.JSONDecodeError:
            messagebox.showerror(
                "Configuration Error",
                "config.json is not valid JSON. Please check the format."
            )
            root.destroy()
            return
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to initialize: {str(e)}"
            )
            root.destroy()
            return
        
        # Initialize variables
        self.selected_time = tk.IntVar(value=0)
        self.active_sprinklers = {}
        self.station_names = []
        self.status_check_thread = None
        
        # Create main frames
        self.create_control_frame()
        self.create_display_frame()
        
        # Initialize sprinkler buttons
        self.sprinkler_buttons = {}
        self.load_stations()
        
        # Start status monitoring
        self.start_status_monitoring()




    def create_control_frame(self):
        """Create the frame containing sprinkler controls"""
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create time dial
        self.time_dial = ttk.Scale(
            control_frame,
            from_=0,
            to=180,  # Maximum 3 minutes (180 seconds)
            orient="horizontal",
            variable=self.selected_time,
            command=self.update_time_display
        )
        self.time_dial.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Label for the dial
        ttk.Label(control_frame, text="Duration (seconds):").grid(row=1, column=0, columnspan=2)




    def create_display_frame(self):
        """Create the frame for displaying status messages"""
        display_frame = ttk.Frame(self.root, padding="10")
        display_frame.grid(row=1, column=0, sticky="nsew")
        
        self.display_label = ttk.Label(
            display_frame,
            text="Select duration and press a sprinkler button",
            font=("Arial", 12)
        )
        self.display_label.grid(row=0, column=0, pady=10)





    def load_stations(self):
        """Load station names from OpenSprinkler"""
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.grid(row=2, column=0, sticky="nsew")
        
        # Get station names from API
        self.station_names = self.api.get_station_names()
        
        # Create buttons for each station
        for idx, name in enumerate(self.station_names):
            style = ttk.Style()
            style.configure(f'Station{idx}.TButton', background='white')
            
            btn = ttk.Button(
                button_frame,
                text=name,
                style=f'Station{idx}.TButton',
                command=lambda i=idx, n=name: self.toggle_station(i, n)
            )
            btn.grid(row=idx//2, column=idx%2, padx=5, pady=5)
            self.sprinkler_buttons[idx] = btn




    def update_time_display(self, *args):
        """Update the display when the dial is adjusted"""
        self.display_label.config(
            text=f"Selected Duration: {self.selected_time.get()} seconds"
        )



    def toggle_station(self, station_id, name):
        """Toggle a station on/off"""
        if station_id in self.active_sprinklers:
            # Turn off the station
            if self.api.deactivate_station(station_id):
                del self.active_sprinklers[station_id]
                self.display_label.config(text=f"Turned off {name}")
                self.update_button_colors()
        else:
            # Turn on the station
            duration = self.selected_time.get()
            if duration <= 0:
                self.display_label.config(text="Please select a duration first!")
                return
                
            if self.api.activate_station(station_id, duration):
                self.active_sprinklers[station_id] = time.time() + duration
                self.display_label.config(text=f"Activated {name} for {duration} seconds")
                self.update_button_colors()




    def update_button_colors(self):
        """Update button colors based on station status"""
        try:
            status = self.api.get_station_status()
            for idx, is_active in enumerate(status):
                style = ttk.Style()
                if is_active:
                    style.configure(f'Station{idx}.TButton', background='green')
                else:
                    style.configure(f'Station{idx}.TButton', background='white')
        except Exception as e:
            print(f"Error updating status: {e}")




    def start_status_monitoring(self):
        """Start a thread to monitor station status"""
        def monitor_status():
            while True:
                if self.root.winfo_exists():
                    self.root.after(0, self.update_button_colors)
                time.sleep(self.refresh_interval)
                
        self.status_check_thread = threading.Thread(target=monitor_status)
        self.status_check_thread.daemon = True
        self.status_check_thread.start()




def main():
    root = tk.Tk()
    app = SprinklerControl(root)
    root.mainloop()



if __name__ == "__main__":
    main() 