import os
import time

def clean_txt_files(base_path):
    excluded_files = {'inputinterpretation.txt', 'outputinterpretation.txt'}

    # 遍歷目標資料夾
    for root, dirs, files in os.walk(base_path):
        for file_name in files:
            if file_name.endswith('.txt') and file_name not in excluded_files:
                file_path = os.path.join(root, file_name)
                try:
                    print(f"正在刪除檔案: {file_path}")
                    os.remove(file_path)
                except Exception as e:
                    print(f"無法刪除檔案 {file_path}: {e}")
                    time.sleep(1)  # 等待 1 秒後重試
                    try:
                        os.remove(file_path)
                    except Exception as retry_e:
                        print(f"重試仍無法刪除檔案 {file_path}: {retry_e}")

if __name__ == "__main__":
    base_path = r"C:\Users\tippi\SynologyDrive\Tsing_Hua\third_grade\project\RealTimeAccompaniment_COPY\data_management2025\SMC2024\data"
    clean_txt_files(base_path)