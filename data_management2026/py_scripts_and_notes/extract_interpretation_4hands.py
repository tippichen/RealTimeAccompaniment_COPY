import os
from pathlib import Path

# 目錄與候選樂譜設定
search_dirs = [
    'data_management2026/202412 Experiments/20241217',
    # 'data_management2026/202412 Experiments/20241220',
]
logs_dir = Path("logs")
FOLDER_CANDIDATES = {
    '20241217': ['debussy1_1', 'debussy1_2'],
    '20241220': ['debussy3_1', 'debussy3_2']
}

# ==========================================
# 核心邏輯 (完全保留原本的 matching logic)
# ==========================================
def write_interpretation(performance, interpretation):
    inputscorepositions=[-1]
    for note in interpretation:
        if not note[3]==inputscorepositions[-1] and note[1]==144:
            inputscorepositions+=[note[3]]
    inputscorepositions.append(10000) 
    
    lastinputIndex=-1
    lastinputscorepositionIndex=0
    unmatchednotes=0

    for msg in performance:
        foundmatch=0
        if msg[0]==144: 
            for note in interpretation:
                if note[1]==144 and note[3]>=inputscorepositions[lastinputscorepositionIndex]-0.01 and note[3]<=inputscorepositions[lastinputscorepositionIndex+1]+1.01:
                    if (note[2]==msg[1] or (note[0]<9 and (note[2]-msg[1])%12==0)) and note[4:]==[0,0]:
                        note[4]=msg[3] 
                        note[5]=msg[2] 
                        lastinputIndex=max(lastinputIndex,note[0])
                        lastinputscorepositionIndex=inputscorepositions.index(interpretation[lastinputIndex][3])
                        foundmatch=1
                        break
        if msg[0]==128:
            for note in reversed(interpretation): 
                if note[1]==144 and note[2]==msg[1] and not note[4:]==[0,0]:
                    for offnote in interpretation[note[0]:]: 
                        if offnote[1]==128 and offnote[2]==msg[1]:
                            if not offnote[4:]==[0,0]:
                                pass
                            offnote[4]=msg[3]
                            offnote[5]=msg[2]
                            foundmatch=1
                            break
                    break

        if foundmatch==0: 
            unmatchednotes+=1

    return interpretation, unmatchednotes

# ==========================================
# 執行主程式：動態搜尋檔案、比對並匯出
# ==========================================
def process_experiments():
    for dir_str in search_dirs:
        target_dir = Path(dir_str)
        date_key = target_dir.name  # 自動抓取最後一個資料夾名稱 (如 20241217)
        
        if date_key not in FOLDER_CANDIDATES:
            continue
            
        if not target_dir.exists():
            print(f"\n[錯誤] 找不到資料夾，請確認終端機的執行路徑是否正確: {target_dir.absolute()}")
            continue

        # 使用寬鬆的正規表示式抓檔案，避免 inputmsglog / inputmslog 的拼字問題
        input_log_paths = list(target_dir.glob("input*log*"))
        
        if not input_log_paths:
            print(f"\n[找不到檔案] 在 {target_dir} 中找不到檔名包含 'input...log' 的檔案。")
            print("該資料夾內實際存在的檔案有：")
            for f in target_dir.iterdir():
                if f.is_file():
                    print(f"  - {f.name}")
            continue

        for input_log_path in input_log_paths:
            print(f"\n--- 正在處理數據: {input_log_path.name} ---")
            
            try:
                # 讀取使用者的 performance
                with open(input_log_path, 'r', encoding='utf-8') as f:
                    performance = eval(f.read())
            except Exception as e:
                print(f"讀取 {input_log_path.name} 失敗: {e}")
                continue

            best_match_name = None
            best_interpretation = None
            min_unmatched = float('inf')

            candidates = FOLDER_CANDIDATES[date_key]
            for candidate in candidates:
                score_path = logs_dir / candidate / 'outputscore.txt'
                
                if not score_path.exists():
                    print(f"  找不到候選樂譜: {score_path}")
                    continue
                    
                try:
                    with open(score_path, 'r', encoding='utf-8') as f:
                        candidate_score = eval(f.read())
                except Exception as e:
                    print(f"  讀取 {score_path} 失敗: {e}")
                    continue
                
                test_interpretation = [event + [0, 0] for event in candidate_score]
                result_interpretation, unmatched_count = write_interpretation(performance, test_interpretation)
                
                print(f"  比對 {candidate} -> 無法匹配音符數: {unmatched_count}")
                
                if unmatched_count < min_unmatched:
                    min_unmatched = unmatched_count
                    best_match_name = candidate
                    best_interpretation = result_interpretation

            if best_match_name:
                print(f">>> 最佳匹配為: {best_match_name} (Unmatched: {min_unmatched})")
                
                # 產生輸出檔名：將原本檔名的 inputms(g)log 替換掉
                original_name = input_log_path.stem  # 不含副檔名的檔名
                # 簡單暴力的替換法，避免拼字問題
                output_name = original_name.replace('inputmsglog', 'extracted_interpretation')
                output_name = output_name.replace('inputmslog', 'extracted_interpretation')
                if 'extracted' not in output_name:
                    output_name = f"extracted_interpretation_{original_name}"
                
                output_path = target_dir / f"{output_name}.txt"
                
                # 把時間 (note[4]) 還是 0 的音符濾掉，只保留有成功配對的音
                cleaned_interpretation = [note for note in best_interpretation if note[4] != 0]

                with open(output_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(str(best_interpretation))
                print(f"已將結果輸出至: {output_path}")
            else:
                print(f">>> {input_log_path.name} 沒有找到任何可匹配的結果。")

if __name__ == "__main__":
    process_experiments()