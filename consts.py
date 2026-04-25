import enum
from typing import Tuple, Optional

import numpy as np


# 枚举类型: 方块类别
class CubeType(enum.Enum):
    UNKNOWN = -1
    I = 0
    J = 1
    L = 2
    O = 3
    S = 4
    T = 5
    Z = 6

    def __str__(self):
        default_texts = {
            CubeType.UNKNOWN: "Unknown",
            CubeType.I: "I-shaped Cube",
            CubeType.J: "J-shaped Cube",
            CubeType.L: "L-shaped Cube",
            CubeType.O: "O-shaped Cube",
            CubeType.S: "S-shaped Cube",
            CubeType.T: "T-shaped Cube",
            CubeType.Z: "Z-shaped Cube",
        }
        return default_texts.get(self, "Unknown")


# 方块类
class Cube:
    def __init__(
            self,
            contour=None,
            hull=None,
            vertice=None,
            width=None,
            height=None,
            angle=None,
            mask=None,
    ):
        # Camera attributes
        self.contour: np.ndarray = contour                          # 轮廓
        self.hull: np.ndarray = hull                                # 凸包
        self.vertice: Tuple[float, float] = vertice                 # 旋转框中心点
        self.width: float = width                                   # 旋转框宽度
        self.height: float = height                                 # 旋转框高度
        self.angle: float = angle                                   # 旋转角度
        self.mask: np.ndarray = mask                                # 二值图像掩膜
        self.category: CubeType = CubeType.UNKNOWN                  # 方块类别
        self.catch_point: Optional[Tuple[float, float]] = None      # 抓取点
        self.catch_angle: Optional[np.ndarray] = None               # 抓取角度

        # Broad attributes
        self.broad_point: Optional[Tuple[float, float]] = None
        self.broad_angle: Optional[np.ndarray] = None

        # Arm attributes
        self.arm_from: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray] | np.ndarray] = None
        self.arm_to: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray] | np.ndarray] = None
        self.arm_rot: Optional[float] = None

        # Debug attributes
        self.hot_map = None

    def __str__(self):
        return (f"方块类型: {self.category}, 位于: \n  像素坐标: {self.catch_point} \n"
                f"  机械臂坐标: {self.arm_from} \n"
                f"  棋盘坐标: {self.broad_point}, 棋盘角度: {self.broad_angle} \n"
                f"  机械臂坐标: {self.arm_to} \n"
                f"  机械臂旋转角度: {self.arm_rot} \n")


def poly2d(xy, *coeffs) -> np.ndarray:
    x, y = xy
    degree = 2
    idx = 0
    z = np.zeros_like(x)
    for i in range(degree + 1):
        for j in range(degree + 1 - i):
            z += coeffs[idx] * x**i * y**j
            idx += 1
    return z
