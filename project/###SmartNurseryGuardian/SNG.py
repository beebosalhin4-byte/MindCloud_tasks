import tkinter as tk
from tkinter import ttk
import vlc
from datetime import datetime
import threading
import time
import random
from ctypes import windll
from subprocess import call
import CombinedScript as cs
import serial
from PIL import Image, ImageTk
from tkinter import messagebox

#serial connection
stm = serial.Serial("COM5", 115200,timeout=1)
# Enable system DPI awareness (Windows 10/11) (to avoid making the GUI blurry or pixelated)
windll.shcore.SetProcessDpiAwareness(1)
class SNG:
    def __init__(self,root):
        self.r=root #this is the root , probs the whole gui if you would
        self.r.title("Smart Nursery Guardian") 
        self.r.geometry("1500x1100") #I chose those two numbers for absolutely no reason , will change them later
        self.r.minsize(1280,720)#as well as this one lol
        self.parameters = {"temperature": tk.StringVar(value="27.0 °C"),    
                      "motion": tk.StringVar(value="still"),
                      "baby_state": tk.StringVar(value="Sleeping"),
                      "light": tk.StringVar(value="Bright"),
                      "gas": tk.StringVar(value="Safe"),
                      "fan": tk.StringVar(value="Half Speed"),
                      "servo": tk.StringVar(value="Stopped"),
                      "connection": tk.StringVar(value="Connected"),
                      "cry": tk.StringVar(value="No cry detected"),
                      "classification": tk.StringVar(value="—"),}
        # as the name suggests , the parameters that determine the outcome
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Card.TFrame", relief="solid", borderwidth=1)
        style.configure("CardTitle.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Value.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Small.TLabel", font=("Segoe UI", 9))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        self.builder()
        self.update_clock()
        
        self.start_audio_thread()
    def builder(self): #a big chunk of the interface
        status=ttk.Frame(self.r,padding=(25,5)) 
        status.pack(fill="x")
        ttk.Label(status, text=" | Serial: BlackPill",style="Small.TLabel").pack(side="left")
        ttk.Separator(self.r).pack(fill="x", padx=2, pady=8)
        self.clock = ttk.Label(status, text="")
        self.clock.pack(side="right", pady=(10, 0))
        content = ttk.Frame(self.r, padding=(22, 8))
        content.pack(fill="both", expand=False)
        left = ttk.Frame(content)
        left.pack( fill="both", expand=False, padx=(0, 10))
        ttk.Label(left, text="Live Monitoring",font=("Segoe UI", 16, "bold")).pack(anchor='center', pady=(0, 10))
        cards = ttk.Frame(left)
        cards.pack(fill="x")

        self.make_card(cards, 0, 0, "Temperature", self.parameters["temperature"], "Thermistor")
        self.make_card(cards, 1, 0, "Motion state", self.parameters["motion"])
        self.make_card(cards, 0, 1, "Room Light", self.parameters["light"], "LDR")
        self.make_card(cards, 1, 1, "Gas / Smoke", self.parameters["gas"], "Gas sensor")
        state = ttk.LabelFrame(left, text="System State", padding=14)
        state.pack(fill="x", pady=12)
        rows = [
            ("Baby state", "baby_state"),
            ("Cry detection", "cry"),
            ("ML classification", "classification"),
            ("Cooling fan", "fan"),
            ("Servo", "servo"),
        ]
        for i, (label, key) in enumerate(rows):
            ttk.Label(state, text=label + ":", font=("Segoe UI", 10, "bold")).grid(row=i, column=0, sticky="w", pady=5,padx=70)
            ttk.Label(state, textvariable=self.parameters[key]).grid(row=i, column=1, sticky="w", padx=700, pady=5)
        activity=ttk.Frame(self.r,padding=(25,5)) 
        activity.pack(fill="x") # our log 
        ttk.Label(self.r, text="Log", style="Small.TLabel").pack(anchor='center')
        self.recent_activity = tk.Text(self.r,height=5,width=50,state="disabled")
        self.recent_activity.pack()
    def start_audio_thread(self):
        thread = threading.Thread(target=self.audio_worker,daemon=True)
        thread.start()
    def audio_worker(self):
        while True:                 #might crash your whole device if u use a sample audio 
            time.sleep(5)
            result = cs.AudioML(log_callback=self.add_activity).strip()
            self.r.after(0,self.update_audio_result,result)
    def update_audio_result(self, result):
        if result != "N":
            self.parameters["classification"].set(result)
            self.parameters["cry"].set("Cry detected")
            self.parameters["Baby state"].set("Awake")
            stm.write("CRY_DETECTED\n".encode())
            stm.write("SERVO_START\n".encode())
            self.add_activity("Cry DETECTED !!!!!!!!")
        if result == "hungry":
            self.Hungry()
        elif result == "tired":
            self.tired()
        else:
            self.parameters["classification"].set("—")
            stm.write("CRY_ENDED\n".encode())
            stm.write("BUZZER_OFF\n".encode())
            stm.write("SERVO_STOP\n".encode())
            self.parameters["Baby state"].set("Sleeping")
            self.parameters["cry"].set("No cry detected")
    def start_serial(self):
        thread = threading.Thread(target=self.serial_worker,daemon=True)
        thread.start()
    def serial_worker(self):
        if stm.in_waiting:
            message = stm.readline().decode().strip()
            if message.startswith("TEMP:"):
                self.parameters["temperature"].set(str(float(message[5:])))
                if float(message[5:]) > 30 :
                    self.parameters["fan"].set("Full Speed")
                elif float(message[5:]) > 25 :
                    self.parameters["fan"].set("Half Speed")
                else:
                    self.parameters["fan"].set("Off")      
            elif message == "GAS_ALERT":
                self.parameters["gas"].set("Not Safe")
                self.r.after(0,self.add_activity,"GAS/SMOKE DETECTED")
                self.r.after(0,self.save_the_baby)
            elif message == "BABY_AWAKE":
                self.parameters["motion"].set("moving")
            elif message == "BABY_ASLEEP":
                            self.parameters["motion"].set("still")                                
    def add_activity(self,message=""):
        try:
            if self.recent_activity.winfo_exists():
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.recent_activity.config(state="normal")
                self.recent_activity.insert("end",f"[{timestamp}] {message}" + "\n")
                self.recent_activity.see("end")  # automatically scroll down
                self.recent_activity.config(state="disabled")
        except tk.TclError:
            pass
    def update_clock(self):
        self.clock.config(text=datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
        self.r.after(1000, self.update_clock)
    def tired(self):
        stm.write("BUZZER_ON\n".encode())
        messagebox.showinfo("Attention", "Your child is tired , Check on your kid")
        pass 
    def Hungry(self):    
        vidr = tk.Toplevel(self.r)
        vidr.title("Hungry_kiddo")
        vidr.attributes('-fullscreen', True)
        vidr.minsize(1280,720)
        vidr.bind('<Escape>', lambda e: vidr.attributes('-fullscreen', False))
        vidframe = tk.Frame(vidr)
        vidframe.pack(fill=tk.BOTH, expand=True)
        vidr.update_idletasks()
        instance = vlc.Instance()
        player = instance.media_player_new()
        player.set_hwnd(vidframe.winfo_id())
        list_player = instance.media_list_player_new()
        list_player.set_media_player(player)  # <-- links the two together
        media_list = instance.media_list_new()
        media_list.add_media(instance.media_new("video.mp4"))
        list_player.set_media_list(media_list)
        list_player.set_playback_mode(vlc.PlaybackMode.loop)
        list_player.play()
        if(self.parameters["cry"] == "No cry detected"):
            vidr.destroy()

    def save_the_baby(self):  #SNG: 1 , Linsey Clancy : -3
        window = tk.Toplevel(self.r)
        window.title("Image")
        image = Image.open("image.png")
        image = ImageTk.PhotoImage(image)
        label = tk.Label(window, image=image)
        label.pack()
        label.image = image
        call(["python" , "tele.py"])
    def check_connection(self):
         pass
    def make_card(self,parent, col, row, title, variable, subtitle):
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        parent.columnconfigure(col, weight=1)
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor='center')
        ttk.Label(card, textvariable=variable, style="Value.TLabel").pack(anchor='center', pady=(8, 2))
        ttk.Label(card, text=subtitle, style="Small.TLabel").pack(anchor='center')
#will be changed once everything is assembled
#there should be a function that gets called here that checks if the thing is connected , if it isn't it should return 0
# now the display is over , let's cut to action
root = tk.Tk()
app = SNG(root)
app.r.mainloop()