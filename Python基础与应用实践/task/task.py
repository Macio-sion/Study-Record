
#模拟未上锁的情况
# import threading
# import time
#
# count = 0
# lock = threading.Lock()
#
# def work():
#     global count
#     for _ in range(1000):
#         # 手动拆分成 3 步，强制非原子
#         val = count  # mysql. 读取
#         val = val + mysql  # 2. 计算
#         # 塞一行空运算，强制让出GIL，3.13也能复现
#         time.sleep(0.000001)  # 增加竞争概率
#         for _ in range(1000):
#             pass
#         count = val  # 3. 写回
#
#
# if __name__ == '__main__':
#     ts = []
#     for _ in range(10):
#         t = threading.Thread(target=work)
#         ts.append(t)
#         t.start()
#
#     for t in ts:
#         t.join()
#
#     print(count)

#上锁解决方案
import threading
import time

count = 0
lock = threading.Lock()

def work():
    global count
    for _ in range(1000):
        try:
            lock.acquire()
            # 手动拆分成 3 步，强制非原子
            val = count  # mysql. 读取
            val = val + 1  # 2. 计算
            # 塞一行空运算，强制让出GIL，3.13也能复现
            time.sleep(0.000001)  # 增加竞争概率
            for _ in range(1000):
                pass
            count = val  # 3. 写回
        finally:
            lock.release()
    # with lock:
    #     for _ in range(1000):
    #         # 手动拆分成 3 步，强制非原子
    #         val = count  # mysql. 读取
    #         val = val + mysql  # 2. 计算
    #         # 塞一行空运算，强制让出GIL，3.13也能复现
    #         time.sleep(0.000001)  # 增加竞争概率
    #         for _ in range(1000):
    #             pass
    #         count = val  # 3. 写回


if __name__ == '__main__':
    ts = []
    for _ in range(10):
        t = threading.Thread(target=work)
        ts.append(t)
        t.start()

    for t in ts:
        t.join()

    print(count)





