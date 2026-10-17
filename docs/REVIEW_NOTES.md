# 复习笔记（REVIEW_NOTES）

> 这份笔记由 Claude 根据 2026-10-17 的对话整理，用来复习。
> 它不是我的 LEARNING_LOG.md（LEARNING_LOG 只由我自己用自己的话写）。
> 每一步后面附了当时的面试题；"参考答案"是提示，面试前要改成我自己的话。

---

## 1. 现在做到哪里了

| 步骤 | 内容                                   | 状态      |
|------|----------------------------------------|-----------|
| 0    | 第一次 Git commit + push               | ✅ 完成   |
| 1    | 安装 TurtleBot3 / Gazebo / SLAM / Nav2 | ✅ 完成   |
| 2    | SLAM 建图并保存                        | ✅ 完成   |
| 3    | Nav2 加载地图，开启自动导航            | ✅ 完成   |
| 4    | RViz 发导航目标，机器人自己开过去      | ✅ 完成   |
| 5    | （可选）巡逻节点 A→B→C                 | ⏳ 进行中 |
| 6    | （可选）集装箱堆场世界                 | 跳过      |
| 7    | 必做：最终测试（畅通 / 有障碍物）      | 未开始    |
| 8    | README + 演示 GIF                      | 未开始    |

**下次从这里继续：** 第 5 步的 5.2 第 ① 小步：用 RViz 的 Publish Point 拿到一个目标点的 x、y。
（5.1 已完成：package `src/port_patrol` 已经建好。）

---

## 2. 每次开机的标准启动流程

每个命令开一个新终端（VS Code 终端面板点 **+**）。

**终端 1：Gazebo 仿真世界**
```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

**终端 2：Nav2（带我们改过的配置文件）**
```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=$HOME/maps/my_map.yaml params_file:=$HOME/turtlebot3-port-patrol/config/nav2_burger.yaml
```

**终端 3：RViz 一打开，马上设置初始位置**（Gazebo 刚启动时机器人在出生点 = 地图原点）
```bash
ros2 topic pub --times 3 -r 1 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 0.0}, orientation: {z: 0.0, w: 1.0}}, covariance: [0.25,0,0,0,0,0, 0,0.25,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0.0685]}}"
```

**检查：** RViz 左上 Global Status = Ok；左下 Navigation = **active**；机器人周围有绿色小箭头（AMCL 粒子）。

**关闭：** 每个终端按 `Ctrl+C`。不要用 Gazebo 的重置按钮（↻），它会把机器人删掉。

---

## 3. 每一步做了什么

### 第 2 步：SLAM 建图

**命令（4 个终端）：**
```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py                     # 仿真世界
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=True           # SLAM 建图
ros2 run rviz2 rviz2 -d $(ros2 pkg prefix nav2_bringup)/share/nav2_bringup/rviz/nav2_default_view.rviz   # 看地图
ros2 run turtlebot3_teleop teleop_keyboard                                   # 键盘开车
```

**保存地图（SLAM 还在运行时）：**
```bash
mkdir -p ~/maps
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map
ls ~/maps        # 应该看到 my_map.pgm 和 my_map.yaml
```

**要点：**
- `online_async`：边开边建图。
- `use_sim_time:=True`：用 Gazebo 的仿真时钟，不加的话时间对不上，建不出图。
- RViz 只负责**显示**，地图存在 SLAM Toolbox 里。关掉 RViz 也还能保存地图。
- 关 RViz 时出现 `failed to create guard condition ... context is not valid` 报错，是 RViz 退出不干净，**不影响**任何东西。
- 地图颜色：白色 = 空地，黑色 = 障碍物，灰色 = 未知，红点 = 当前激光扫到的点。

**teleop 按键：**
- `w` / `x`：前进速度加 / 减（每按一次只加 0.01，要连按 10 次左右才看得出在动）
- `a` / `d`：左转 / 右转（转向速度会一直保持，拐完要按反方向抵消回 0）
- `s`：全部停下
- 按键前要先用鼠标点一下 teleop 终端。
- 建图时：前进速度 ≤ 0.1，转向速度 ≤ 0.3，不要撞东西。

**做错了什么 → 怎么改的**

- **按了一次 `w` 就等它走；之前按过 `a`/`d` 没清零**
  - 结果：机器人只会原地转圈，以为"只能左右转"
  - 后来怎么改的（对）：先按 `s` 把速度全清零，再连按 `w` 大约 10 次；拐弯时轻按 `a`/`d`，拐完按反方向抵消回 0

- **转向速度开到 0.89，开得快，撞到了柱子**
  - 结果：轮子打滑，里程计算错，地图画歪，红色激光点和墙对不上
  - 后来怎么改的（对）：关掉 Gazebo 和 SLAM 重新启动（地图清空），慢慢开：前进 ≤ 0.1、转向 ≤ 0.3，离柱子远一点

- **让 Claude 开车时，teleop 还开着**
  - 结果：teleop 每 0.1 秒发一次"速度 0"，会和别的命令抢控制权
  - 后来怎么改的（对）：用 `ros2 node list` 确认 `/teleop_keyboard` 还在，到它的终端按 `Ctrl+C` 关掉

- **保存地图前先把 RViz 关了，以为地图没了**
  - 结果：其实没事，还出现一段 `guard condition` 报错
  - 后来怎么改的（对）：地图存在 SLAM Toolbox 里，不在 RViz 里。只要 SLAM 终端没关，照样能保存；那段报错只是 RViz 退出不干净

**面试准备（参考答案要改成我自己的话）**

**面试题：机器人碰撞打滑后，SLAM 地图为什么会变乱？**
SLAM 部分依赖里程计来估计机器人怎么移动。打滑时轮子在转但车没动，里程计算出的移动是错的，SLAM 把新的激光数据画在了错误的位置，地图就重叠、歪掉了。

**面试题：SLAM 的"建图"和 Nav2 里的"定位"有什么区别？**
建图（SLAM Toolbox）时没有地图，要同时画地图和估计位置；定位（AMCL）时地图已经有了而且固定不变，只需要估计机器人在这张地图上的位置。

### 第 3 步：Nav2 加载地图 + 定位

1. 关掉 SLAM（地图已经保存了），**Gazebo 保持开着**。
2. 启动 Nav2（见第 2 节终端 2）。
3. 设置初始位置：可以在 RViz 里用 **2D Pose Estimate**（点住机器人的位置，往车头方向拖），也可以用终端命令发 `/initialpose`（见第 2 节终端 3）。
4. RViz 小技巧：Displays 里勾选 **RobotModel** 才能看到机器人；右上角 Views 里的 Angle 不是 0 时，说明地图被转过方向了。

**做错了什么 → 怎么改的**

- **照着"机器人在地图左侧中间"去找机器人，用 2D Pose Estimate 拖动（这个位置是 Claude 说错的）**
  - 结果：没有反应。实际上 RViz 视图转了 90°（Views 里 Angle = -1.57），而且 RobotModel 没勾选，看不到机器人
  - 后来怎么改的（对）：勾选 RobotModel；机器人其实在地图下方中间那个红绿小坐标轴的位置

- **用 `ros2 topic pub --once` 发初始位置（Claude 给的命令）**
  - 结果：消息丢了：发完就退出，还没和 AMCL 连上
  - 后来怎么改的（对）：改成 `--times 3 -r 1`，每秒发 1 次，连发 3 次

- **加了 `-w 2`，等 2 个订阅者（Claude 判断错了）**
  - 结果：一直显示 "Waiting for at least 2 matching subscription(s)"，卡住不动
  - 后来怎么改的（对）：`Ctrl+C` 停掉。订阅 `/initialpose` 的只有 AMCL 一个，RViz 是发布方

- **朝向用了四舍五入的四元数 `z: 0.87, w: 0.49`（Claude 给的值）**
  - 结果：AMCL 拒收：`Received initialpose message is malformed`
  - 后来怎么改的（对）：用精确值 `z: 0.870356, w: 0.492424`（平方和 = 1），再加上 covariance

- **Navigation 是 inactive，就点 **Startup****
  - 结果：失败：Nav2 只启动了一半，controller_server 已经 active，再 Startup 会报错
  - 后来怎么改的（对）：应该先 Reset 再 Startup，但是……

- **然后点了 **Reset****
  - 结果：Nav2 整个进程崩溃退出（exit code -6）
  - 后来怎么改的（对）：重新启动 Nav2，**RViz 一打开马上**发初始位置，这次全部都是 active

**教训：** 先发初始位置，再期待 Nav2 全部 active。顺序反了，就容易只启动一半。

**面试准备（参考答案要改成我自己的话）**

**面试题：为什么 Nav2 开始导航之前，要先告诉 AMCL 机器人的初始位置？**
AMCL 是在已知地图上"猜"位置，需要一个大概的起点，才能把粒子撒在正确的区域附近。没有初始位置，就没有 map→odom 的坐标变换，Nav2 不知道机器人在地图的哪里，也就没法规划路线。

### 第 4 步：发导航目标

1. 确认 Navigation = **active**。
2. 点 RViz 顶部的 **Nav2 Goal**，在地图白色区域点住，拖一下表示车头方向，然后松开。
3. 结果：Feedback = **reached**，Recoveries = 0，表示成功。

**过程：** RViz 把目标作为 **action** 发给 Nav2 的 `bt_navigator` → 全局规划器（planner）在地图上算出路线 → 控制器（controller）看着 costmap，每一刻算出速度发给轮子 → 到达后把结果返回给 RViz。

**做错了什么 → 怎么改的**

- **Navigation active 之后发了 Nav2 Goal，路线（红线）也画出来了**
  - 结果：机器人不动，Recoveries 一直增加到 6，日志里有 `Failed to make progress`
  - 后来怎么改的：这次不是操作错了，而是配置不适合我的电脑：Gazebo 慢，`/scan` 大约 0.6 秒才来一次，`collision_monitor` 只接受 0.2 秒以内的数据，就把所有运动命令拦下来。把配置复制到 `config/nav2_burger.yaml`，把 `scan.source_timeout` 改成 2.0，重启 Nav2 → 发目标 → **reached**，Recoveries = 0

- **先试着在运行中用 `ros2 param set` 改这个参数**
  - 结果：显示 "Set parameter successful"，但实际上没生效，警告还在
  - 后来怎么改的：有些参数只在节点启动时读一次，要改配置文件再重启才有效

**面试准备（参考答案要改成我自己的话）**

**面试题：Nav2 里的全局规划（planner）和局部控制（controller）分别负责什么？**
planner 在整张地图（global costmap）上找一条从起点到终点的路线；controller 沿着这条路线走，根据机器人周围实时的 local costmap 算出每一刻的速度命令，也负责躲开路上临时出现的障碍物。

**面试题：为什么 Nav2 用 action，而不是 topic 或 service，来接收导航目标？**
导航要花很长时间：过程中需要反馈（还剩多远、用了多久），结束时要有结果（成功、失败、取消），中途还可能要取消。topic 没有结果，service 是一问一答、不适合长时间任务，只有 action 同时支持这三点。

**面试题：collision_monitor 为什么要把"过期"的传感器数据当成不可信？**
它是安全模块。数据过期，说明它不知道机器人前面**现在**有没有障碍物；用旧数据可能会撞上，所以宁可停车。我遇到的问题就是：仿真太慢导致数据"看起来"过期，所以要根据实际的传感器频率调整超时时间。

### 第 5 步：巡逻节点（进行中）

**5.1 建 package（已完成）：**
```bash
cd ~/turtlebot3-port-patrol
mkdir -p src && cd src
ros2 pkg create --build-type ament_python port_patrol --dependencies rclpy nav2_simple_commander geometry_msgs
```
建包时打印出一串许可证名字（MIT、GPL…），只是提示没指定许可证，不影响使用。

**5.2 最小版本（下一步）：**

① 用 Publish Point 拿坐标：
```bash
ros2 topic echo /clicked_point      # 先在新终端运行这条，它会一直等着
```
然后在 RViz 顶部点 **📍 Publish Point**（在 Nav2 Goal 左边），再点地图上的白色空地，终端就会打印出 x、y。

② 自己写 `src/port_patrol/port_patrol/patrol_node.py`，会用到：

- **导入**
  - 用什么：`from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult`；`from geometry_msgs.msg import PoseStamped`

- **启动**
  - 用什么：`rclpy.init()`，然后 `nav = BasicNavigator()`

- **等 Nav2 准备好**
  - 用什么：`nav.waitUntilNav2Active()`

- **造一个目标**
  - 用什么：`PoseStamped()`：填 `header.frame_id = 'map'`、`header.stamp = nav.get_clock().now().to_msg()`、`pose.position.x/y`、`pose.orientation.w = 1.0`

- **发目标**
  - 用什么：`nav.goToPose(goal)`（发完马上返回，不会等机器人开到）

- **等待**
  - 用什么：`while not nav.isTaskComplete():`

- **拿结果**
  - 用什么：`nav.getResult()`，跟 `TaskResult.SUCCEEDED / FAILED / CANCELED` 比较

- **打日志**
  - 用什么：`nav.get_logger().info('...')`

- **结束**
  - 用什么：`rclpy.shutdown()`

③ 在 `setup.py` 的 `console_scripts` 里注册：
```python
'patrol_node = port_patrol.patrol_node:main',
```

**之后的小步：** 5.3 从 YAML 读多个巡逻点；5.4 加超时（`nav.cancelTask()`）、失败就跳过、最后打印总结。

**做错了什么 → 怎么改的**

- **`ros2 pkg create` 之后打印出一串许可证名字（MIT、GPL-3.0…），以为出错了**
  - 结果：其实 package 已经建好了
  - 正确理解：那只是提示"你没指定许可证，可选的有这些"。用 `ls` 或 `find` 看一下文件有没有生成就知道了

### 第 7 步：最终测试（还没做）

同一段路线来回跑两次：A→B 路线畅通；B→A 在 Gazebo 里放一个方块挡在路上（左上角方块图标）。每次记录 Feedback、Time taken、Recoveries，以及机器人是绕过去 / 卡住 / 放弃。

**面试准备（参考答案要改成我自己的话）**

**面试题：地图里没有的新障碍物，Nav2 是怎么"看到"并避开的？**
costmap 除了静态地图层（static layer），还有障碍物层（obstacle layer），它会实时读激光数据，把新看到的障碍物加进 costmap。controller 和 planner 都会根据更新后的 costmap 绕开它。

---

## 4. 遇到的问题和解决方法

- **1**
  - 现象：teleop 只能转弯、不会直走
  - 原因：每按一次 `w` 只加 0.01 m/s；之前按过的转向速度还在
  - 解决：按 `s` 清零，再连按 `w` 大约 10 次

- **2**
  - 现象：机器人撞到柱子后，SLAM 地图乱了（红色激光点和墙对不上）
  - 原因：撞墙时轮子打滑，**里程计（odometry）**以为车还在往前走，地图跟着画歪；转向太快也会加重
  - 解决：重启 Gazebo 和 SLAM 重新建图；开慢一点，不要撞

- **3**
  - 现象：`ros2 topic pub --once /initialpose` 发了但没反应
  - 原因：`--once` 发完就退出，可能还没和 AMCL 连上，消息丢了
  - 解决：改用 `--times 3 -r 1`（每秒发 1 次，发 3 次）

- **4**
  - 现象：加了 `-w 2` 后一直显示 "Waiting for at least 2 matching subscription(s)"
  - 原因：订阅 `/initialpose` 的只有 AMCL 一个，RViz 是发布方
  - 解决：`Ctrl+C`，不用 `-w 2`

- **5**
  - 现象：AMCL 日志：`Received initialpose message is malformed. Rejecting.`
  - 原因：四元数用了四舍五入的值（z 0.87, w 0.49），平方和 0.997，Nav2 要求误差 < 0.0001
  - 解决：用精确值（z 0.870356, w 0.492424），并加上 covariance

- **6**
  - 现象：Navigation 一直 inactive，点 Startup 没用
  - 原因：Nav2 第一次启动只成功了一半（controller_server active，其他 inactive），再点 Startup 会去配置已经 active 的节点而报错
  - 解决：先 Reset 再 Startup；最好的办法是：Nav2 一启动就马上设置初始位置

- **7**
  - 现象：点 Reset 后 Nav2 整个退出了
  - 原因：Nav2 进程崩溃（exit code -6）
  - 解决：重新启动 Nav2，马上发初始位置，这次全部 active

- **8**
  - 现象：发了目标，路线也画出来了，但机器人不动，Recoveries 一直增加，日志里有 `Failed to make progress`
  - 原因：电脑上 Gazebo 跑得慢，`/scan` 大约 0.6 秒才来一次；`collision_monitor` 认为超过 0.2 秒的激光数据是过期的，就把所有运动命令拦下来
  - 解决：把 TurtleBot3 的 Nav2 配置复制到 `config/nav2_burger.yaml`，把 `scan.source_timeout` 从 0.2 改成 2.0，启动 Nav2 时加上 `params_file:=...`

- **9**
  - 现象：想关掉程序时，`Ctrl+C`（SIGINT）关不掉
  - 原因：Gazebo 的服务端进程卡住了
  - 解决：最后用强制结束（kill）关掉

**第 8 个问题最适合写进 README 的"遇到的真实问题"一节。**

**查问题用过的方法：**
```bash
ros2 node list                              # 看有哪些节点在运行
ros2 topic info -v /cmd_vel                 # 看谁在发、谁在收，消息类型是什么
ros2 topic hz /scan                         # 看话题频率（我的电脑上只有约 1.6–2.3 Hz）
ros2 lifecycle get /planner_server          # 看 Nav2 服务器是 active 还是 inactive
ros2 run tf2_ros tf2_echo map odom          # 看坐标变换是否存在（定位成功才会有 map→odom）
ros2 param get /collision_monitor scan.source_timeout   # 查参数
```

---

## 5. 概念讲解

- **SLAM**：机器人一边移动、一边用激光扫描，同时**画地图**和**算出自己在地图上的位置**。
- **占用栅格地图（occupancy grid map）**：把地图切成小格子（我们的是每格 5 cm），每格标成空地 / 障碍物 / 未知三种状态。`.pgm` 是地图图片；`.yaml` 记录分辨率（每格多少米）和原点。
- **里程计（odometry）**：根据轮子转了多少圈，推算车走了多远。轮子打滑时就会算错。
- **use_sim_time**：让节点使用 Gazebo 发布的仿真时钟（`/clock`），而不是电脑的真实时间。
- **RViz vs Gazebo**：Gazebo 是仿真世界（物理、传感器）；RViz 只是显示工具，看 ROS 里的数据，本身不做计算。
- **AMCL**：Nav2 里负责**定位**的节点。它在一张**已知地图**上，用激光数据和一大堆"粒子"（RViz 里的绿色小箭头）猜机器人在哪里。它需要一个大概的初始位置作为起点。
- **建图 vs 定位**：SLAM 是"没有地图，边走边画"；AMCL 是"已经有地图，只算我在哪"。
- **四元数（quaternion）**：ROS 里表示朝向的方式。只绕竖直轴转 θ 角时：`z = sin(θ/2)`，`w = cos(θ/2)`。四个数的平方和必须等于 1。
- **协方差（covariance）**：表示"我对这个位置有多不确定"。给初始位置加一点不确定度，AMCL 的粒子会散开一些，它才能自己修正小误差。
- **costmap（代价地图）**：在地图上标出每个位置有多"危险"。越靠近障碍物，代价越高（RViz 里颜色越深）。分为 global costmap（全局，用来规划路线）和 local costmap（局部，机器人周围，实时更新）。
- **全局规划器（planner）vs 控制器（controller）**：planner 在整张地图上算出一条从起点到终点的路线；controller 沿着这条路线，结合 local costmap，每一刻算出具体的速度（`/cmd_vel`）。
- **生命周期节点（lifecycle node）**：Nav2 的服务器有 unconfigured → inactive → active 几种状态，由 `lifecycle_manager` 按顺序启动。全部 active 之后才能导航。
- **collision_monitor**：Nav2 里最后一道安全关卡。它在速度命令发给轮子之前，检查激光数据里有没有快撞上的东西；数据过期时，它宁可不让机器人动。
- **Action**：用来执行"要花一段时间"的任务。客户端发出目标（goal），过程中会收到反馈（feedback），最后拿到结果（result），中途还可以取消。导航就是一个 action：`NavigateToPose`。
- **topic vs service vs action**：
  - topic：持续广播，没有回应（比如 `/scan`、`/cmd_vel`）
  - service：一问一答，适合很快能完成的事
  - action：耗时任务，有反馈，可以取消
- **package / colcon**：package 是 ROS 2 代码的打包单位；colcon 是编译工具，把 package 编译、安装后，才能用 `ros2 run` 运行。
- **异步（asynchronous）**：`goToPose()` 发出目标后马上返回，不会等机器人开到，所以需要自己用循环去等结果。

---

## 6. 诚实记录（写 README 时要用）

- **建图时的驾驶**：第二次建图是 Claude 用脚本发 `/cmd_vel` 命令慢慢开的，因为我用 teleop 不好控制。README 里要写明"建图时的驾驶由 AI 辅助完成"。
- **Nav2 的启动和排错**：Nav2 卡在一半、崩溃、机器人不动这几个问题，是 Claude 帮我查日志、重启 Nav2 解决的。
- **`config/nav2_burger.yaml`**：复制自 TurtleBot3 官方配置，只改了 `scan.source_timeout` 一个参数（Claude 改的，原因写在文件注释里）。
- **巡逻节点**：由我自己写（option a），Claude 只给提示和检查。

---

## 7. 命令速查

```bash
# Git
git status                          # 看哪些文件改了
git add <文件...>                   # 选出要提交的文件
git commit -m "<我的提交信息>"      # 保存一个版本
git push                            # 上传到 GitHub

# 编译和运行自己的 package（5.2 写完代码后会用到）
cd ~/turtlebot3-port-patrol
colcon build --packages-select port_patrol
source install/setup.bash
ros2 run port_patrol patrol_node
```
