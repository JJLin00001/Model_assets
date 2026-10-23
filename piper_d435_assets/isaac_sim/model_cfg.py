"""Fixed-base Piper + wrist D435. Requires Isaac Lab."""
from pathlib import Path
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
PIPER_D435_CFG = ArticulationCfg(
    prim_path="/World/Piper",
    spawn=sim_utils.UsdFileCfg(
        usd_path=str(Path(__file__).with_name("piper_d435.usd")),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(enabled_self_collisions=False),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0., 0., 0.), joint_pos={"joint[1-6]": 0., "joint7": .038, "joint8": -.038},
        joint_vel={".*": 0.},
    ),
    actuators={
        "arm_large": ImplicitActuatorCfg(joint_names_expr=["joint[1-3]"], effort_limit_sim=32., velocity_limit_sim=5., stiffness=360., damping=20.),
        "arm_small": ImplicitActuatorCfg(joint_names_expr=["joint[4-6]"], effort_limit_sim=8., velocity_limit_sim=5., stiffness=60., damping=3.),
        "gripper": ImplicitActuatorCfg(joint_names_expr=["joint[78]"], effort_limit_sim=10., velocity_limit_sim=1., stiffness=800., damping=5.),
    },
)
