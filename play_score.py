import ast
import time
import sys
import os
from rtmidi.midiutil import open_midioutput

# --- 1. MIDI 初始化 ---
port = sys.argv[1] if len(sys.argv) > 1 else None
try:
    midiout, port_name = open_midioutput(port)
except (EOFError, KeyboardInterrupt):
    sys.exit()

# --- 2. 檔案路徑處理 ---
# 預設播放 logs 資料夾下的 outputscore_fixed.txt
file_path = sys.argv[2] if len(sys.argv) > 2 else 'outputscore_fixed.txt'

if not os.path.exists(file_path):
    print(f"找不到檔案：{file_path}")
    sys.exit()

# --- 3. 讀取並修正內容 ---
with open(file_path, 'r') as file:
    content = file.read()
    # 這裡就是解決 ValueError 的關鍵：把 numpy 的型別字串清掉
    content = content.replace('np.float64(', '').replace(')', '')
    
    try:
        full_log = ast.literal_eval(content)
    except Exception as e:
        print(f"解析失敗，請確認檔案內容格式。錯誤：{e}")
        sys.exit()

# 過濾掉包含 'q' 的資訊列
score_data = [item for item in full_log if item[1] != 'q']

print(f'正在播放檔案: {file_path}')
print('音符總數 = ', len(score_data))

# --- 4. 播放邏輯 ---
startTime = time.time()
index = 0
bpm_factor = 1.0  # 調整播放速度，1.0 為原速

try:
    while index < len(score_data):
        currentTime = time.time()
        
        # 取得相對時間位置 (在 score_sort 產出的格式中，位置通常在最後一位)
        event_time_relative = score_data[index][3]
        
        # 目標播放時間 (延遲 1 秒開始播放以確保穩定)
        target_time = startTime + (event_time_relative * bpm_factor) + 1
        
        if target_time <= currentTime:
            status = int(score_data[index][1])
            note = int(score_data[index][2])
            
            # 判斷有無 velocity (第四位)，若無則給 100
            velocity = 100
            
            midiout.send_message([status, note, velocity])
            print(f"[{index}] Status: {status} | Note: {note} | Pos: {event_time_relative:.3f}")
            
            index += 1
        
        # 減少 CPU 負擔並維持 0.1ms 的精確度
        time.sleep(0.0001)

except KeyboardInterrupt:
    print('\n停止播放')

finally:
    print('Done')
    midiout.close_port()