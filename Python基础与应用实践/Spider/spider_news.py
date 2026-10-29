"""
@Author : Administrator
@Company :
@Date : 2026/8/13
@Desc : 通用网页新闻爬虫，URL 可动态指定
@Version : 1.0
"""
from lxml import etree
import requests
import re
import argparse
import sys
import os
import json
import datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "utf-8",
    "Connection": "keep-alive",
}


def fetch_html(url: str) -> str:
    """
    动态抓取指定 URL 对应的 HTML 页面内容
    :param url: 新闻页面的目标 URL
    :return: 解码后的 HTML 文本
    """
    if not url or not re.match(r"^https?://", url, re.IGNORECASE):
        raise ValueError("请输入合法的 http/https 协议的 URL")

    response = requests.get(url=url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    return response.text


def parse_news(html: str) -> dict:
    """
    解析新闻页 HTML，提取常见的新闻字段（标题、作者、时间、正文）
    :param html: 原始 HTML 文本
    :return: 包含新闻信息的字典
    """
    tree = etree.HTML(html)
    if tree is None:
        return {"status": "error", "message": "HTML 解析失败"}

    title = tree.xpath(
        "//title/text() | "
        "//h1[@class='title']/text() | "
        "//h1[@id='article_title']/text() | "
        "//article/h1/text() | "
        "//div[@class='article-title']/h1/text()"
    )

    author = tree.xpath(
        "//meta[@name='author']/@content | "
        "//span[@class='author']/text() | "
        "//div[@class='author']/text() | "
        "//a[@class='author-name']/text()"
    )

    publish_time = tree.xpath(
        "//meta[@property='article:published_time']/@content | "
        "//meta[@name='publishdate']/@content | "
        "//meta[@name='pubdate']/@content | "
        "//span[@class='date']/text() | "
        "//span[@class='publish-time']/text()"
    )

    content_nodes = tree.xpath(
        "//article//p/text() | "
        "//div[@class='article-content']//p/text() | "
        "//div[@class='content']//p/text() | "
        "//div[@id='article-content']//p/text()"
    )

    title_text = title[0].strip() if title else ""
    author_text = author[0].strip() if author else ""
    time_text = publish_time[0].strip() if publish_time else ""
    content_text = "\n".join(
        [p.strip() for p in content_nodes if p and p.strip()]
    )

    return {
        "title": title_text,
        "author": author_text,
        "publish_time": time_text,
        "content": content_text,
    }


def crawl_news(url: str) -> dict:
    """
    完整流程：动态下载页面并解析新闻内容
    :param url: 新闻页面的目标 URL
    :return: 爬取并解析后的新闻数据
    """
    html = fetch_html(url)
    news = parse_news(html)
    news["url"] = url
    return news


def save_news_to_json(news_data: dict, file_path: str = None) -> str:
    """
    将新闻内容排版成指定 JSON 格式并保存为 JSON 文件
    要求格式：{"news": [{"source_web": "", "title": "", "content": ""}]}
    :param news_data: crawl_news 返回的新闻字典，需要包含 url / title / content
    :param file_path: 保存文件路径，若为 None 则保存到脚本所在目录并自动生成文件名
    :return: 实际保存的文件绝对路径
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    source_web = news_data.get("url", "")
    title = news_data.get("title", "") or news_data.get("status", "")
    content = news_data.get("content", "") or news_data.get("message", "")

    payload = {
        "news": [
            {
                "source_web": source_web,
                "title": title,
                "content": content,
            }
        ]
    }

    if file_path is None:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r"[\\/:*?\"<>|\r\n\t]", "", title).strip()
        safe_title = safe_title[:40] or "news"
        file_name = f"news_{ts}_{safe_title}.json"
        file_path = os.path.join(current_dir, file_name)
    else:
        if not os.path.isabs(file_path):
            file_path = os.path.join(current_dir, file_path)

    os.makedirs(os.path.dirname(file_path) or current_dir, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

    return os.path.abspath(file_path)


def main():
    parser = argparse.ArgumentParser(description="通用网页新闻爬虫，动态指定目标 URL")
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        help="目标新闻页面的 URL（http/https 协议）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="保存的 JSON 文件路径，不传则自动生成到脚本所在目录",
    )
    args = parser.parse_args()

    if not args.url:
        args.url = input("请输入要爬取的新闻页面 URL: ").strip()

    try:
        result = crawl_news(args.url)
    except Exception as e:
        print(f"[ERROR] 爬取失败: {e}", file=sys.stderr)
        return

    print("=" * 60)
    print(f"URL : {result.get('url')}")
    print(f"标题: {result.get('title')}")
    print(f"作者: {result.get('author')}")
    print(f"发布时间: {result.get('publish_time')}")
    print("-" * 60)
    print("正文:")
    print(result.get("content", "") or "（未提取到正文，请针对目标页面调整 XPath）")
    print("=" * 60)

    try:
        saved_path = save_news_to_json(result, args.output)
        print(f"[INFO] 新闻已保存到: {saved_path}")
    except Exception as e:
        print(f"[ERROR] 保存 JSON 失败: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
