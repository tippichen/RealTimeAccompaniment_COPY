import time
import mido
import ast

# 檔案路徑
file_path = r"C:\Users\ychen\Desktop\Lab\kit學長\RealTimeAccompaniment_COPY\SMC2024\data\9_4\inputmsglog.txt"

def play_input_log(path):
    try:
        # 1. 讀取並解析檔案內容
        with open(path, 'r') as f:
            # 檔案內容通常是 Python list 格式的字串，使用 ast.literal_eval 安全解析
            data = ast.literal_eval(f.read())
        
        # 2. 獲取 MIDI 輸出埠
        output_names = mido.get_output_names()
        if not output_names:
            print("找不到 MIDI 輸出裝置。請確認已開啟音源軟體（如 GarageBand）或系統合成器。")
            return
            
        with mido.open_output(output_names[0]) as outport:
            print(f"播放檔案: {path}")
            print(f"使用輸出裝置: {output_names[0]}")

            # 3. 數據前處理
            # 根據論文，格式為 ['Device', Status, Note, Velocity, Timestamp]
            # 過濾掉非 Keyboard 訊息並按時間戳排序 [cite: 139, 143]
            events = [e for e in data if isinstance(e, list) and len(e) >= 5]
            events.sort(key=lambda x: x[4])

            if not events:
                print("檔案中沒有有效的 MIDI 事件。")
                return

            start_real_time = time.time()
            first_event_time = events[0][4]

            # 4. 播放迴圈
            for event in events:
                _, status, note, velocity, timestamp = event
                
                # 計算與第一顆音符的相對時間差，精確控制播放節奏 [cite: 191]
                target_time = start_real_time + (timestamp - first_event_time)
                wait_time = target_time - time.time()

                if wait_time > 0:
                    time.sleep(wait_time)

                # 解析 Status (144: Note On, 128: Note Off) [cite: 64, 72]
                msg_type = 'note_on' if status == 144 else 'note_off'
                
                # 如果是 Note Off 但力度為 0 以外的值，某些合成器會需要處理
                # 此處依照標準 MIDI 協定發送
                msg = mido.Message(msg_type, note=note, velocity=velocity)
                outport.send(msg)

            print("播放完畢。")

    except FileNotFoundError:
        print(f"錯誤：找不到檔案，請檢查路徑是否正確。\n目前路徑：{path}")
    except Exception as e:
        print(f"發生非預期錯誤：{e}")

if __name__ == "__main__":
    play_input_log(file_path)