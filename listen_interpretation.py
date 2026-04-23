import os
import ast
from pathlib import Path

try:
    import mido
except ImportError:
    print("❌ 缺少 mido 模組，請執行: pip install mido")
    exit()

def listen_to_senior_format(txt_path, midi_path):
    """
    將對齊後的 interpretation 文字檔轉換為 MIDI 試聽檔。
    學長格式定義: [index, status, pitch, beat, time, vel]
    """
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content: 
                return
            # 使用 ast.literal_eval 安全地解析 Python 列表結構
            data = list(ast.literal_eval(content))

        # 🛠️ 關鍵修復：處理 NoneType 並確保 time 是有效數字
        # 我們必須確保 event[4] (time) 不是 None 且大於 0
        valid_events = []
        for e in data:
            if len(e) >= 6:
                time_val = e[4]
                # 只有當時間不是 None 且轉換為 float 後大於 0 時才視為成功配對的音符
                if time_val is not None:
                    try:
                        if float(time_val) > 0:
                            valid_events.append(e)
                    except (ValueError, TypeError):
                        continue

        if not valid_events:
            print(f"⚠️ {os.path.basename(txt_path)} 無有效配對音符，跳過。")
            return

        # 依照時間戳記 (event[4]) 先後排序，避免 MIDI 順序混亂
        valid_events.sort(key=lambda x: float(x[4]))

        # 💡 裁切空白：將整段音樂的時間軸歸零到第一個音
        start_time = float(valid_events[0][4])

        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        last_time_sec = 0.0
        for event in valid_events:
            # 格式：index[0], status[1], pitch[2], beat[3], time[4], vel[5]
            status, pitch, original_time, vel = event[1], event[2], event[4], event[5]
            
            # 計算平移後的時間 (秒)
            shifted_time = float(original_time) - start_time
            
            # MIDI 使用 Delta Time (與上一個事件的間隔時間)
            delta_sec = shifted_time - last_time_sec
            if delta_sec < 0: 
                delta_sec = 0
            
            # 將秒數轉換為 MIDI Ticks (假設 480 PPQ, 這裡用 960 作為較細緻的採樣)
            delta_ticks = int(round(delta_sec * 960))

            # 判斷 Note On 或 Note Off
            # MIDI 標準：144 為 Note On, 128 為 Note Off
            if status == 144 and vel > 0:
                msg_type = 'note_on'
            else:
                msg_type = 'note_off'
                
            track.append(mido.Message(msg_type, note=int(pitch), velocity=int(vel), time=delta_ticks))
            
            # 更新基準時間
            last_time_sec = shifted_time

        mid.save(midi_path)
        print(f"🎧 產出成功: {os.path.basename(midi_path)}")
        
    except Exception as e:
        print(f"❌ 處理 {os.path.basename(txt_path)} 時發生錯誤: {e}")

def main():
    # 設定實驗數據目錄
    search_dirs = [
        'data_management2026/202412 Experiments/20241217',
        'data_management2026/202412 Experiments/20241220',
    ]
    
    print("🎵 開始將 Interpretation 轉換為去空白的 MIDI 試聽檔...\n")
    
    for d in search_dirs:
        dir_path = Path(d)
        if not dir_path.exists():
            print(f"找不到路徑: {d}")
            continue
            
        # 尋找所有以 extracted_ 開頭的對齊結果檔 (這是你上一動產出的檔名)
        files = list(dir_path.glob('extracted_*.txt'))
        
        # 如果你原本的檔名是 interpretation_ 開頭，請改用下面這行
        if not files:
            files = list(dir_path.glob('interpretation_*.txt'))

        for f_path in files:
            # 產出的 MIDI 檔名：加上 _listen 字樣方便區分
            midi_name = f_path.stem + "_listen.mid"
            midi_path = f_path.parent / midi_name
            listen_to_senior_format(str(f_path), str(midi_path))

    print("\n✨ 轉換完畢！快去資料夾聽聽看吧！")

if __name__ == '__main__':
    main()