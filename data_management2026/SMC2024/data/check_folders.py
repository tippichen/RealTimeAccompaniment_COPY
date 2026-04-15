import os

def check_folders(base_path):
    missing_files_folders = []
    invalid_files_folders = []

    for root, dirs, files in os.walk(base_path):
        # 檢查是否有 inputinterpretation.txt 和 outputinterpretation.txt
        if 'inputinterpretation.txt' not in files or 'outputinterpretation.txt' not in files:
            missing_files_folders.append(root)
        else:
            # 檢查檔案內容
            for file_name in ['inputinterpretation.txt', 'outputinterpretation.txt']:
                file_path = os.path.join(root, file_name)
                try:
                    with open(file_path, 'r') as f:
                        first_line = f.readline().strip()
                        # 檢查第一層是否有六組數字
                        if len(first_line.split()) != 6:
                            invalid_files_folders.append(root)
                            break
                except Exception as e:
                    print(f"無法讀取檔案 {file_path}: {e}")

    # 列出結果
    if missing_files_folders:
        print("以下資料夾缺少 inputinterpretation.txt 或 outputinterpretation.txt:")
        for folder in missing_files_folders:
            print(folder)
    else:
        print("所有資料夾都有 inputinterpretation.txt 和 outputinterpretation.txt。")

    if invalid_files_folders:
        print("以下資料夾的檔案內容不符合要求（第一層不是六組數字）:")
        for folder in invalid_files_folders:
            print(folder)
    else:
        print("所有檔案內容都符合要求。")

if __name__ == "__main__":
    base_path = r"C:\Users\tippi\SynologyDrive\Tsing_Hua\third_grade\project\RealTimeAccompaniment_COPY\data_management2025"
    check_folders(base_path)