"""Render the assembly and installation views with MuJoCo (EGL by default)."""
from pathlib import Path
import os
import xml.etree.ElementTree as ET

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def main():
    root = ET.parse(ROOT / "mujoco/scene.xml").getroot()
    root.find("include").set("file", str(ROOT / "mujoco/go2_piper_d435_mid360.xml"))
    asset = ET.SubElement(root, "asset")
    ET.SubElement(asset, "texture", type="skybox", builtin="gradient", rgb1=".16 .20 .25",
                  rgb2=".58 .64 .70", width="512", height="512")
    global_settings = root.find("visual/global")
    global_settings.set("offwidth", "1600")
    global_settings.set("offheight", "1200")
    ET.SubElement(root.find("worldbody"), "light", pos="1 -2 2", dir="-1 2 -1.5", diffuse=".55 .55 .55")
    model = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding="unicode"))
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    renderer = mujoco.Renderer(model, width=1200, height=900)
    options = mujoco.MjvOption()
    options.geomgroup[3] = 0
    options.sitegroup[:] = 0
    base_pos = data.xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "base")]
    target = base_pos + np.array([.205, 0, .12])
    views = [
        ("assembly", [0.025, 0, .34], 1.25, 125, -22),
        ("front", [0.025, 0, .34], 1.05, 180, 0),
        ("left", [0.025, 0, .34], 1.15, 270, 0),
        ("top", [-.025, 0, .29], 1.05, 270, -89.9),
        ("mid360_detail", target, .37, 225, -18),
    ]
    preview_dir = ROOT / "previews"
    preview_dir.mkdir(exist_ok=True)
    images = {}
    for name, lookat, distance, azimuth, elevation in views:
        camera = mujoco.MjvCamera()
        camera.lookat[:] = lookat
        camera.distance = distance
        camera.azimuth = azimuth
        camera.elevation = elevation
        renderer.update_scene(data, camera, scene_option=options)
        image = Image.fromarray(renderer.render())
        images[name] = image
        image.save(ROOT / "preview.png" if name == "assembly" else preview_dir / f"{name}.png")
    renderer.close()
    canvas = Image.new("RGB", (1600, 1280), (24, 30, 39))
    draw = ImageDraw.Draw(canvas)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 24) if Path(font_path).exists() else ImageFont.load_default()
    for i, (name, title) in enumerate([
        ("front", "FRONT (+X)"), ("left", "LEFT (+Y)"),
        ("top", "TOP (+Z)"), ("mid360_detail", "MID360 MOUNT DETAIL"),
    ]):
        x, y = (i % 2)*800, (i // 2)*640
        canvas.paste(images[name].resize((800, 600), Image.Resampling.LANCZOS), (x, y+40))
        draw.text((x+22, y+9), title, font=font, fill=(225, 233, 243))
    canvas.save(ROOT / "installation_views.png")
    print("Rendered preview.png, installation_views.png and previews/*.png")


if __name__ == "__main__":
    main()
