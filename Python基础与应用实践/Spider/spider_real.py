"""
@Author : Administrator
@Company : 
@Date : 2026/7/29 9:38
@Desc :
@Version : 1.0
"""
import requests

url = 'https://cn.bing.com/images/search'

headers = {
    "authority": "cn.bing.com",
    "method": "GET",
    "scheme": "https",
    "Accept": "*/*",
    # "Accept-Encoding": "gzip, deflate, br",
    "Accept-Encoding": "utf-8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cookie": "0",
    "Ect": "4g",
    "Referer": "https://cn.bing.com/images/search?view=detailV2&ccid=GUiUnh3Z&id=ED5CB77EB75446D1888C1B04F591657EB641E110&thid=OIP.GUiUnh3ZAVW0KO4i2N7H_AHaE6&mediaurl=https%3A%2F%2Fpic3.zhimg.com%2Fv2-d1f733345b0d11ea4d1bde0e2511dbc8_720w.jpg%3Fsource%3D172ae18b&exph=384&expw=578&q=%E4%B8%96%E7%95%8C%E6%97%85%E6%B8%B8%E8%83%9C%E5%9C%B0&FORM=IRPRST&ck=013AE326E8DBEBEEAED85C0F4D6F9EF2&selectedIndex=0&itb=0&cw=724&ch=715&mode=overlay",
    "Priority": "u=1,i",
    "Sec-Ch-Prefers-Color-Scheme": "light"
}

params = {
    "view": "detailV2",
    "ccid": "GUiUnh3Z",
    "id": "ED5CB77EB75446D1888C1B04F591657EB641E110",
    "thid": "OIP.GUiUnh3ZAVW0KO4i2N7H_AHaE6",
    "mediaurl": "https://pic3.zhimg.com/v2-d1f733345b0d11ea4d1bde0e2511dbc8_720w.jpg?source=172ae18b",
    "exph": "384",
    "expw": "578",
    "q": "世界旅游胜地",
    "FORM": "IRPRST",
    "ck": "013AE326E8DBEBEEAED85C0F4D6F9EF2",
    "selectedIndex": "0",
    "itb": "0",
    "cw": "724",
    "ch": "715",
    "mode": "overlay"
}

response = requests.get(url=url, headers=headers, params=params)
response.encoding = 'utf-8'

print(response.text)