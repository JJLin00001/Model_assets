# Model_assets：Go2 / Piper / D435 模型资产

本仓库提供两套可独立复制、使用的机器人模型资产，包含网格、模型描述、相机安装坐标、预览图和校验工具。

| 资产目录 | 模型组成 | 基座形式 | 活动关节 | D435 数量 |
| --- | --- | --- | --- | --- |
| `go2_piper_d435_assets` | Go2 四足机器人 + Piper 六轴机械臂 + 双指夹爪 + 腕部连接件 | 浮动基座 | 20：四足 12 + 机械臂 6 + 夹爪 2 | 2：头部、腕部 |
| `piper_d435_assets` | Piper 六轴机械臂 + 双指夹爪 + 腕部连接件 | 固定底座 | 8：机械臂 6 + 夹爪 2 | 1：腕部 |

两套资产均包含 URDF、MuJoCo MJCF、Gazebo SDF、Isaac Sim USD 和 Isaac Lab 配置参考。资产为描述文件和几何资源；站立、抓取、真实硬件驱动及 ROS 2 控制器需由使用项目接入。

## 1. 克隆仓库

```bash
git clone https://github.com/JJLin00001/Model_assets.git
cd Model_assets
```

后续示例默认仓库克隆在 `~/Model_assets`。如果使用其他位置，请把命令中的 `~/Model_assets` 替换为实际路径。

```text
Model_assets/
├── readme.md
├── go2_piper_d435_assets/
└── piper_d435_assets/
```

每套资产目录包含：

```text
<asset_package>/
├── CMakeLists.txt             # ROS 2 ament_cmake 安装配置
├── package.xml               # ROS 2 包信息
├── urdf/                     # 相对网格路径版与 package:// 路径版 URDF
├── meshes/                   # 包内网格及来源网格
├── mujoco/                   # 机器人 MJCF 与带地面场景
├── gazebo/                   # 模型 SDF 与静态预览 world
├── isaac_sim/                # 自包含 USD、Isaac Lab 配置参考
├── model.config              # Gazebo 模型入口
├── README.md                 # 对应资产的详细说明
├── preview.png               # MuJoCo 实际渲染预览
├── validate.py               # 文件、资源与模型校验脚本
├── VALIDATION.md             # 已完成的验证及范围
├── joint_metadata.json       # 关节限位、夹爪约定
├── asset_manifest.json       # 来源记录
├── SHA256SUMS                # 文件校验哈希
└── licenses/                 # 上游许可证与来源说明
```

## 2. 适配环境与验证范围

当前开发机器为 **Ubuntu 24.04.3 LTS**，安装 **ROS 2 Jazzy**。各格式的验证范围如下，不能将格式可读取等同于完整仿真验收。

| 使用方式 | 环境 / 依赖 | 已验证范围 |
| --- | --- | --- |
| ROS 2 / RViz | Ubuntu 24.04、ROS 2 Jazzy、ament_cmake、colcon、RViz2、robot_state_publisher、joint_state_publisher_gui | 两套资产的 URDF 均通过原生 `check_urdf` 解析；构建及 RViz 操作见下文 |
| MuJoCo | 已验证 MuJoCo 3.9.0；物理校验需要 NumPy、SciPy | 两套资产的编译、运动学、短时步进和 EGL 离屏预览通过 |
| Isaac Sim / OpenUSD | 支持 USD 的 Isaac Sim / OpenUSD 环境 | USD 打开、资源闭包、物理层级及位姿检查通过；未进行 Isaac Sim GUI 运行验收 |
| Isaac Lab | 自行配置匹配的 Isaac Sim / Isaac Lab 环境 | 提供 `model_cfg.py` 参考；未指定已验收的 Isaac Lab 版本组合 |
| Gazebo Sim | SDF 1.9，预览 world 面向 Gazebo Sim Harmonic | XML、资源和运动学已检查；未进行 Gazebo 原生启动、渲染及动力学验收 |

其他 Linux 发行版、ROS 2 版本以及 Windows/macOS 未进行完整验收。只使用 MuJoCo 或 USD 时，无需编译 ROS 2 包。

## 3. ROS 2 环境准备

以下命令假设已安装 ROS 2 Jazzy，且 `/opt/ros/jazzy/setup.bash` 存在。缺少相关组件时，可安装：

```bash
sudo apt update
sudo apt install \
  python3-colcon-common-extensions \
  python3-catkin-pkg \
  ros-jazzy-ament-cmake \
  ros-jazzy-rviz2 \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher-gui
```

### 避免 Conda 干扰系统 ROS 2

如果终端提示符带有 `(base)`，先退出 Conda，再加载 ROS 环境：

```bash
conda deactivate
source /opt/ros/jazzy/setup.bash
```

如果希望新终端默认不激活 Conda base，只需执行一次：

```bash
conda config --set auto_activate_base false
```

然后重新打开终端。若激活过多层 Conda 环境，需要重复 `conda deactivate`，直到退出 Conda。

## 4. 编译模型描述包

可直接在仓库根目录编译两套资产，无需移动到其他工作空间：

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Model_assets

colcon build \
  --base-paths ./go2_piper_d435_assets ./piper_d435_assets \
  --packages-select go2_piper_d435_assets piper_d435_assets \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3

source install/setup.bash
```

仅编译 Piper + 单 D435：

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Model_assets

colcon build \
  --base-paths ./piper_d435_assets \
  --packages-select piper_d435_assets \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3

source install/setup.bash
```

构建输出位于根目录的 `build/`、`install/`、`log/`。编译仅安装模型描述和网格，不编译控制程序。也可以将资产包放进已有 ROS 2 工作空间的 `src/`，在该工作空间根目录按包名编译。

确认包可被找到：

```bash
ros2 pkg prefix piper_d435_assets
# 如果也编译了完整 Go2 资产：
ros2 pkg prefix go2_piper_d435_assets
```

### 修复 `ModuleNotFoundError: No module named 'catkin_pkg'`

如果报错中出现 `/home/.../anaconda3/bin/python3`，说明 CMake 选择了 Conda Python。退出 Conda，并刷新该包 CMake 缓存、指定系统 Python：

```bash
conda deactivate
source /opt/ros/jazzy/setup.bash
cd ~/Model_assets

colcon build \
  --base-paths ./piper_d435_assets \
  --packages-select piper_d435_assets \
  --cmake-clean-cache \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3

source install/setup.bash
```

若系统 Python 本身也缺失模块，执行 `sudo apt install python3-catkin-pkg`。无需为此向 Conda base 安装 ROS 构建依赖。

## 5. 使用 RViz 查看模型

以下示例查看 **Piper + 单 D435**。先完成上一节构建，再打开三个终端。每个终端都需要加载 ROS 和本仓库安装环境。

### 终端 1：发布机器人模型和 TF

```bash
source /opt/ros/jazzy/setup.bash
source ~/Model_assets/install/setup.bash

ASSET_SHARE="$(ros2 pkg prefix --share piper_d435_assets)"
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat "$ASSET_SHARE/urdf/piper_d435.ros.urdf")"
```

### 终端 2：发布并调节关节状态

```bash
source /opt/ros/jazzy/setup.bash
source ~/Model_assets/install/setup.bash
ros2 run joint_state_publisher_gui joint_state_publisher_gui
```

保持终端 1 运行，关节界面会读取 `/robot_description`，通过 `/joint_states` 发布关节位置。

### 终端 3：启动 RViz

```bash
source /opt/ros/jazzy/setup.bash
source ~/Model_assets/install/setup.bash
rviz2
```

在 RViz 中：

1. 将 **Global Options → Fixed Frame** 设置为 `base`。
2. 点击 **Add → RobotModel**。
3. 将 RobotModel 的 **Description Source** 设为 `Topic`，**Description Topic** 设为 `/robot_description`。
4. 根据需要添加 **TF**、**Grid**，调整视角；拖动关节界面的滑块即可查看机械臂姿态。
5. 可通过 **File → Save Config As** 保存自己的 `.rviz` 配置，下次使用 `rviz2 -d /path/to/model.rviz` 打开。

### 查看 Go2 + Piper + 双 D435

先停止上一套模型的三个进程，再将终端 1 替换为：

```bash
source /opt/ros/jazzy/setup.bash
source ~/Model_assets/install/setup.bash

ASSET_SHARE="$(ros2 pkg prefix --share go2_piper_d435_assets)"
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat "$ASSET_SHARE/urdf/go2_piper_d435.ros.urdf")"
```

终端 2、3 和 RViz 设置相同。默认命名下，一次查看一套模型，以避免 `/robot_description`、`/joint_states` 和同名 TF 帧相互覆盖。

### RViz 常见问题

| 现象 | 检查方式 |
| --- | --- |
| 提示找不到资产包 | 确认构建成功，并在当前终端执行 `source ~/Model_assets/install/setup.bash` |
| RobotModel 网格加载失败 | 使用 `.ros.urdf` 版本，确认 `package://` 对应的包已安装并 source；保持 `meshes/` 目录完整 |
| 模型不出现或提示 Fixed Frame 不存在 | 设置 Fixed Frame 为 `base`；检查 robot_state_publisher 是否正常启动 |
| 连杆提示缺少变换 | 保持关节界面运行，检查 `ros2 topic echo /joint_states --once` 是否有消息 |
| RobotModel 没收到描述 | 选择 Topic 来源及 `/robot_description`；必要时将描述订阅的 Durability 设为 `Transient Local` |

RViz 用于模型与坐标显示，不执行动力学，也不会自动生成 D435 图像。

## 6. 使用 MuJoCo

MuJoCo 直接读取包内 MJCF，无需 ROS 2 编译。可使用单独 Python 环境：

```bash
python3 -m venv ~/venvs/model_assets
source ~/venvs/model_assets/bin/activate
python -m pip install 'mujoco==3.9.0' numpy scipy
```

如果 Ubuntu 缺少 `venv`，先安装 `python3-venv`。

打开 Piper + 单 D435：

```bash
cd ~/Model_assets
python -m mujoco.viewer --mjcf=piper_d435_assets/mujoco/scene.xml
```

打开 Go2 + Piper + 双 D435：

```bash
cd ~/Model_assets
python -m mujoco.viewer --mjcf=go2_piper_d435_assets/mujoco/scene.xml
```

代码中读取场景并使用 `home` 姿态：

```python
from pathlib import Path
import mujoco

bundle = Path.home() / "Model_assets" / "piper_d435_assets"
model = mujoco.MjModel.from_xml_path(str(bundle / "mujoco/scene.xml"))
data = mujoco.MjData(model)
mujoco.mj_resetDataKeyframe(model, data, 0)
mujoco.mj_forward(model, data)
```

Piper 模型为 `nq=8`、`nv=8`、7 个执行器、1 台相机；Go2 组合模型为 `nq=27`、`nv=26`、19 个执行器、2 台相机。模型保留力矩/力控制接口，初始姿态不提供抗重力或站立控制；开始物理步进后，姿态会随动力学变化。

## 7. 使用 Isaac Sim / Isaac Lab

在 Isaac Sim 中通过 **File → Open** 打开以下任一文件，或将其作为 reference 加入场景：

| 模型 | USD 路径 | 默认 prim |
| --- | --- | --- |
| Piper + 单 D435 | `piper_d435_assets/isaac_sim/piper_d435.usd` | `/piper_d435` |
| Go2 + Piper + 双 D435 | `go2_piper_d435_assets/isaac_sim/go2_piper_d435.usd` | `/go2_piper_d435` |

USD 的几何与物理描述已封装，读取 USD 本身不依赖其他资产目录。统一使用米制、Z 向上。

Isaac Lab 配置参考位于各资产目录的 `isaac_sim/model_cfg.py`，Piper 使用 `PIPER_D435_CFG`，Go2 组合模型使用 `GO2_PIPER_CFG`。应在配置好 Isaac Lab 的环境内导入，再接入自己的场景、PhysicsScene 和控制逻辑。

USD 提供 D435 外观及 `WristCameraOpticalFrame`；Go2 模型还提供 `HeadCameraOpticalFrame`。获取 RGB-D 图像需另建相机传感器。光学坐标为 X 向右、Y 向下、Z 向前；安装位姿沿用 CAD 名义值。

## 8. 使用 Gazebo Sim

以下命令假设已安装 Gazebo Sim Harmonic。保持资产文件夹名称不变，并将仓库根目录加入资源搜索路径：

```bash
cd ~/Model_assets
export GZ_SIM_RESOURCE_PATH="$PWD${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"

# 二选一：
gz sim piper_d435_assets/gazebo/preview.sdf
# gz sim go2_piper_d435_assets/gazebo/preview.sdf
```

可在已安装 `gz sdf` 的环境内检查 SDF：

```bash
gz sdf -k piper_d435_assets/gazebo/model.sdf
gz sdf -k go2_piper_d435_assets/gazebo/model.sdf
```

`preview.sdf` 将整机设为静态，便于查看装配，并包含示例 RGB-D 传感器。动态使用时在自己的 world 引用对应 `model://..._assets` 模型、设置初始关节状态并接入控制器。Piper 模型的 `world_fixed` 始终固定底座；Go2 模型为浮动基座。

SDF 1.9 中未配置夹爪 mimic 插件，动态控制需同时向两指发送位置目标。相机为通用渲染传感器，不代表完整 D435 硬件成像模型。

## 9. 关节与装配约定

- Piper 六轴关节名为 `joint1`–`joint6`，双指关节为 `joint7`、`joint8`。
- 夹爪总开口：`opening_m = joint7 - joint8`；对称目标：`joint7 = opening_m / 2`、`joint8 = -opening_m / 2`。
- 建议总开口范围为 `0–0.076 m`，模型硬限位允许 `0–0.10 m`。
- MuJoCo 使用 equality 耦合，URDF 带 mimic；其他控制栈需确认其耦合支持，必要时同时控制两指。
- 独立 Piper 底座 CAD 原点位于模型原点，`joint1` 相对底座高度为 `0.123 m`。支架和相机随 `link6` 运动。
- 相机、支架已包含于源模型的复合惯量，不重复增加质量。独立 Piper 底座惯量在源包中与 Go2 合并，因此本资产采用固定底座，未推测其独立动力学参数。
- 各格式与配置的控制参数可能存在差异，详见对应资产 README 与 `joint_metadata.json`。

## 10. 校验资产

标准库校验，无需 ROS 2 或仿真器：

```bash
cd ~/Model_assets
python3 piper_d435_assets/validate.py
python3 go2_piper_d435_assets/validate.py
```

在安装了 MuJoCo、NumPy、SciPy 的 Python 环境中进行物理校验：

```bash
python piper_d435_assets/validate.py --physics
python go2_piper_d435_assets/validate.py --physics
```

Go2 资产还提供 USD 检查选项，需使用可导入 `pxr` 的 Python 环境：

```bash
python go2_piper_d435_assets/validate.py --usd
```

具体历史验证结果见 [Piper 校验记录](piper_d435_assets/VALIDATION.md) 与 [Go2 组合模型校验记录](go2_piper_d435_assets/VALIDATION.md)。修改资产包内已记录文件后，哈希校验会报告变化；重新导出或维护资产时需同步更新相应清单。

## 11. 预览与许可证

### Piper + 单 D435

![Piper 与腕部 D435](piper_d435_assets/preview.png)

详细说明：[piper_d435_assets/README.md](piper_d435_assets/README.md)。

### Go2 + Piper + 双 D435

![Go2、Piper 与双 D435](go2_piper_d435_assets/preview.png)

详细说明：[go2_piper_d435_assets/README.md](go2_piper_d435_assets/README.md)。

模型包含不同上游来源的资源，使用和分发时请保留各资产目录的 `licenses/`，并遵循对应许可证与 `SOURCES.md` 中的说明。
