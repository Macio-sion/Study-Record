import threading
import time

# 全局共享数据
a, b = 0, 0
lock = threading.Lock()  # 创建锁对象
# 线程函数
def unsafe_operation():
    global a, b
    while True:
        # 模拟一些计算
        while lock:
            a += 1
            time.sleep(0)  # 让出时间片，模拟线程切换 等价于 yield(放弃当前cpu时间片)
            b += 1
        if a != b:
            print(f"数据不一致: a={a}, b={b}")
            break

task1 = threading.Thread(target=unsafe_operation)  # 创建线程对象
task2 = threading.Thread(target=unsafe_operation)

if __name__ == "__main__":
    task1.start()  # 启动线程
    task2.start()
    task1.join()  # 阻塞函数，直到 task1 执行完毕
    task2.join()