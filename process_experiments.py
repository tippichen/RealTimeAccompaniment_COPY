import os
import ast
import difflib

# ==========================================
# 1. 讀取與萃取功能 (抓取第三個元素：音高)
# ==========================================
def get_pitch_from_file(file_path):
    """讀取 txt 檔，並抓取每一行的第三個元素 (index 2)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = ast.literal_eval(f.read().strip())
            # 確保長度大於 2 才抓，避免報錯
            return [row[2] for row in data if len(row) > 2]
    except Exception as e:
        # 如果檔案不是預期的 list 格式，就安靜地跳過
        return []

# ==========================================
# 2. 建立標準答案題庫 (掃描 logs 資料夾)
# ==========================================
def build_gt_database(logs_dir):
    print(f"🔄 正在從 {logs_dir} 建立標準答案題庫...")
    gt_dict = {}
    
    for root, dirs, files in os.walk(logs_dir):
        if 'outputscore.txt' in files:
            file_path = os.path.join(root, 'outputscore.txt')
            seq = get_pitch_from_file(file_path)
            
            if seq:
                # 用 logs 裡的子資料夾名稱作為這首曲子的名字
                folder_name = os.path.basename(root)
                gt_dict[folder_name] = seq
                
    print(f"✅ 題庫建立完成！共找到 {len(gt_dict)} 首標準樂譜。\n")
    return gt_dict

# ==========================================
# 3. 掃描錄音檔並比對 (掃描 202412 Experiments)
# ==========================================
def match_recordings(exp_dir, gt_dict):
    print(f"🔍 開始掃描錄音檔: {exp_dir}")
    print("-" * 60)
    
    for root, dirs, files in os.walk(exp_dir):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                
                # 抓出這個錄音檔的音高序列
                test_seq = get_pitch_from_file(file_path)

                # 如果檔案裡面抓不到音高 (可能只是普通的 log 文字檔)，就跳過
                if not test_seq:
                    continue

                best_match_name = "未知曲目"
                highest_ratio = 0.0

                # 跟題庫裡的所有標準答案比對
                for gt_name, gt_seq in gt_dict.items():
                    matcher = difflib.SequenceMatcher(None, test_seq, gt_seq)
                    ratio = matcher.ratio()

                    if ratio > highest_ratio:
                        highest_ratio = ratio
                        best_match_name = gt_name

                # 印出結果
                # 只顯示最後兩層路徑，讓版面乾淨一點
                folder_name = os.path.basename(root)
                print(f"📂 錄音檔: ...\\{folder_name}\\{file}")
                print(f"  👉 最佳匹配: {best_match_name} (來自 logs)")
                print(f"  👉 匹配率:   {highest_ratio:.2%}\n")
                
    print("-" * 60)
    print("🎯 所有錄音檔比對完成！")

# ==========================================
# 4. 執行主程式
# ==========================================
if __name__ == "__main__":
    # 設定路徑
    logs_directory = r"C:\Users\tippi\SynologyDrive\Tsing_Hua\third_grade\project\RealTimeAccompaniment_COPY\logs"
    experiments_directory = r"C:\Users\tippi\SynologyDrive\Tsing_Hua\third_grade\project\RealTimeAccompaniment_COPY\data_management2026\202412 Experiments"
    
    # 執行流程
    ground_truth_db = build_gt_database(logs_directory)
    
    if ground_truth_db:
        match_recordings(experiments_directory, ground_truth_db)
    else:
        print("❌ 在 logs 資料夾中沒有找到任何有效的 outputscore.txt，請檢查路徑。")