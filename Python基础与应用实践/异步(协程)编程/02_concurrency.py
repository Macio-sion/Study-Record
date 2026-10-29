"""
多任务
"""
import threading
import time
import requests

NUM = 5

def download():
    response = requests.get("http://www.baidu.com")
    if response.status_code == 200:
        print(f"获取成功，线程: {threading.current_thread().name}")
    else:
        print(f"获取失败，线程: {threading.current_thread().name}")

if __name__ == "__main__":
    # 单线程获取
    start_time = time.time()
    for i in range(NUM):
        download()
    end_time = time.time()
    print(f"单线程耗时: {end_time - start_time:.2f}秒")
    # 循环多线程，并发访问
    start_time = time.time()
    threads = []
    for i in range(NUM):
        t = threading.Thread(target=download)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    end_time = time.time()
    print(f"多线程耗时: {end_time - start_time:.2f}秒")