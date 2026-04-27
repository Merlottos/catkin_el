ROS2 Humble 迁移方案
- 包结构（建议）  
  - tetris_interfaces（msg/action 定义）  
  - tetris_vision（camera + detector + classifier + converter）  
  - tetris_planning（solver + 规划服务）  
  - tetris_routing（坐标映射/安全检查）  
  - tetris_arm（xArm 执行与动作）  
  - tetris_bringup（launch & 参数）
- 消息与动作定义（建议最小集）  
  - msg/Cube.msg：uint8 type，float32 angle，float32[2] pixel，float32[2] board，float32[3] arm_from，float32[3] arm_to  
  - msg/CubeArray.msg：builtin_interfaces/Time stamp，Cube[] cubes  
  - msg/PlannerResult.msg：Cube[] cubes，int32 status  
  - srv/PlanTetris.srv：Cube[] cubes -> PlannerResult result  
  - action/ExecutePickPlace.action：Cube[] cubes -> bool success, string message, float32 progress
- 节点职责与数据流  
  - camera_node：发布 sensor_msgs/Image  
  - detector_node：订阅 Image，发布 CubeArray（只填轮廓、像素、尺寸、初始角度）  
  - classifier_node：订阅 CubeArray，填充 type + angle  
  - converter_node：计算抓取像素点与角度补偿  
  - planner_node：提供 PlanTetris 服务（输入 CubeArray，输出带棋盘点/角度）  
  - routing_node：订阅规划结果，输出 CubeArray（含 arm_from/arm_to）  
  - arm_node：订阅或 action 接收 CubeArray 执行动作
- 参数与标定  
  - 把 CoordBuilder 的矩阵写成 YAML（camera_matrix.yaml，board_matrix.yaml）  
  - 在 routing_node 使用 ROS2 参数读取，并可通过 ros2 param set 动态更新  
  - arm_node 用参数配置 arm_ip、速度、加速度、运行高度
- Launch 组织  
  - tetris_bringup/launch/real.launch.py：全链路真实硬件  
  - tetris_bringup/launch/vision.launch.py：仅视觉链路  
  - tetris_bringup/launch/sim.launch.py：无硬件测试
  推荐落地顺序
1. tetris_interfaces 定义 msg/srv/action  
2. tetris_vision 把现有 detector/classifier/converter 放进节点  
3. tetris_planning 提供 PlanTetris 服务  
4. tetris_routing 加入矩阵参数化 + legality_check  
5. tetris_arm 封装 XArmAPI 成 action  
6. tetris_bringup 统一启动与参数