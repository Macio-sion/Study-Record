import requests
# import json

# 提交任务请求
response = requests.post(
    'http://localhost:8000/tasks',
    json={"message": "你好。"}
)

# 打印响应内容
print(response.json())
# 返回任务ID:task_id
task_id = response.json()["task_id"]

# 根据task_id方法任务
# task_id = "01M1VFQEYHYTNNF0R67NGWFHJN"
response = requests.get(
    F'http://localhost:8000/tasks/{task_id}'
)


print(response.json())