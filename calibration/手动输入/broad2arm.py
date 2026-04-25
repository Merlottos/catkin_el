import numpy as np

# 假设我们有 n 个点对
# V 是原始坐标系中的点，形状为 (n, 3)
# V_prime 是新坐标系中的点，形状为 (n, 3)
V = np.array([
    [0, 0,  1],
    [9, 0,  1],
    [9, 6,  1],
    [4, 6,  1],
    [0, 6,  1],
    [0, 13, 1],
    [9, 13, 1]
])

V_prime = np.array([
    [319.518372, 88.441849, 110],
    [330.778961, 268.816742, 110],
    [450.830658, 260.816833, 110],
    [445.843597, 160.572845, 110],
    [440.843658, 80.294968, 110],
    [581.57135, 72.294983, 110],
    [592.469177, 252.267639, 110],
])

# 使用最小二乘法求解变换矩阵 A
# 我们需要将 V 转置以适应 np.linalg.lstsq 的输入格式
# 转置后的 V.T 形状为 (3, n) 而 V_prime.T 形状为 (3, n)
A, residuals, rank, s = np.linalg.lstsq(V, V_prime, rcond=None)

# A 是变换矩阵
print(f"残差: {residuals}, 秩: {rank}, 奇异值: {s}")
print("变换矩阵 A:")
print(A)
print()

# 验证结果
V_prime_calculated = V @ A
# 转换为非科学计数法4位小数
V_prime_calculated_display = np.around(V_prime_calculated, decimals=4)
print("计算得到的新坐标系中的点:")
print(V_prime_calculated_display)
print()

# 比较计算得到的点和实际的新坐标系中的点
V_prime_display = np.around(V_prime, decimals=4)
print("实际的新坐标系中的点:")
print(V_prime_display)
print()

# 展示差异
diff = V_prime_calculated - V_prime
diff_display = np.around(diff, decimals=2)
print("差异:")
print(diff_display)
