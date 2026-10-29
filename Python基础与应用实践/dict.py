# 字典本质是键与值，键要是唯一的，因此在py里所谓的不可变类型都可以作为键
# 集合本质是没有值的字典，都要通过键去哈希位置，所以无需，因为涉及扩容，每次扩容都可能会变位置，所以逻辑上是无序的。

# 一般定义字典，先把键值定义在全局

ID = "id"
NAME = "name"
DEPT = "dept"
SALARY = "salary"

emp_dict = {
    ID: 1000,
    NAME: "wjc",
    DEPT: "游戏部",
    SALARY: 20000
}
# print(f"员工编号：{emp_dict[ID]}")

# # 字典的访问方法get()
# print(f"员工编号：{emp_dict.get(ID)}")

# # 字典的添加update()//批量
# emp_dict.update({"age":23, "detail":"..."})
# print(f"员工字典：{emp_dict}")

# key
keys = emp_dict.keys()
print(keys, type(keys))

# value
values = emp_dict.values()
print(values, type(values))

# item
items = emp_dict.items()
print(items, type(items))

# pop 与 del


#推导式
dict = {(x , y) for x in range(1, 6) for y in range(1, 6)}

dict1 = {f"{chr(65 + n)}" for n in range(0, 6)}
print(dict1)