import ast
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import mido

class MatrixMidiPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("SMC2024 Interpretation 播放器")
        self.root.geometry("450x180")
        self.root.resizable(False, False)

        # 狀態變數
        self.events = []
        self.playing = False
        self.is_seeking = False
        self.current_time = 0.0
        self.duration = 0.0
        self.play_index = 0
        self.real_start_time = 0.0

        # 初始化 MIDI 輸出埠 (自動抓取系統預設，例如 Windows GS Wavetable)
        try:
            out_ports = mido.get_output_names()
            self.midi_out = mido.open_output(out_ports[0])
        except Exception as e:
            messagebox.showerror("MIDI 錯誤", "找不到可用的 MIDI 輸出裝置。")
            self.root.destroy()
            return

        self.setup_gui()
        
        # 啟動背景播放執行緒與 GUI 更新迴圈
        self.thread = threading.Thread(target=self.playback_loop, daemon=True)
        self.thread.start()
        self.update_gui_loop()

    def setup_gui(self):
        # 路徑輸入區
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=10, padx=15, fill="x")
        
        tk.Label(frame_top, text="TXT 絕對路徑:").pack(side="left")
        self.path_entry = tk.Entry(frame_top, width=35)
        self.path_entry.pack(side="left", padx=5)
        
        tk.Button(frame_top, text="載入", command=self.load_file).pack(side="left")

        # 時間與進度條區
        frame_middle = tk.Frame(self.root)
        frame_middle.pack(pady=10, padx=15, fill="x")

        self.time_label = tk.Label(frame_middle, text="00:00.00 / 00:00.00", font=("Courier", 10))
        self.time_label.pack()

        self.slider = ttk.Scale(frame_middle, from_=0, to=100, orient="horizontal")
        self.slider.pack(fill="x")
        self.slider.bind("<ButtonPress-1>", self.on_seek_start)
        self.slider.bind("<ButtonRelease-1>", self.on_seek_end)

        # 播放控制區
        frame_bottom = tk.Frame(self.root)
        frame_bottom.pack(pady=5)
        
        self.btn_play = tk.Button(frame_bottom, text="▶ 播放", width=10, state="disabled", command=self.toggle_play)
        self.btn_play.pack()

    def load_file(self):
        path = self.path_entry.get().strip()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw_data = ast.literal_eval(f.read().strip())
            
            parsed_events = []
            active_notes = {}

            for row in raw_data:
                if len(row) < 6: continue
                status, note, time_val, vel = row[1], row[2], row[4], row[5]

                # ==========================================
                # 【關鍵修正】：防禦「砸鋼琴」現象
                # 1. 處理未彈奏/未對齊的幽靈音符 (Note On 時間為 0)
                # ==========================================
                if status == 144 and (time_val == 0 or time_val == 0.0 or time_val is None):
                    continue # 略過這顆音符，不排入播放序列

                # ==========================================
                # 2. 正常 Note On 的數值修正
                # ==========================================
                if status == 144:
                    if vel <= 1: 
                        vel = 80 # 強制放大 AI 或異常的過小力度
                    active_notes[note] = time_val

                # ==========================================
                # 3. 處理缺失的 Note Off (避免延音無限長)
                # ==========================================
                elif status == 128 and (time_val == 0 or time_val == 0.0 or time_val is None):
                    if note in active_notes:
                        time_val = active_notes[note] + 0.3 # 給予預設 0.3 秒的長度
                    else:
                        continue # 如果前面沒紀錄到 Note On，這個 Note Off 直接無效化

                # 將過濾與修正後的音符加入清單
                parsed_events.append({
                    'status': status,
                    'note': note,
                    'time': time_val,
                    'vel': vel
                })

            # 根據時間重新排序
            parsed_events.sort(key=lambda x: x['time'])

            # 正規化時間 (讓第一顆真實音符從 0 秒開始)
            if parsed_events:
                start_time = parsed_events[0]['time']
                for ev in parsed_events:
                    ev['time'] -= start_time

            self.events = parsed_events
            self.duration = parsed_events[-1]['time'] if parsed_events else 0

            # 重置播放器狀態
            self.slider.config(to=self.duration)
            self.current_time = 0.0
            self.play_index = 0
            self.playing = False
            self.btn_play.config(text="▶ 播放", state="normal")
            self.update_time_label()
            messagebox.showinfo("成功", f"載入並過濾完成！\n有效事件數: {len(self.events)}\n總時長: {self.duration:.2f} 秒")

        except Exception as e:
            messagebox.showerror("載入失敗", f"無法讀取或解析檔案:\n{e}")

    def toggle_play(self):
        if not self.events: return
        self.playing = not self.playing
        if self.playing:
            self.btn_play.config(text="⏸ 暫停")
            self.real_start_time = time.time() - self.current_time
        else:
            self.btn_play.config(text="▶ 播放")
            self.panic() # 暫停時切斷所有聲音

    def on_seek_start(self, event):
        self.is_seeking = True
        self.panic() # 拉動進度條時靜音，避免破音與殘響

    def on_seek_end(self, event):
        self.current_time = float(self.slider.get())
        # 尋找拉動後對應的陣列 index
        self.play_index = next((i for i, ev in enumerate(self.events) if ev['time'] >= self.current_time), len(self.events))
        self.real_start_time = time.time() - self.current_time
        self.is_seeking = False
        self.update_time_label()

    def panic(self):
        """傳送 All Notes Off (CC 123) 確保沒有延音掛在背景"""
        for channel in range(16):
            self.midi_out.send(mido.Message('control_change', channel=channel, control=123, value=0))

    def playback_loop(self):
        """背景播放執行緒"""
        while True:
            if self.playing and not self.is_seeking:
                self.current_time = time.time() - self.real_start_time
                
                if self.current_time > self.duration:
                    self.playing = False
                    self.current_time = 0.0
                    self.play_index = 0
                    self.root.after(0, lambda: self.btn_play.config(text="▶ 播放"))
                    self.panic()
                    continue

                # 發送當前時間點需要發聲的 MIDI 訊號
                while self.play_index < len(self.events) and self.events[self.play_index]['time'] <= self.current_time:
                    ev = self.events[self.play_index]
                    msg_type = 'note_on' if ev['status'] == 144 else 'note_off'
                    self.midi_out.send(mido.Message(msg_type, note=ev['note'], velocity=int(ev['vel'])))
                    self.play_index += 1

            time.sleep(0.005) # 降低 CPU 負載

    def update_gui_loop(self):
        """定時更新進度條與文字"""
        if self.playing and not self.is_seeking:
            self.slider.set(self.current_time)
            self.update_time_label()
        self.root.after(50, self.update_gui_loop)

    def update_time_label(self):
        cur_m, cur_s = divmod(self.current_time, 60)
        dur_m, dur_s = divmod(self.duration, 60)
        self.time_label.config(text=f"{int(cur_m):02d}:{cur_s:05.2f} / {int(dur_m):02d}:{dur_s:05.2f}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MatrixMidiPlayer(root)
    root.mainloop()