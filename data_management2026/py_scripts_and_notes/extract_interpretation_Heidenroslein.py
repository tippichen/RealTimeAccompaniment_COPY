import os
import matplotlib.pyplot as plt

def align_score_and_performance(performance, interpretation):
    piece = "none" 
    
    inputscorepositions = [-1]
    for note in interpretation:
        if not note[3] == inputscorepositions[-1] and note[1] == 144:
            inputscorepositions += [note[3]]
    inputscorepositions.append(10000) 
    
    lastinputIndex = -1
    lastinputscorepositionIndex = 0
    
    matched_count = 0   
    unmatched_count = 0 
    unmatched_events = []

    for msg in performance:
        foundmatch = 0
        if msg[0] == 144: 
            for note in interpretation:
                if note[1] == 144 and note[3] >= inputscorepositions[lastinputscorepositionIndex] - 0.01 and note[3] <= inputscorepositions[lastinputscorepositionIndex+1] + 0.01:
                    if note[2] == msg[1] and note[4:] == [0, 0]: 
                        lastinputIndex = max(lastinputIndex, note[0])
                        lastinputscorepositionIndex = inputscorepositions.index(interpretation[lastinputIndex][3])
                        foundmatch = 1
                        matched_count += 1
                        break
        
        elif msg[0] == 128:
            for note in reversed(interpretation): 
                if note[1] == 144 and note[2] == msg[1] and not note[4:] == [0, 0]:
                    for offnote in interpretation[note[0]:]: 
                        if offnote[1] == 128 and offnote[2] == msg[1]:
                            if offnote[4:] == [0, 0]:
                                offnote[4] = msg[3]
                                offnote[5] = msg[2]
                                foundmatch = 1
                                matched_count += 1
                                break
                    break
        
        if foundmatch == 0: 
            unmatched_count += 1
            unmatched_events.append(msg)

    return interpretation, matched_count, unmatched_count, unmatched_events

def plot_alignment(interpretation, output_img_path):
    score_times = []
    real_times = []
    
    for note in interpretation:
        if note[1] == 144 and note[4] != 0:
            score_times.append(note[3])  
            real_times.append(note[4])   
            
    plt.figure(figsize=(10, 6))
    plt.plot(score_times, real_times, marker='o', linestyle='-', color='b', markersize=4)
    plt.title('Score Alignment Curve')
    plt.xlabel('Score Beat (score_data)')
    plt.ylabel('Real Time in Seconds (performance_data)')
    plt.grid(True)
    plt.savefig(output_img_path)
    plt.close()

def main():
    print("=== MIDI Alignment ===")
    folder_path = input("請輸入資料夾路徑: ").strip(" '\"")
    
    msg_log_file = os.path.join(folder_path, 'inputmsglog.txt')
    score_file = os.path.join(folder_path, 'outputscore.txt')
    output_file = os.path.join(folder_path, 'inputinterpretation.txt')

    if not os.path.exists(msg_log_file) or not os.path.exists(score_file):
        print(f"\n錯誤：在 {folder_path} 找不到必要的 txt 檔案。")
        return

    with open(score_file, 'r') as f:
        score_raw = eval(f.read())
    interpretation_ready = [event + [0, 0] for event in score_raw]

    with open(msg_log_file, 'r') as f:
        performance_raw = eval(f.read())

    performance_clean = []
    for event in performance_raw:
        if isinstance(event[0], str):
            performance_clean.append(event[1:])
        else:
            performance_clean.append(event)

    print(f"\n成功載入：樂譜音符 {len(interpretation_ready)} 個，彈奏事件 {len(performance_clean)} 個。")
    print("正在執行對齊運算...")

    final_interpretation, matched, unmatched_count, unmatched_events = align_score_and_performance(performance_clean, interpretation_ready)

    with open(output_file, 'w') as f:
        f.write(str(final_interpretation))

    print(f"\n處理完成！檔案已儲存至：{output_file}")
    print(f"統計報告：成功配對 {matched} 個事件，無法配對 {unmatched_count} 個事件。")
    if matched == 0:
        print("警告：成功配對數為 0，輸出的時間與力度將全部為 0！(請參考下方的除錯說明)")
    
    if unmatched_count > 0:
        print("\n--- 無法配對的事件列表 ---")
        for event in unmatched_events:
            print(event)
        print("--------------------------")
    
    plot_file = os.path.join(folder_path, 'alignment_plot.png')
    print(f"\n正在將對齊曲線圖存成圖片：{plot_file} ...")
    plot_alignment(final_interpretation, plot_file)
    print("✨ 圖表已生成！請從左側檔案總管點開查看。")

if __name__ == "__main__":
    main()
