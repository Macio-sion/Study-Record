class Student:
    """
    学生类
    """

    __slots__ = ["__name", "__age", "__gender"]

    def __init__(self, name, age, gender = "未知"):
        self.__name = name
        self.__age = age
        self.__gender = gender

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def age(self):
        return self.__age

    @age.setter
    def age(self, age):
        self.__age = age

    @property
    def gender(self):
        return self.__gender

    @gender.setter
    def gender(self, gender):
        self.__gender = gender



if __name__ == '__main__':
    wjc = Student("wjc",23, gender="男")
    wjc.name = "wjc"
    print(wjc.name)
    print(wjc.__dict__)
