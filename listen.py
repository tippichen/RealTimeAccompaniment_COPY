import os
import ast
try:
    import mido
except ImportError:
    print("❌ 找不到 mido 套件！請先在終端機執行: pip install mido")
    exit()

def txt_to_midi_offset(txt_path, midi_path):
    """處理索引偏移的原始 Log (2345 對應 status, pitch, velocity, time)"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return
            data = list(ast.literal_eval(content))

        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        ticks_per_second = 960
        last_time = 0.0

        for item in data:
            # 依據你的描述：原本的 1234 變成了 2345
            # 代表 index 0 可能是序號或其他數據，我們要跳過它
            if len(item) >= 5:
                status = item[1]   # 原本的 1 (Status)
                pitch = item[2]    # 原本的 2 (Pitch)
                velocity = item[3] # 原本的 3 (Velocity)
                time = item[4]     # 原本的 4 (Time)
            else:
                continue

            delta_sec = time - last_time
            if delta_sec < 0:
                delta_sec = 0

            delta_ticks = int(round(delta_sec * ticks_per_second))
            msg_type = 'note_on' if (status in (144, 1) and velocity > 0) else 'note_off'

            track.append(mido.Message(msg_type, note=pitch, velocity=velocity, time=delta_ticks))
            last_time = time

        mid.save(midi_path)
        print(f"🎧 成功產生試聽檔: {os.path.basename(midi_path)}")
        
    except Exception as e:
        print(f"❌ 處理失敗: {e}")

def main():
    # 🎯 你的目標檔案完整路徑
    target_file = r'C:\Users\tippi\SynologyDrive\Tsing_Hua\third_grade\project\RealTimeAccompaniment_COPY\logs\debussy1_1\inputmsglog.txt'
    
    if not os.path.exists(target_file):
        print(f"❌ 找不到檔案，請檢查路徑是否正確：\n{target_file}")
        return

    # 產生的新檔名
    midi_path = target_file.replace('.txt', '_corrected_listen.mid')

    print(f"🎵 正在處理偏移格式的 Log: {os.path.basename(target_file)}")
    txt_to_midi_offset(target_file, midi_path)
    print(f"✨ 轉換完畢！檔案存放在：\n{midi_path}")

if __name__ == '__main__':
    main()