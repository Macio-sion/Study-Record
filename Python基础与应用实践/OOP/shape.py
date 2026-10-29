import math


class Shape:
    """
    形状基类
    """
    def __init__(self, color):
        self.color = color

    def area(self):
        return 0

    def perimeter(self):
        return 0

class Circle(Shape):
    """
    子类 - 圆
    """
    def __init__(self, color, radius):
        super().__init__(color)
        self.radius = radius

    def area(self):
        return math.pi * self.radius ** 2

    def perimeter(self):
        return math.pi * self.radius * 2

class Rectangle(Shape):
    """
    子类 - 矩形
    """
    def __init__(self, color, width, height):
        super().__init__(color)
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)

class Square(Rectangle):
    """
    子类 - 正方形
    """
    def __init__(self, color, length):
        super().__init__(color, length, length)
        self.length = length

    def area(self):
        return self.length * self.length

    def perimeter(self):
        return 4 * self.length

if __name__ == '__main__':
    shape = Shape('red')
    print(shape.area())
    print(shape.perimeter())

    circle = Circle('blue', 5)
    print(circle.area())
    print(circle.perimeter())

    square = Square('green', 5)
    print(square.area())
    print(square.perimeter())

    rectangle = Rectangle('yellow', 5, 5)
    print(rectangle.area())
    print(rectangle.perimeter())

