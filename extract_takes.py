import xml.etree.ElementTree as ET
import os

def extract_and_group_takes(xml_file, output_dir):
    print(f"\n📂 正在處理專案: {xml_file}")
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    bpm = 120.0
    beat_to_sec = 60.0 / bpm
    
    # 收集所有音符，並標記是哪個人彈的
    all_notes = []
    
    for track_id, human_name in {'1003': 'Human_1', '1006': 'Human_2'}.items():
        track = root.find(f".//TRACK[@id='{track_id}']")
        if track is None: continue
        
        for clip in track.findall(".//MIDICLIP"):
            clip_start = float(clip.get('start', 0))
            clip_offset = float(clip.get('offset', 0))
            
            for note in clip.findall(".//NOTE"):
                if note.get('b') is None or note.get('l') is None: continue
                
                pitch = int(note.get('p'))
                if pitch < 21 or pitch > 108: continue # 濾除幽靈音符
                
                onset = clip_start - clip_offset + (float(note.get('b')) * beat_to_sec)
                offset = onset + (float(note.get('l')) * beat_to_sec)
                velocity = int(note.get('v'))
                
                # 將音符加入總表
                all_notes.append({
                    'player': human_name, 'pitch': pitch, 
                    'velocity': velocity, 'onset': onset, 'offset': offset
                })

    # 依照絕對時間 (onset) 排序所有音符
    all_notes.sort(key=lambda x: x['onset'])

    # 💡 核心邏輯：用「空白時間」來切割 Take！
    takes = []
    current_take = []
    last_time = 0.0

    for note in all_notes:
        # 如果距離上一個音符超過 10 秒，就當作是新的 Take (錄音段落)
        if current_take and (note['onset'] - last_time > 10.0):
            takes.append(current_take)
            current_take = []
            
        current_take.append(note)
        # 更新最後發聲時間
        last_time = max(last_time, note['offset'])
        
    if current_take: takes.append(current_take)

    # 將切好的 Take 分別存檔
    for i, take_notes in enumerate(takes):
        # 如果這個段落總音符太少(低於20)，可能是按錯或試音，直接丟棄
        if len(take_notes) < 20: continue
            
        for player in ['Human_1', 'Human_2']:
            # 挑出這個 Take 裡屬於該玩家的音符
            player_notes = [n for n in take_notes if n['player'] == player]
            if not player_notes: continue
            
            # 轉回 [status, pitch, velocity, time] 格式
            output_data = []
            for n in player_notes:
                output_data.append([144, n['pitch'], n['velocity'], round(n['onset'], 6)])
                output_data.append([128, n['pitch'], 0, round(n['offset'], 6)])
            
            output_data.sort(key=lambda x: (x[3], x[1]))
            
            # 檔名變成 Take_X，這樣 Kit 就能輕鬆把 Human_1 和 Human_2 配對！
            out_file = os.path.join(output_dir, f"inputmslog_Take_{i+1}_{player}.txt")
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(str(output_data))
            print(f"✅ 產出: inputmslog_Take_{i+1}_{player}.txt (音符數: {len(player_notes)})")

def main():
    experiments = [
        {"xml": "./202412 Experiments/20241217/Recordings Edit 2.tracktionedit", "dir": "./data_management2026/202412 Experiments/20241217"},
        {"xml": "./202412 Experiments/20241218/asdf Edit 1.tracktionedit", "dir": "./data_management2026/202412 Experiments/20241218"},
        {"xml": "./202412 Experiments/20241220/Edit 2.tracktionedit", "dir": "./data_management2026/202412 Experiments/20241220"}
    ]
    for exp in experiments:
        if os.path.exists(exp["xml"]): extract_and_group_takes(exp["xml"], exp["dir"])
        else: print(f"⚠️ 找不到 XML: {exp['xml']}")

if __name__ == '__main__':
    main()