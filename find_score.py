import os
import ast
import difflib

# 💡 大絕招：直接定義「每一天只可能出現哪兩首樂譜」
FOLDER_CANDIDATES = {
    '20241217': ['debussy1_1', 'debussy1_2'],
    '20241218': ['faure1', 'faure2'],
    '20241220': ['debussy3_1', 'debussy3_2']
}

# ==========================================
# 第一部分：純粹提取音高，照時間排
# ==========================================
def extract_pitches(raw_data, is_score=False):
    events = []
    for item in raw_data:
        if not is_score and len(item) == 4 and item[0] in (144, 1) and item[2] > 0:
            events.append({'pitch': item[1], 'time': item[3]})
        elif is_score and len(item) >= 4 and item[1] in (144, 1):
            events.append({'pitch': item[2], 'time': item[3]})

    events.sort(key=lambda x: float(x['time']))
    return [e['pitch'] for e in events]

# ==========================================
# 第二部分：2選1 簡單對決比對
# ==========================================
def calculate_similarity(input_pitches, score_pitches):
    """只用最標準的字串比對，因為只有兩個對手，分數高的就是贏家"""
    if not input_pitches or not score_pitches: return 0.0
    matcher = difflib.SequenceMatcher(None, input_pitches, score_pitches)
    return matcher.ratio() * 100

# ==========================================
# 第三部分：你的 Align 演算法
# ==========================================
def nextscorepos(score, p):
    for note in score:
        if note[3] > p + 0.01 and note[0] == 144: return note[3]
    return max(score, key=lambda x: x[3])[3]

def align(midi, score):
    midi = sorted(midi, key=lambda x: x[3])
    inputinterpretation = [{'part': 0, 'index': e[0], 'on_off': e[1], 'note#': e[2], 'score_pos': e[3], 'time': None, 'vel': None} for e in score]
    latest_input_pos = 0
    latest_input_index = 0
    aligned_events, unaligned_events = [], []

    for inputmsg in midi:
        foundmatch = 0
        if inputmsg[0] == 144:
            index = 0
            while index < len(inputinterpretation) and inputinterpretation[index]['score_pos'] < nextscorepos(score, latest_input_pos) + 0.51:
                if [inputinterpretation[index]['on_off'], inputinterpretation[index]['note#']] == [144, inputmsg[1]] and inputinterpretation[index].get('time') is None:
                    inputinterpretation[index]['vel'], inputinterpretation[index]['time'] = inputmsg[2], inputmsg[3]
                    latest_input_index = max(index, latest_input_index)
                    latest_input_pos = max(inputinterpretation[index]['score_pos'], latest_input_pos)
                    foundmatch = 1
                    break
                index += 1
        if inputmsg[0] == 128:
            index = latest_input_index
            foundon = 0
            while index > 0 and foundon == 0: 
                index -= 1
                if inputinterpretation[index]['note#'] == inputmsg[1] and not inputinterpretation[index].get('time') is None: foundon = 1
            if foundon == 1:
                while index < len(inputinterpretation) and foundmatch == 0: 
                    if [inputinterpretation[index]['on_off'], inputinterpretation[index]['note#']] == [128, inputmsg[1]] and inputinterpretation[index].get('time') is None:
                        inputinterpretation[index]['vel'], inputinterpretation[index]['time'] = inputmsg[2], inputmsg[3]
                        latest_input_index = max(index, latest_input_index)
                        foundmatch = 1
                    index += 1
        if foundmatch == 0: unaligned_events.append(inputmsg)
        else: aligned_events.append(inputmsg)

    aligned_notes = [note for note in inputinterpretation if note.get('time') is not None]
    return inputinterpretation, len(aligned_events), len(aligned_notes)

# ==========================================
# 第四部分：自動化總司令部
# ==========================================
def main():
    search_dirs = [
        'data_management2026/202412 Experiments/20241217',
        'data_management2026/202412 Experiments/20241218',
        'data_management2026/202412 Experiments/20241220',
    ]
    logs_dir = "logs"
    
    print("🚀 開始「指定對決」模式...\n")
    
    for d in search_dirs:
        if not os.path.exists(d): continue
        
        folder_date = os.path.basename(os.path.normpath(d))
        candidates = FOLDER_CANDIDATES.get(folder_date)
        
        if not candidates:
            print(f"⚠️ {folder_date} 沒有設定對決名單，跳過。")
            continue

        print(f"📂 進入 {folder_date} (只會從 {candidates} 中二選一)")
        
        # 只載入這兩首候選的樂譜
        score_db = {}
        for song in candidates:
            score_path = os.path.join(logs_dir, song, "outputscore.txt")
            if os.path.exists(score_path):
                with open(score_path, 'r', encoding='utf-8') as f:
                    raw_score = list(ast.literal_eval(f.read().strip()))
                score_db[song] = {
                    'raw': raw_score, 
                    'pitches': extract_pitches(raw_score, is_score=True) 
                }

        # 處理資料夾裡的錄音檔
        target_files = [f for f in os.listdir(d) if f.startswith('inputmslog') and f.endswith('.txt')]

        for fname in target_files:
            input_path = os.path.join(d, fname)
            with open(input_path, 'r', encoding='utf-8') as f:
                raw_midi = list(ast.literal_eval(f.read().strip()))
                
            input_pitches = extract_pitches(raw_midi, is_score=False)
            if not input_pitches: continue

            best_match = None
            best_similarity = -1.0

            # 兩首對決，選出分數比較高的那首
            for song_name, score_data in score_db.items():
                sim = calculate_similarity(input_pitches, score_data['pitches'])
                if sim > best_similarity:
                    best_similarity = sim
                    best_match = song_name

            print(f"🎵 {fname} \n   -> 🎯 判定為: {best_match} (比較勝出)")

            # 執行對齊
            interpretation, ae, an = align(raw_midi, score_db[best_match]['raw'])
            print(f"   -> ⚙️ 對齊結果: 配對 {ae} 個事件，對應 {an} 個樂譜音符。")

            # 存檔
            output_fname = fname.replace('inputmslog', 'interpretation')
            output_path = os.path.join(d, output_fname)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(interpretation))
            print(f"   -> 💾 已儲存: {output_fname}\n")

if __name__ == '__main__':
    main()