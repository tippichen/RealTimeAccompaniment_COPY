import os
import ast
from collections import Counter

# ==========================================
# 第一部分：資料解析與「和弦量化排序」
# ==========================================
def parse_events_for_matching(raw_data, is_score=False):
    """解析資料，並針對人類和弦的微小時間差進行量化排序"""
    events = []
    for item in raw_data:
        if (not is_score and len(item) == 4) or (is_score and len(item) >= 4):
            if not is_score:
                on_off, pitch, velocity, time = item
            else:
                on_off, pitch, time = item[1], item[2], item[3]
                velocity = 64 # 樂譜不看力度

            if on_off in (144, 1) and velocity > 0:
                # 💡 魔法 1：時間量化 (50毫秒)。把差不多時間按下的音符視為「同時」，強制依音高排序！
                q_time = round(float(time) * 20) / 20.0
                events.append({'pitch': int(pitch), 'q_time': q_time})

    # 先用量化時間排，再用音高排。確保稍微不整齊的和弦也會有完美的陣列順序
    events.sort(key=lambda x: (x['q_time'], x['pitch']))
    return [e['pitch'] for e in events] # 我們只需要乾淨的音高陣列來找譜

# ==========================================
# 第二部分：N-gram 局部特徵比對引擎
# ==========================================
def calculate_ngram_similarity(input_pitches, output_pitches):
    """💡 魔法 2：局部特徵比對 (完美解決未彈完的短片段)"""
    if len(input_pitches) < 4 or len(output_pitches) < 4:
        return 0.0

    def get_ngrams(seq, n):
        return [tuple(seq[i:i+n]) for i in range(len(seq)-n+1)]

    sim_score = 0.0
    # 4連音最能代表一首歌的獨特旋律特徵，給予 50% 最高權重
    weights = {4: 0.50, 3: 0.30, 2: 0.20}

    for n, weight in weights.items():
        ng1 = get_ngrams(input_pitches, n)
        ng2 = get_ngrams(output_pitches, n)
        if not ng1 or not ng2: continue

        c1 = Counter(ng1)
        c2 = Counter(ng2)

        # 只計算「這段短片段」裡面的旋律，有多少 % 命中大樂譜
        intersection = sum((c1 & c2).values())
        ratio = (intersection / len(ng1)) * 100
        sim_score += ratio * weight

    return sim_score

# ==========================================
# 第三部分：你提供的精準對齊演算法 (Align)
# ==========================================
def nextscorepos(score, p):
    for note in score:
        if note[3] > p + 0.01 and note[0] == 144:
            return note[3]
    return max(score, key=lambda x: x[3])[3]

def align(midi, score):
    midi = sorted(midi, key=lambda x: x[3])
    inputinterpretation = [{'part': 0, 'index': event[0], 'on_off': event[1], 'note#': event[2], 'score_pos': event[3], 'time': None, 'vel': None} for event in score]
    latest_input_pos = 0
    latest_input_index = 0
    aligned_events, unaligned_events = [], []

    for inputmsg in midi:
        foundmatch = 0
        if inputmsg[0] == 144:
            index = 0
            while index < len(inputinterpretation) and inputinterpretation[index]['score_pos'] < nextscorepos(score, latest_input_pos) + 0.51:
                if [inputinterpretation[index]['on_off'], inputinterpretation[index]['note#']] == [144, inputmsg[1]] and inputinterpretation[index].get('time') is None:
                    inputinterpretation[index]['vel'] = inputmsg[2]
                    inputinterpretation[index]['time'] = inputmsg[3]
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
                if inputinterpretation[index]['note#'] == inputmsg[1] and not inputinterpretation[index].get('time') is None: 
                    foundon = 1
            if foundon == 1:
                while index < len(inputinterpretation) and foundmatch == 0: 
                    if [inputinterpretation[index]['on_off'], inputinterpretation[index]['note#']] == [128, inputmsg[1]] and inputinterpretation[index].get('time') is None:
                        inputinterpretation[index]['vel'] = inputmsg[2]
                        inputinterpretation[index]['time'] = inputmsg[3]
                        latest_input_index = max(index, latest_input_index)
                        foundmatch = 1
                    index += 1
        if foundmatch == 0:
            unaligned_events.append(inputmsg)
        else:
            aligned_events.append(inputmsg)

    aligned_notes = [note for note in inputinterpretation if note.get('time') is not None]
    return inputinterpretation, len(aligned_events), len(aligned_notes)

# ==========================================
# 第四部分：自動化總司令部 (Main)
# ==========================================
def main():
    search_dirs = [
        'data_management2026/202412 Experiments/20241217',
        'data_management2026/202412 Experiments/20241218',
        'data_management2026/202412 Experiments/20241220',
    ]
    logs_dir = "logs"

    print("🔍 正在載入標準樂譜庫...")
    score_db = {}
    for song in os.listdir(logs_dir):
        score_path = os.path.join(logs_dir, song, "outputscore.txt")
        if os.path.exists(score_path):
            with open(score_path, 'r', encoding='utf-8') as f:
                raw_score = list(ast.literal_eval(f.read().strip()))
            score_db[song] = {
                'raw': raw_score, 
                'parsed_pitches': parse_events_for_matching(raw_score, is_score=True) 
            }
    print(f"✅ 成功載入 {len(score_db)} 首樂譜！\n" + "="*40)

    for d in search_dirs:
        if not os.path.exists(d): continue
        files = os.listdir(d)
        target_files = [f for f in files if f.startswith('inputmslog_Human') and f.endswith('.txt')]
        parent_dir = os.path.basename(os.path.normpath(d))

        for fname in target_files:
            input_path = os.path.join(d, fname)
            
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content: continue
                raw_midi = list(ast.literal_eval(content))
                
            input_pitches = parse_events_for_matching(raw_midi, is_score=False)
            if not input_pitches: continue

            best_match = None
            best_similarity = -1.0

            # 利用 N-gram 特徵掃描所有樂譜
            for song_name, score_data in score_db.items():
                sim = calculate_ngram_similarity(input_pitches, score_data['parsed_pitches'])
                if sim > best_similarity:
                    best_similarity = sim
                    best_match = song_name

            # 因為 N-gram 非常嚴格，只要超過 20% 通常就是正確的片段
            if best_match and best_similarity > 20.0: 
                print(f"🎵 {parent_dir}/{fname}")
                print(f"   -> 🎯 匹配成功: {best_match} | 旋律特徵吻合度: {best_similarity:.2f}%")

                interpretation, aligned_events, aligned_notes = align(raw_midi, score_db[best_match]['raw'])
                print(f"   -> ⚙️ 對齊結果: 成功配對 {aligned_events} 個事件，對應 {aligned_notes} 個樂譜音符。")

                output_fname = fname.replace('inputmslog', 'interpretation')
                output_path = os.path.join(d, output_fname)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(str(interpretation))
                print(f"   -> 💾 已儲存: {output_fname}\n")
            else:
                print(f"🎵 {parent_dir}/{fname} \n   -> ❌ 吻合度過低 ({best_similarity:.2f}%)，判定為無效或廢棄錄音。\n")

if __name__ == '__main__':
    main()