import logging
from copy import deepcopy
from typing import Dict, Tuple, List, Optional

import numpy as np

from consts import CubeType, Cube


class Action:
    def __init__(self, category: CubeType, row: int, col: int, rotation: int):
        self.category = category
        self.row = row
        self.col = col
        self.rotation = rotation

    def __str__(self):
        return f"Action: {self.category} at ({self.row}, {self.col}) with rotation {self.rotation}"


class TetrisSolver:
    def __init__(self, column: int, pruning_col: int = 0):
        self.column = column
        self.pruning_col = pruning_col
        self.logger = logging.getLogger("Tetris.TetrisSolver")

        self.mask_map: Dict[CubeType, np.ndarray] = {
            CubeType.O: np.array(
                ((1, 1),
                 (1, 1),),
                dtype=np.int8
            ),
            CubeType.I: np.array(
                ((1, 1, 1, 1),),
                dtype=np.int8
            ),
            CubeType.T: np.array(
                ((1, 1, 1),
                 (0, 1, 0),),
                dtype=np.int8
            ),
            CubeType.L: np.array(
                ((1, 1, 1),
                 (1, 0, 0),),
                dtype=np.int8
            ),
            CubeType.J: np.array(
                ((1, 1, 1),
                 (0, 0, 1),),
                dtype=np.int8
            ),
            CubeType.S: np.array(
                ((0, 1, 1),
                 (1, 1, 0),),
                dtype=np.int8
            ),
            CubeType.Z: np.array(
                ((1, 1, 0),
                 (0, 1, 1),),
                dtype=np.int8
            ),
        }

        self.id_map: Dict[CubeType, int] = {
            CubeType.O: 1,
            CubeType.I: 2,
            CubeType.T: 3,
            CubeType.L: 4,
            CubeType.J: 5,
            CubeType.S: 6,
            CubeType.Z: 7,
        }

        self.rotation_map: Dict[CubeType, Tuple[int]] = {
            CubeType.O: (0,),
            CubeType.I: (0, 1),
            CubeType.T: (0, 1, 2, 3),
            CubeType.L: (0, 1, 2, 3),
            CubeType.J: (0, 1, 2, 3),
            CubeType.S: (0, 1),
            CubeType.Z: (0, 1),
        }
        self.cartesian_set: Tuple[Tuple[CubeType, int], ...] = tuple(
            (cube_type, rotation) for cube_type in self.rotation_map for rotation in self.rotation_map[cube_type]
        )

        self.anchor_map: Dict[CubeType, Tuple[int]] = {
            CubeType.O: (0,),
            CubeType.I: (0, 0),
            CubeType.T: (0, 0, 1, 1),
            CubeType.L: (0, 0, 2, 0),
            CubeType.J: (0, 0, 0, 1),
            CubeType.S: (1, 0),
            CubeType.Z: (0, 1),
        }

        self.offset_map: Dict[CubeType, Tuple[Tuple[float, float]]] = {
            CubeType.O: ((0.5, 0.5),),
            CubeType.I: ((1.5, 0), (0, 1.5)),
            CubeType.T: ((1, 0), (0, 1), (1, 1), (1, 1)),
            CubeType.L: ((0, 0), (0, 2), (2, 1), (1, 0)),
            CubeType.J: ((2, 0), (0, 0), (0, 1), (1, 2)),
            CubeType.S: ((1, 0.5), (0.5, 1)),
            CubeType.Z: ((1, 0.5), (0.5, 1))
        }

        self.solution = None

        self.tracking_map = None

    @staticmethod
    def get_pos(broad: np.ndarray) -> Optional[Tuple[int, int]]:
        # 获取零元素的索引
        zero_indices = np.where(broad == 0)

        if zero_indices[0].size == 0:
            return None  # 如果没有非零元素，返回 None

        # 获取第一个非零元素的行和列
        row = zero_indices[0][0]
        col = zero_indices[1][0]

        return int(row), int(col)

    @staticmethod
    def get_floor(broad: np.ndarray) -> int:
        # 使用布尔索引和np.argmax查找最后一行非零元素的索引
        non_zero_rows = np.any(broad != 0, axis=1)
        last_non_zero_row = np.argmax(non_zero_rows[::-1])  # 从后往前找第一个非零行
        return broad.shape[0] - last_non_zero_row - 1 if np.any(non_zero_rows) else -1

    def can_place(self, row: int, col: int, category: CubeType, rotation: int, broad: np.ndarray) -> bool:
        # 计算mask
        mask = np.rot90(self.mask_map[category], rotation)

        # 获取mask的锚点
        anchor = self.anchor_map[category][rotation]

        # 计算实际放置mask的起始列
        start_col = col - anchor
        end_col = start_col + mask.shape[1]

        # 检查mask的高度是否超过4
        if mask.shape[0] > 4:
            self.logger.warning("Mask height exceeds 4 rows.")
            return False

        # 检查mask的宽度是否超出边界
        if start_col < 0 or end_col > broad.shape[1]:
            return False

        # 检查mask的高度是否超出边界
        if row + mask.shape[0] > broad.shape[0] or row + mask.shape[0] > 14:
            return False

        # 获取放置mask的起始位置
        start_row = row
        end_row = start_row + mask.shape[0]

        # 检查mask的1是否与board上的0重合
        board_subsection = broad[start_row:end_row, start_col:end_col]
        if np.any((mask == 1) & (board_subsection != 0)):
            return False

        return True

    def place(self, row: int, col: int, category: CubeType, rotation: int, broad: np.ndarray, undo: bool = False):
        # 计算mask
        mask = np.rot90(self.mask_map[category], rotation)

        # 获取mask的锚点
        anchor = self.anchor_map[category][rotation]

        # 计算实际放置mask的起始列
        start_col = col - anchor
        end_col = start_col + mask.shape[1]

        # 获取放置mask的起始位置
        start_row = row
        end_row = start_row + mask.shape[0]

        # 检查边界条件，确保不超出broad的范围
        if start_row < 0 or start_col < 0 or end_row > broad.shape[0] or end_col > broad.shape[1]:
            raise ValueError("Mask placement is out of bounds")

        # 放置mask
        weight = -1 if undo else 1
        broad[start_row:end_row, start_col:end_col] += mask * self.id_map.get(category, 0) * weight

        return broad

    def solve(self, cubes: List[Cube]) -> Optional[List[Cube]]:
        cubes = deepcopy(cubes)
        cubes_output = []
        categories = np.array([cube.category.value for cube in cubes if cube.category != CubeType.UNKNOWN])
        unique, counts = np.unique(categories, return_counts=True)
        count_dict = dict(zip(unique, counts))
        self.solution = None
        broad = np.zeros((4, self.column), dtype=np.int8)
        result = []
        try:
            self.dfs_recursive(broad, [], count_dict,None,0)
        except StopIteration:
            result = self.solution
        for action in result:
            # 使用next和生成器表达式查找符合条件的cube
            index = next((i for i, cube in enumerate(cubes) if cube.category == action.category), None)
            offset = self.offset_map[action.category][action.rotation]
            anchor = self.anchor_map[action.category][action.rotation]
            if index is not None:
                cube = cubes[index]
                cube.broad_point = (action.col + offset[0] - anchor, action.row + offset[1])
                cube.broad_angle = action.rotation * 90
                cubes.pop(index)
                cubes_output.append(cube)

        return cubes_output

    def dfs_recursive(self, broad: np.ndarray, solution: List[Action], count_dict: Dict,last_category: Optional[CubeType],consecutive_count: int):
        self.tracking_map = broad.copy()

        pos = self.get_pos(broad)
        if pos is None:
            print("Solution Found Because of No Remaining Position.")
            self.solution = solution
            raise StopIteration
        row, col = pos

        remaining = sum(list(count_dict.values()))
        if remaining == 0 and self.get_floor(broad) - row < 2:
            print("Solution Found Because of No Remaining Cubes.")
            self.solution = solution
            raise StopIteration

        # 判断剩余高度是否小于5
        if broad.shape[0] - row < 5:
            # 拓展最多5行
            _extend = 5 - (broad.shape[0] - row)
            broad = np.vstack([broad, np.zeros((_extend, broad.shape[1]), dtype=np.int8)])

        for i, neighbor in enumerate(self.cartesian_set):
            broad_cpy = broad.copy()
            solution_cpy = deepcopy(solution)
            count_dict_cpy = deepcopy(count_dict)
            category, rotation = neighbor
            if count_dict.get(category.value, 0) == 0:
                continue
            if self.can_place(row, col, category, rotation, broad_cpy):
                new_broad = self.place(row, col, category, rotation, broad_cpy)
                count_dict_cpy[category.value] -= 1
                solution_cpy.append(Action(category, row, col, rotation))
                #buchaoguosange
                if last_category == category:
                    if consecutive_count < 1:
                        self.dfs_recursive(new_broad, solution_cpy, count_dict_cpy, category, consecutive_count + 1)
                    else:
                        continue  # 跳过当前类别的递归调用
                else:
                    self.dfs_recursive(new_broad, solution_cpy, count_dict_cpy, category, 1)
                # 检查放置方块数是否达到34块
                # if len(solution_cpy) == 34:
                #     print("Solution Found with 34 Blocks Placed.")
                #     self.solution = solution_cpy
                #     raise StopIteration
                # self.dfs_recursive(new_broad, solution_cpy, count_dict_cpy)

        # 剪枝条件: 如果已经填满了pruning_col列并且放置方块数为34个, 则结束搜索
        if row > self.pruning_col and len(solution) == 34 and self.get_floor(broad) <= 13:
            print("Solution Found Because of Pruning Column.")
            self.solution = solution
            raise StopIteration


def emulate():
    import time
    solver = TetrisSolver(10, pruning_col=13)
    cubes = []
    for category in CubeType:
        if category == CubeType.UNKNOWN:
            continue
        for _ in range(5):
            cube = Cube()
            cube.category = category
            cubes.append(cube)

    print(f"Total Cubes: {len(cubes)}")

    t1 = time.time()
    solver.solve(cubes)
    print(f"Time Consumed: {(time.time() - t1) * 1000} ms")


if __name__ == "__main__":
    emulate()
