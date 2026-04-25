import time
import sys

import numpy as np

try:
    sys.path.append("./")
    from consts import CubeType
    from modules.camera import RealSenseCamera
    from modules.detector import CubeDetector, CubeClassifier, CubeConverter
    from modules.xarm.wrapper import XArmAPI
except ImportError:
    print("请将本文件放置在项目根目录下运行")
    sys.exit(1)


def main():
    arm = XArmAPI("192.168.1.241")
    arm.motion_enable(enable=True)
    arm.set_mode(0)
    arm.set_state(state=0)
    arm.clean_warn()
    arm.clean_error()

    height = input("请输入机械臂的高度: ")
    try:
        height = int(height)
    except ValueError:
        print("无效的高度值")
        sys.exit(1)

    if height < 90:
        print("小于预设的安全高度, 请重新输入")
        sys.exit(1)

    if height > 300:
        print("无效的高度, 请重新输入")
        sys.exit(1)

    src_points = [
        (0, 0, 1),
        (9, 0, 1),
        # (9, 7, 1),
        (9, 13, 1),
        (0, 13, 1),
        # (0, 7, 1),
        (5, 7, 1),
    ]
    target_values = []

    for w, h, _ in src_points:
        arm.set_mode(2)
        arm.set_state(state=0)
        print(f"正在采集第 {len(target_values) + 1} 个点, 共 {len(src_points)} 个点.")
        print(f"现在, 请将机械臂移动到棋盘格的 ({w}, {h}) 处...")
        while True:
            t0 = time.time()
            input("按回车键采集")
            if time.time() - t0 > 5:
                break
            print("过快, 请重试")

        x, y = arm.get_position()[1][0:2]
        pos = (x, y, height)
        print(f"Tgt: ({pos})")
        target_values.append(pos)
        print()

    return src_points, target_values


if __name__ == "__main__":
    t0 = time.time()

    V, V_prime = main()

    V = np.array(V)
    V_prime = np.array(V_prime)

    # 使用最小二乘法求解变换矩阵 A
    # 我们需要将 V 转置以适应 np.linalg.lstsq 的输入格式
    # 转置后的 V.T 形状为 (3, n) 而 V_prime.T 形状为 (3, n)
    A, residuals, rank, s = np.linalg.lstsq(V, V_prime, rcond=None)

    # A 是变换矩阵
    print("变换矩阵 A:")
    print(A)
    print(f"残差: {residuals}, 秩: {rank}, 奇异值: {s}")

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

    print()
    print(f"恭喜, 您耗时 {(time.time() - t0) / 60:.2f} 分钟 {(time.time() - t0) % 60:.2f} 秒标记了 {len(V)} 个点对, "
          f"平均每个点对耗时 {(time.time() - t0) / len(V):.2f} 秒,"
          f"超过了 {np.random.randint(50, 100)}% 的工程师!")
