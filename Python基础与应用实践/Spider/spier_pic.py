"""
@Author : Administrator
@Company : 
@Date : 2026/7/29 10:17
@Desc :
@Version : 1.0
"""
import json
import os
import requests
from datetime import datetime
import random
import time


class SpiderPic:
    """

    """

    def __init__(self, key, url, times, sleep=5, path=os.path.join(os.path.dirname(__file__), "spider_images")):
        self.key = key
        self.url = url
        self.times = times
        self.sleep = sleep
        self.path = path

        self.header = {
            "GET": "/search/acjson?tn=resultjson_com&word=%E5%B0%8F%E7%8B%97&ie=utf-8&fp=result&fr=&ala=0&applid=12159312317834155856&pn=30&rn=30&nojc=0&gsm=1e&newReq=1 HTTP/1.1",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "utf-8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Connection": "keep-alive",
            "Host": "image.baidu.com",
            "Referer": "https://image.baidu.com/search/index?tn=baiduimage&fm=result&ie=utf-8&word=%E5%B0%8F%E7%8B%97",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
            "sec-ch-ua": "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Microsoft Edge\";v=\"150\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\""
        }
        self.params = {
            "tn": "resultjson_com",
            "word": f"{self.key}",
            "ie": "utf-8",
            "fp": "result",
            "fr": "",
            "ala": "0",
            "applid": "12159312317834155856",
            "pn": "30",
            "rn": "30",
            "nojc": "0",
            "gsm": "1e",
            "newReq": "1"
        }


    def get_spider_item(self):
        response = requests.get(self.url, headers=self.header, params=self.params)
        response.encoding = 'UTF-8'
        json_data = response.json()
        image_urls = json_data['data']['images']
        if not image_urls or len(image_urls) == 0:
            print("没有更多图片了")
            return
        for image_url in image_urls:
            self.download(image_url['thumburl'])
            time.sleep(self.sleep)



    def download(self, thumb_url):
        thumb_url.encode("utf-8").decode("unicode_escape")

        response = requests.get(thumb_url)
        image = response.content

        # 获取图片名, 根据当前的日期生成一个随机文件名
        current_time = datetime.now()
        time_name = current_time.strftime("%Y%m%d%H%M%S%f")
        pic_name = time_name + str(random.randint(10000, 99999)) + ".jpg"  # 改成原文件的后缀

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # 保存图片
        with open(os.path.join(self.path, pic_name), "wb") as f:
            f.write(image)


if __name__ == '__main__':
    url = 'https://image.baidu.com/search/acjson'
    path = 'D:/test'
    keyword = '小狗'
    thread1 = SpiderPic(key=keyword, url=url, times=1, sleep=5, path=path)

    thread1.get_spider_item()