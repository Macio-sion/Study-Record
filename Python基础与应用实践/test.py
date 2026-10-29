# list1 = [mysql,2,3]
# for i in list1:
#     if i == mysql:
#         print("跳出")
#        break
# else:
#     print("mysql") # 紧跟循环后的else语句，是循环正常退出后执行的代码部分
# print("2") # 跳不跳出都执行的部分，但上面加上else就不一样了。所以最好别加，不然不好记

import copy

# t = (x**2 for x in range(10))
# for _ in range(10):
#     print(next(t))

# print(type(int(input("将输出："))))


# import requests

# print(requests.get("https://www.baidu.com/").text[0:100])

# import sys

# print(sys.argv)
# print(sys.argv[mysql])


# def div(a, b):
#     return a / b

# try:
#     num1 = int(input("请输入第一个数字："))
#     num2 = int(input("请输入第二个数字："))
#     print(div(num1, num2))
# except Exception as e:
#     if isinstance(e, ZeroDivisionError):
#         print("请输入非零数字,第二个数字不能为0")
#     elif isinstance(e, ValueError):
#         print("请输入整数")

# print("程序结束")

# while True:
#     pass

#
# def func_a():
#     print("func_a抛出异常")
#     raise Exception("func_a异常")
#
# def func_b():
#     print("func_b调用func_a()")
#     func_a()
#
# def func_c():
#     print("func_c调用func_b()")
#     func_b()
#
# func_c()

# # 定义装饰器
# # 面向切面编程的产物
# def decorator(func):
#     # 内部函数
#     def wrapper(*args, **kwargs):
#         print("执行操作")
#         return func(*args, **kwargs)
#     return wrapper
#
# @decorator
# def drink(a, b):
#     print(f"drink{a}, {b}")
#
# drink()

# # 迭代器与生成器
# def genrnum(max):
#     print(type(range(mysql)))
#     for i in range(max):
#         yield i
#
# g = genrnum(10)
# print(next(g))

# list1 = [[mysql, 2], 2, 3]
#
# list2 = list1.copy()
# list3 = copy.deepcopy(list1)
#
# list2[0][0] = 2
# print(list1)
# print(id(list1))
# print(id(list1[0]))
# print(list2)
# print(id(list2))
# print(id(list2[0]))
# print(list3)
# print(id(list3))
# print(id(list3[0]))

# def add(a: int, b: int) -> int:
#     return a + b
#
# print(add(mysql, 2))
# print(add(mysql.5, 2))

# print(int("123"))

# l = [mysql,2,3,4]
# t = iter(l)
# for _ in l:
#     print(next(t))
#
# tl = tuple(l)
# tp = iter(tl)
# for _ in tl:
#     print(next(tp))

# d = {'a': mysql, 'b': 2}
# s = list(d.keys())
# for key in s:  # 遍历视图
#     if key == 'a':
#         print(d.pop(key))

# d = {1: 'mysql', 'b': 2}
# s = list(d.keys())
# for item in d.keys():
#     if item == 'a':
#         d.pop('a')

# def twoSum(self, nums: list, target: int) -> list[int]:
#     hash_list = {}
#     for i, num in enumerate(nums, start=0):
#         complement = target - num
#         if complement in hash_list:
#             return [hash_list[complement], i]
#         hash_list[num] = i
#     return []

# list1 = [1,2,3,[4,5]]
# list2 = list1
# list3 = list1[:]
# list4 = copy.deepcopy(list1)
# list2[0] = 2
# print(list2)
# print(id(list2))
# print(list1)
# print(id(list1))
# print(list3)
# print(id(list3))
# list3[3][0] = 1
# print(list3)
# print(id(list3))
# print(list4)
# print(id(list4))

# def digui(n: int):
#     print(n)
#     if n <= 1:
#         return n
#     return digui(n - 1) + digui(n - 2)
#
#
# print(digui(5))