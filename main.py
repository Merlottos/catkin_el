import time

import cv2


from consts import CubeType
from modules.camera import RealSenseCamera
from modules.detector import CubeDetector, CubeClassifier, CubeConverter
from modules.planning import TetrisSolver
from modules.routing import CoordBuilder
from modules.xarm.wrapper import XArmAPI
ARM_IP = "192.168.1.241"
RUNNING_HEIGHT = 130
HOME_POS = (374.5, -53.3, 546.1, 180, 0, 0)
SPEED = 500
MVACC = 30000



def main():
    arm = XArmAPI(ARM_IP)
    arm.clean_warn()
    arm.clean_error()
    arm.motion_enable(enable=True)
    arm.set_mode(0)
    arm.set_state(state=0)
    arm.set_cgpio_digital(0, 1)

    time.sleep(1)

    camera = RealSenseCamera()
    camera.init()
    detector = CubeDetector()
    classifier = CubeClassifier()
    converter = CubeConverter()
    solver = TetrisSolver(10, pruning_col=12)
    builder = CoordBuilder()

    arm.set_mode(0)
    arm.set_state(state=0)
    arm.set_position(*HOME_POS, speed=1000, mvacc=50000, wait=True)
    
    # while True:
    #     frame = camera.get_frame()

    #     result = detector.fine_cubes(frame)
    #     cubes = classifier.recognize_cubes(result)
    #     cubes = converter.convert(cubes)
    #     for cube in cubes:
    #         if cube.category == CubeType.UNKNOWN:
    #             continue
    #         box = cv2.boxPoints((cube.vertice, (int(cube.width), int(cube.height)), cube.angle))
    #         box = box.astype(int)
    #         cv2.drawContours(frame, [box], -1, (255, 0, 0), 5)
    #         cv2.drawMarker(frame, (int(cube.catch_point[0]), int(cube.catch_point[1])), (0, 255, 0),
    #                        markerType=cv2.MARKER_DIAMOND, markerSize=10)
    #         cv2.putText(frame, f"{cube.category}", (int(cube.catch_point[0]), int(cube.catch_point[1]) - 10),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    #         cv2.putText(frame, f"(x: {cube.catch_point[0]:.2f}, y: {cube.catch_point[1]:.2f})",
    #                     (int(cube.catch_point[0]), int(cube.catch_point[1]) + 10),
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    #     cv2.imshow("frame", frame)
    #     key = cv2.waitKey(1) & 0xFF
    #     if key in [ord('q'), ord('Q'), ord(' ')]:
    #         cv2.destroyAllWindows()
    #         cv2.imshow("Final", frame)
    #         print("按Y接受，或重新采集")
    #         key = cv2.waitKey(0) & 0xFF
            
    #         if key in [ord('y'), ord('Y')]:
    #             cv2.destroyAllWindows()
    #             break
    #         else:
    #             cv2.destroyAllWindows()
    #             continue

    time.sleep(3)
    frame = camera.get_frame()
    result = detector.fine_cubes(frame)
    cubes = classifier.recognize_cubes(result)
    cubes = converter.convert(cubes)
    # print("正在规划轨迹，请稍等")
    cubes = solver.solve(cubes)
    # if cubes is []:
    #     raise ValueError("规划失败")
    print(f"规划结果: \n{solver.tracking_map}")

    cubes = builder.compute(cubes)
    # input("按回车键开始执行")
    # print()

    for cube in cubes:
        start_pos = cube.arm_from.copy()
        start_x, start_y, start_z = start_pos
        end_pos = cube.arm_to.copy()
        end_x, end_y, end_z = end_pos
        rot = cube.arm_rot
        rot1 = -rot / 2
        rot2 = rot / 2
        print(cube)
        arm.set_position(start_x, start_y, RUNNING_HEIGHT, 180, 0, rot1, speed=SPEED, mvacc=MVACC, wait=True)
        arm.set_cgpio_digital(0, 0)
        arm.set_position(start_x, start_y, z=start_z, speed=500, mvacc=30000, wait=True)
        time.sleep(.100)
        arm.set_position(z=RUNNING_HEIGHT, yaw=rot1 + (rot2 / 10), speed=500, mvacc=30000, wait=True)
        arm.set_position(end_x, end_y, RUNNING_HEIGHT, 180, 0, rot2, speed=SPEED, mvacc=MVACC, wait=True)
        arm.set_position(end_x, end_y, z=end_z, yaw=rot2, speed=500, mvacc=30000, wait=True)
        arm.set_cgpio_digital(0, 1)
        time.sleep(.100)
        arm.set_position(z=RUNNING_HEIGHT, yaw=rot2, speed=500, mvacc=30000, wait=True)
        print()

    arm.set_position(*HOME_POS, speed=1000, mvacc=50000, wait=True)


if __name__ == "__main__":
    t0 = time.time()
    main()
    time_seconds = time.time() - t0
    print(f"任务完成，用时 {time.time() - t0:.2f} 秒, 合 {time_seconds // 60:.0f} 分 {time_seconds % 60:.0f} 秒")
