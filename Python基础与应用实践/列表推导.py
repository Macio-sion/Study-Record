# 列表推导式
# 判断列表推导式
num1 = [f"{i}是偶数" if i % 2 == 0 else f"{i}是奇数" for i in range(1,10)]
num2 = [i for i in range(1,10) if i % 2 == 0]
# 嵌套列表推导式
num3 = [[i, j] for i in range(1,10) for j in range(1,10)]
# 元组+集合推导式
# 推导式不能用来生成元组
set1 = {i for i in range(1,10)}
# 数据批处理
original_ids = [1000, 1001, 1002, 1001, 1003]
new_ids = set(original_ids)
prefix = "SUT-"
user_ids = [f"SUT-{num}" for num in new_ids if num > 1001]
print(user_ids)
