"""
@Author : Administrator
@Company : 
@Date : 2026/7/29 15:22
@Desc :
@Version : 1.0
"""
import requests
import json

URL = 'https://dushu.baidu.com/api/pc/getChapterContent'

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "dushu.baidu.com",
    "Referer": "https://dushu.baidu.com/pc/reader?gid=4355360020&cid=1568988152",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
    "sec-ch-ua": "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Microsoft Edge\";v=\"150\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}

params = {
    "data": "{\"book_id\":\"4355360020\",\"cid\":\"4355360020|1568988153\",\"need_bookinfo\":0}"
}


response = requests.get(url=URL, headers=headers, params=params)
response.encoding = 'UTF-8'

print(response.content)


json_obj = json.loads(response.text)
title = json_obj["data"]["novel"]["chapter_title"]
content = json_obj["data"]["novel"]["content"]

print(title, content)