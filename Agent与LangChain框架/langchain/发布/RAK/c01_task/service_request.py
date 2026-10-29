import requests

# 提交队列

response = requests.post(
    "http://localhost:8000/tasks",
    json={"message": "你好"}
)


# 查询访问结果