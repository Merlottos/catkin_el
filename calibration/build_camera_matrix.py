import time
import sys

import cv2
import numpy as np
from typing import Tuple

try:
    sys.path.append("./")
    from consts import CubeType
    from modules.camera import RealSenseCamera
    from modules.detector import CubeDetector, CubeClassifier, CubeConverter
    from modules.xarm.wrapper import XArmAPI
except ImportError:
    print("请将本文件放置在项目根目录下运行")
    sys.exit(1)


def wait_key(key: str = " "):
    while True:
        if cv2.waitKey(1) & 0xFF == ord(key):
            break


def main():
    arm = XArmAPI("192.168.1.241")
    arm.motion_enable(enable=True)
    arm.set_mode(0)
    arm.set_state(state=0)
    arm.clean_warn()
    arm.clean_error()

    time.sleep(1)

    src_points = []
    target_values = []

    camera = RealSenseCamera()
    camera.init()
    detector = CubeDetector()
    classifier = CubeClassifier()
    converter = CubeConverter()

    while True:
        t1 = time.time()
        arm.set_mode(2)
        arm.set_state(state=0)
        ipt = input(f"第 {len(src_points) + 1} 个点: 按回车键采集，输入字符E结束: ")

        if ipt != "":
            if ipt.lower().strip() == "e":
                if len(src_points) < 6:
                    print("采集的数据点过少，请继续采集或按Ctrl+C退出")
                    continue
                break
            print("输入无效，已跳过")
            continue
        if time.time() - t1 < 5:
            print("采集过快，请重试")
            continue

        pos = arm.get_position()[1][0:3]
        print(f"Tgt: ({pos})")
        target_values.append(pos)

        arm.set_mode(0)
        arm.set_state(state=0)
        arm.set_position(z=200, speed=200, mvacc=10000, wait=True, motion_type=2)
        arm.set_position(374.5, -53.3, 546.1, 180, 0, 0, speed=200, mvacc=10000, wait=True, motion_type=2)
        while True:
            t_cubes = []
            frame = camera.get_frame()
            result = detector.fine_cubes(frame)
            cubes = classifier.recognize_cubes(result)
            cubes = converter.convert(cubes)
            give_up_current = False
            for cube in cubes:
                if cube.category != CubeType.T:
                    continue
                t_cubes.append(cube)
                box = cv2.boxPoints((cube.vertice, (int(cube.width), int(cube.height)), cube.angle))
                box = box.astype(int)
                cv2.drawContours(frame, [box], -1, (255, 0, 0), 2)
                cv2.drawMarker(frame, (int(cube.catch_point[0]), int(cube.catch_point[1])), (0, 255, 0),
                               markerType=cv2.MARKER_DIAMOND, markerSize=10)
                cv2.putText(frame, f"(x: {cube.catch_point[0]:.2f}, y: {cube.catch_point[1]:.2f})",
                            (int(cube.catch_point[0]), int(cube.catch_point[1]) + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            cv2.imshow("frame", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in [ord('q'), ord('Q'), ord(' ')] and len(t_cubes) == 1:
                cv2.destroyAllWindows()
                cv2.imshow("Final", frame)
                print("按Y接受，按N重新采集，按P放弃该点")
                key = cv2.waitKey(0) & 0xFF
                if key in [ord('y'), ord('Y')]:
                    cv2.destroyAllWindows()
                    break
                elif key in [ord('p'), ord('P')]:
                    give_up_current = True
                    cv2.destroyAllWindows()
                    print("已放弃该点")
                    break
                elif key in [ord('n'), ord('N')]:
                    cv2.destroyAllWindows()
                    continue
                else:
                    cv2.destroyAllWindows()
                    continue

        if give_up_current:
            target_values.pop()
            print()
            continue
        pos = t_cubes[0].catch_point
        pos = ([pos[0], pos[1], 1])
        src_points.append(pos)
        print(f"Src: ({pos})")
        print()
        time.sleep(1)

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
