def sub(first, second):
    if not first and not second:
        print("数字不能为空")
        return
    print(f"结果是：{first - second}")
    # return first - second

def plus(first, second):
    if not first and not second:
        print("数字不能为空")
        return
    print(f"结果是：{first + second}")
    # return first + second

def mul(first, second):
    if not first and not second:
        print("数字不能为空")
        return
    print(f"结果是：{first * second}")
    # return first * second

def div(first, second):
    if not first and not second:
        print("数字不能为空")
        return
    if second == 0:
        print("被除数不能为0")
        return
    print(f"结果是：{first / second}")
    # return first / second

def mod(first, second):
    if not first and not second:
        print("数字不能为空")
        return
    if second == 0:
        print("被除数不能为0")
        return
    print(f"结果是：{first % second}")
    # return first % second

def main():
    """

    :return:
    """
    while True:
        print("欢迎使用本计算器,退出系统请按q。".center(30, "*"))
        num1 = int(input("请输入第一运算数"))
        tag = input("请输入运算符")
        num2 = int(input("请输入第二运算数"))
        if tag == "+":
            plus(num1,num2)
            continue
        elif tag == "-":
            sub(num1,num2)
            continue
        elif tag == "*":
            mul(num1,num2)
            continue
        elif tag == "/":
            div(num1,num2)
            continue
        elif tag == "%":
            mod(num1,num2)
            continue
        elif tag == "q":
            break
        else:
            print("暂不支持该运算符的运算")
            continue
main()