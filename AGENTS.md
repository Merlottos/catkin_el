# AGENTS.md
# 面向本仓库的智能代理工作指南（中文）

## 1. 项目概览与目录
- 入口脚本: `main.py`
- 视觉/检测: `modules/camera.py`、`modules/detector.py`
- 规划/求解: `modules/planning.py`
- 坐标与标定/路径: `modules/routing.py`、`calibration/`
- 机械臂SDK: `modules/xarm/`（第三方库，尽量少改）
- 公共类型与常量: `consts.py`

## 2. 构建/安装/运行命令
### 2.1 依赖安装
- Windows 批处理: `install.bat`
- 通用方式: `pip install -r requirements.txt`

### 2.2 运行主流程
- 直接运行: `python main.py`
- 说明: 需要 RealSense 相机与 xArm 机械臂在线（见下文环境说明）

### 2.3 Lint/格式化/测试
- 本仓库未内置 lint/format/test 工具配置。
- 建议代理在新增工具前先征询维护者，避免引入不一致的格式规则。

### 2.4 单测/单用例运行
- 当前没有测试框架与测试目录。
- 若未来引入 pytest，可采用: `pytest -k <test_name> -q` 运行单测。

## 3. 环境与硬件依赖
- Python 版本: 未固定，建议 3.8+（已有 3.8/3.11 的 .pyc 迹象）
- 依赖库: OpenCV、RealSense、NumPy（见 `requirements.txt`）
- 硬件:
  - RealSense RGB 相机（`modules/camera.py` 依赖 pyrealsense2）
  - xArm 机械臂（`modules/xarm/` SDK 与 `main.py` 中 XArmAPI）
- 网络: 机械臂 IP 通过 `main.py` 的 `ARM_IP` 配置

## 4. 项目架构与数据流
1) 采集: `RealSenseCamera.get_frame()` 获取 RGB 图像
2) 检测: `CubeDetector.fine_cubes()` 提取方块轮廓与最小外接矩形
3) 分类: `CubeClassifier.recognize_cubes()` 通过几何比例/掩膜判别类别
4) 坐标转换:
   - `CubeConverter.convert()` 计算抓取像素点与角度
   - `CoordBuilder.compute()` 通过相机/棋盘标定矩阵转换为机械臂坐标
5) 规划: `TetrisSolver.solve()` 生成方块在棋盘上的摆放动作
6) 执行: `main.py` 中 `XArmAPI` 设定位姿与抓放动作

## 5. 代码风格与规范（结合现有代码）
### 5.1 Imports
- 标准库、第三方、本地模块分组，当前文件多数未严格分组，新增代码请保持一致性。
- 相对导入: 本地模块以 `from modules.xxx import ...` 为主。
- 避免在非入口文件里修改 `sys.path`（`modules/detector.py` 已有历史代码）。

### 5.2 命名
- 类: `CamelCase`（如 `CubeDetector`、`TetrisSolver`）
- 函数/变量: `snake_case`（如 `fine_cubes`, `catch_point`）
- 常量: `UPPER_SNAKE_CASE`（如 `ARM_IP`、`RUNNING_HEIGHT`）

### 5.3 类型与数据结构
- 使用 `typing` 提示（已有 `Optional`, `List`, `Tuple`, `Dict`）
- `Cube` 为跨模块数据载体，新增字段请在 `consts.py` 中集中维护
- `CubeType` 枚举用于流程判断，新增类型需同步更新分类/规划/坐标模块

### 5.4 格式与布局
- 文件缩进 4 空格
- 尽量保持现有风格，不强制引入 black/ruff
- 中英文注释混用，关键算法可保留中文解释

### 5.5 错误处理与日志
- 使用 `logging`（已有 `self.logger = logging.getLogger(...)`）
- 硬件相关失败优先抛异常并在入口层处理
- 允许少量 `print` 用于调试，但批量输出应改为 logger

### 5.6 性能与安全
- 视觉/规划可能耗时，避免在主循环中频繁复制大矩阵
- 机械臂动作前后应保证安全姿态与高度限制
- `CoordBuilder.legality_check` 等安全约束不得删除

### 5.7 第三方代码
- `modules/xarm/` 视为第三方 SDK，除非明确要求，否则避免改动

## 6. 关键模块说明
- `modules/camera.py`: RealSense 采集与基础错误重试
- `modules/detector.py`: 视觉检测与方块类别识别
- `modules/planning.py`: 俄罗斯方块搜索/放置规划
- `modules/routing.py`: 像素/棋盘坐标到机械臂坐标映射
- `calibration/`: 透视矩阵与标定脚本

## 7. 开发建议与注意事项
- 改动标定矩阵需同步验证抓取与放置精度
- `main.py` 内部硬编码参数（IP/速度/加速度）建议外置配置
- 新增功能优先在 `modules/` 内封装，减少 `main.py` 复杂度
- 若引入测试，建议先从纯算法部分（规划/坐标转换）开始

## 8. Cursor/Copilot 规则
- 未检测到 `.cursor/rules/`、`.cursorrules` 或 `.github/copilot-instructions.md`

## 9. 文档与变更
- 本文档面向智能代理，保持更新
- 任何新增工具链/规则请同时更新此文件
