"""Generate the nine simplified MID360/cage meshes. Requires numpy and trimesh.

Generated 2026-11-16 from installation photos and nominal Livox dimensions.
License: Apache-2.0, see ../licenses/PROJECT_LICENSE.txt.
"""
from pathlib import Path
import argparse
import numpy as np
import trimesh


def box(size, pos):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(pos)
    return mesh


def cylinder(radius, height, pos, axis=None, sections=48):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    if axis is not None:
        mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], axis))
    mesh.apply_translation(pos)
    return mesh


def rounded_plate(width, depth, radius, height, z):
    outline = []
    for cx, cy, start in [(width/2-radius, depth/2-radius, 0),
                           (-width/2+radius, depth/2-radius, 90),
                           (-width/2+radius, -depth/2+radius, 180),
                           (width/2-radius, -depth/2+radius, 270)]:
        for angle in np.linspace(start, start+90, 9):
            a = np.deg2rad(angle)
            outline.append([cx+radius*np.cos(a), cy+radius*np.sin(a)])
    n = len(outline)
    verts = [[x, y, z-height/2] for x, y in outline]
    verts += [[x, y, z+height/2] for x, y in outline]
    verts += [[0, 0, z-height/2], [0, 0, z+height/2]]
    faces = []
    for i in range(n):
        j = (i+1) % n
        faces += [[2*n, j, i], [2*n+1, n+i, n+j],
                  [i, j, n+j], [i, n+j, n+i]]
    return trimesh.Trimesh(vertices=verts, faces=faces, process=True)


def dome():
    # Closed oblate hemisphere: bottom z=.034, apex z=.060, diameter .054 m.
    n, rings = 96, 24
    verts = [[0, 0, .060]]
    for theta in np.linspace(0, np.pi/2, rings+1)[1:]:
        for phi in np.linspace(0, 2*np.pi, n, endpoint=False):
            verts.append([.027*np.sin(theta)*np.cos(phi),
                          .027*np.sin(theta)*np.sin(phi), .034+.026*np.cos(theta)])
    verts.append([0, 0, .034])
    faces = [[0, 1+i, 1+(i+1) % n] for i in range(n)]
    for r in range(rings-1):
        for i in range(n):
            a, b = 1+r*n+i, 1+r*n+(i+1) % n
            faces += [[a, a+n, b+n], [a, b+n, b]]
    last = 1+(rings-1)*n
    for i in range(n):
        faces.append([len(verts)-1, last+(i+1) % n, last+i])
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    mesh.fix_normals()
    return mesh


def geometry():
    silver = [.72, .76, .80, 1]
    parts = []
    def add(body, name, meshes, color, metallic=.6, roughness=.3):
        mesh = trimesh.util.concatenate(meshes)
        mesh.fix_normals()
        assert mesh.is_watertight and mesh.volume > 0, name
        parts.append(dict(body=body, name=name, mesh=mesh, color=color,
                          metallic=metallic, roughness=roughness))
    # The cage/feet are an approximate interpretation of the installation photos.
    mounts = [rounded_plate(.080, .080, .005, .003, .018)]
    mounts += [box([.014, .064, .016], [x, 0, .008]) for x in [-.026, .026]]
    # Open upper frame around the device flange, carried by four brass posts.
    mounts += [box([.080, .007, .002], [0, y, .0545]) for y in [-.0365, .0365]]
    mounts += [box([.007, .066, .002], [x, 0, .0545]) for x in [-.0365, .0365]]
    add("mid360_mount", "mount_aluminum", mounts, silver)
    posts = [cylinder(.0025, .035, [x, y, .0365], sections=6)
             for x in [-.035, .035] for y in [-.035, .035]]
    add("mid360_mount", "mount_posts", posts, [.61, .43, .17, 1], .75, .25)
    screws = [cylinder(.0031, .0020, [x, y, .0565], sections=12)
              for x in [-.035, .035] for y in [-.035, .035]]
    screws += [cylinder(.0025, .002, [x, y, .0205], sections=12)
               for x in [-.026, .026] for y in [-.023, .023]]
    add("mid360_mount", "mount_screws", screws, [.40, .43, .46, 1], .8, .24)
    core = [box([.052, .049, .030], [0, 0, .016])]
    core += [box([.0016, .065, .030], [x, 0, .016])
             for x in np.linspace(-.026, .026, 11)]
    core += [rounded_plate(.065, .065, .004, .003, .0015)]
    add("mid360_link", "heat_sink", core, [.37, .40, .43, 1], .8, .34)
    add("mid360_link", "front_panel", [box([.002, .050, .026], [.031, 0, .017])],
        [.035, .042, .050, 1], .15, .32)
    lid = [rounded_plate(.065, .065, .005, .003, .0325),
           cylinder(.0294, .002, [0, 0, .034])]
    lid += [cylinder(.002, .0018, [x, y, .0349], sections=12)
            for x in [-.0265, .0265] for y in [-.0265, .0265]]
    add("mid360_link", "top_flange", lid, silver, .8, .20)
    add("mid360_link", "glass_dome", [dome()], [.018, .045, .095, 1], .35, .10)
    add("mid360_link", "connector", [cylinder(.005, .016, [-.039, 0, .024], axis=[1, 0, 0]),
        cylinder(.0057, .003, [-.0335, 0, .024], axis=[1, 0, 0], sections=6)],
        [.025, .030, .035, 1], .15, .4)
    points = [[-.047, 0, .024], [-.063, 0, .024], [-.078, .003, .019],
              [-.089, .008, .008], [-.101, .014, -.010]]
    wire = []
    for a, b in zip(points, points[1:]):
        a, b = np.array(a), np.array(b)
        wire.append(cylinder(.0024, np.linalg.norm(b-a), (a+b)/2, axis=b-a, sections=16))
    for p in points[1:-1]:
        cap = trimesh.creation.icosphere(subdivisions=2, radius=.0024)
        cap.apply_translation(p)
        wire.append(cap)
    add("mid360_link", "cable", wire, [.018, .022, .026, 1], 0, .6)
    return parts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'meshes/mid360')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for part in geometry():
        part['mesh'].export(args.output / (part['name'] + '.stl'))
    print('Generated 9 meshes. Refresh previews and SHA256SUMS after any change.')


if __name__ == '__main__':
    main()
