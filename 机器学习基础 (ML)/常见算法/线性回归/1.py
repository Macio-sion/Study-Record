from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np

X = np.random.rand(200, 3)
y = X @ np.array([2.0, -1.0, 0.5]) + 0.1 * np.random.randn(200)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = LinearRegression()
model.fit(X_train, y_train)
pred = model.predict(X_test)

print("系数:", model.coef_)
print("MSE:", mean_squared_error(y_test, pred))

# if __name__ == "__main__":
#     x = np.array([[1, 2], [2, 3], [3, 4]])
#     print(x.shape)
#     y = np.array([[1, 2], [2, 3], [3, 4]])
#     print(y.shape)
#     print(f"{x},{y.T},{x @ y.T}")