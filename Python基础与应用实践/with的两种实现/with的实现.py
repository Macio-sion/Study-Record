# @Author : Administrator
# @Company : 
# @Date : 2026/7/13 10:22
# @Desc :
# @Version : 1.0

class MyWith:

    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """

        :param exc_type: 异常类型
        :param exc_val: 异常值
        :param exc_tb: 异常的追踪信息
        :return:
        """
        if exc_type:
            print(exc_type, exc_val, exc_tb)
        return False