# 学习日志 (LEARNING_LOG)

> 用我自己的话记录。每个里程碑写：学到了什么；遇到问题时写：现象 / 原因 / 解决方法。

## Day 1

Day 1 笔记（2026-10-14）

一、环境检查
- 系统：Windows 11 + WSL2 + Ubuntu 24.04
- VS Code 已经连接到 WSL，在 VS Code 终端里就能操作 Ubuntu
- WSL 只分到 7.7 GB 内存，以后跑 Gazebo 可能会慢

二、遇到的问题：sudo 密码
- 现象：运行安装脚本时，sudo 要输入密码，输错两次后脚本停止
- 原因：sudo 要的是 WSL 里 Ubuntu 用户 zhang 的密码，不是 Windows 密码，而我不知道这个密码
- 解决：在 Windows PowerShell 里运行
    wsl -l -v                                  （查看 Linux 系统的名字：Ubuntu-24.04）
    wsl -d Ubuntu-24.04 -u root passwd zhang   （用 root 身份给 zhang 设置新密码）
- 补充：在 Linux 里输入密码时屏幕不显示任何字符，这是正常的
- 补充：sudo 只记住密码 15 分钟，安装时间长的话会再问一次

三、安装 ROS 2 Jazzy
- 按照 docs.ros.org 官方步骤，安装了 ros-jazzy-desktop 和 ros-dev-tools
- 安装位置：/opt/ros/jazzy/

四、source
- source /opt/ros/jazzy/setup.bash：告诉当前终端 ROS 装在哪里
- 不 source，就会报 ros2: command not found
- source 只对当前终端有效
- 已经写进 ~/.bashrc，以后每个新终端会自动 source
- 检查方法：printenv | grep ROS，应该能看到 ROS_DISTRO=jazzy

五、节点（node）和话题（topic）
- 节点：一个正在运行的 ROS 程序
- 话题：节点之间传消息的频道
- 演示：
    终端1：ros2 run demo_nodes_cpp talker     （往 /chatter 发消息）
    终端2：ros2 run demo_nodes_py listener    （从 /chatter 收消息）
- 发现：停掉 talker，listener 不会崩溃，只是收不到消息；talker 重启后，listener 又能自动收到
- 原因：节点互相独立，只通过话题联系
- 比喻：talker = 电台主持人，/chatter = 频道，listener = 收音机

六、今天用到的命令
    ros2 --help
    source /opt/ros/jazzy/setup.bash
    printenv | grep ROS
    ros2 run <包名> <程序名>
    Ctrl+C   停止正在运行的程序
