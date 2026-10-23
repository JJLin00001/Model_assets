"""Validate the portable fixed-base Piper and wrist D435 bundle."""
from pathlib import Path
import argparse, hashlib, json, xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parent

def check(ok,msg):
    if not ok: raise ValueError(msg)

def static_checks():
    count=0
    for line in (ROOT/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1);p=ROOT/name
        check(p.is_file() and not p.is_symlink(),f'Missing or symlink: {name}')
        check(hashlib.sha256(p.read_bytes()).hexdigest()==digest,f'Hash mismatch: {name}');count+=1
    refs=0
    for p in ROOT.rglob('*'):
        if p.suffix not in {'.xml','.sdf','.urdf','.config'}:continue
        r=E.parse(p).getroot()
        for e in r.iter():
            filenames=[]
            if e.tag=='mesh':filenames=[e.get(k) for k in ['file','filename'] if e.get(k)]
            if e.tag=='include' and e.get('file'):filenames.append(e.get('file'))
            if e.tag=='uri' and e.text:filenames.append(e.text)
            for name in filenames:
                if name=='model://piper_d435_assets':target=ROOT/'model.config'
                elif name.startswith(('package://piper_d435_assets/','model://piper_d435_assets/')):target=ROOT/name.split('/',3)[3]
                else:
                    check(not Path(name).is_absolute(),f'Absolute dependency: {name}');target=p.parent/name
                target=target.resolve();check(target.is_relative_to(ROOT) and target.is_file(),f'Invalid resource: {name}');refs+=1
    for p in ROOT.rglob('*.obj'):
        check(not any(x.lstrip().startswith(('mtllib ','usemtl ')) for x in p.read_text().splitlines()),f'OBJ external material: {p}')
    for file in ['piper_d435.urdf','piper_d435.ros.urdf']:
        u=E.parse(ROOT/'urdf'/file).getroot();links={l.get('name') for l in u.findall('link')};children=[j.find('child').get('link') for j in u.findall('joint')]
        check(len(children)==len(set(children)) and links-set(children)=={'base'},'URDF tree invalid')
        check({j.get('name') for j in u.findall('joint') if j.get('type')!='fixed'}=={f'joint{i}' for i in range(1,9)},'Wrong moving joints')
        check(u.find("joint[@name='joint8']/mimic").get('multiplier')=='-1','Wrong mimic')
        check('HeadCameraOpticalFrame' not in links,'Head camera retained')
    s=E.parse(ROOT/'gazebo/model.sdf').getroot().find('model')
    check(len(s.findall(".//sensor[@type='rgbd_camera']"))==1,'Expected one RGB-D camera')
    check(s.find("joint[@name='world_fixed']/parent").text=='world','Base not fixed')
    print(json.dumps({'integrity':'PASS','files':count,'local_resource_references':refs,'moving_joints':8,'rgbd_cameras':1}))

def physics_checks():
    import mujoco
    import numpy as np
    from scipy.spatial.transform import Rotation as R
    def mat(xyz,rpy):
        t=np.eye(4);t[:3,3]=xyz;t[:3,:3]=R.from_euler('xyz',rpy).as_matrix();return t
    def origin(e):return mat(np.fromstring(e.get('xyz','0 0 0'),sep=' '),np.fromstring(e.get('rpy','0 0 0'),sep=' '))
    m=mujoco.MjModel.from_xml_path(str(ROOT/'mujoco/piper_d435.xml'));scene=mujoco.MjModel.from_xml_path(str(ROOT/'mujoco/scene.xml'))
    check((m.nq,m.nv,m.nu,m.ncam)==(8,8,7,1),'Wrong MJCF dimensions')
    u=E.parse(ROOT/'urdf/piper_d435.urdf').getroot();s=E.parse(ROOT/'gazebo/model.sdf').getroot().find('model');rng=np.random.default_rng(435);error=0.
    for sample in range(12):
        data=mujoco.MjData(m);q={}
        for j in range(m.njnt):
            name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_JOINT,j);lo,hi=m.jnt_range[j];q[name]=float(rng.uniform(lo,hi)) if sample else 0.
        q['joint8']=-q['joint7']
        for name,value in q.items():data.qpos[m.jnt_qposadr[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,name)]]=value
        mujoco.mj_forward(m,data)
        for fmt in ['urdf','sdf']:
            pending=list((u if fmt=='urdf' else s).findall('joint'));actual={'base':np.eye(4),'world':np.eye(4)}
            while pending:
                progress=False
                for j in pending[:]:
                    parent=j.find('parent').get('link') if fmt=='urdf' else j.findtext('parent');child=j.find('child').get('link') if fmt=='urdf' else j.findtext('child')
                    if parent not in actual:continue
                    if fmt=='urdf':t=origin(j.find('origin'))
                    else:
                        pose=np.fromstring(s.find(f"link[@name='{child}']/pose").text,sep=' ');t=mat(pose[:3],pose[3:])
                    motion=np.eye(4)
                    if j.get('type')!='fixed':
                        axis=np.fromstring(j.find('axis').get('xyz') if fmt=='urdf' else j.findtext('axis/xyz'),sep=' ');value=q[j.get('name')]
                        if j.get('type')=='prismatic':motion[:3,3]=axis*value
                        else:motion[:3,:3]=R.from_rotvec(axis*value).as_matrix()
                    actual[child]=actual[parent]@t@motion;pending.remove(j);progress=True
                check(progress,'Unresolved tree')
            for i in range(1,m.nbody):
                name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,i);expected=np.eye(4);expected[:3,3]=data.xpos[i];expected[:3,:3]=data.xmat[i].reshape(3,3)
                err=float(np.max(np.abs(actual[name]-expected)));error=max(error,err);check(err<2e-9,f'{fmt} FK mismatch: {name}')
    for i in range(1,m.nbody):
        name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,i)
        if name=='base':continue
        inertia=u.find(f"link[@name='{name}']/inertial");check(abs(float(inertia.find('mass').get('value'))-m.body_mass[i])<1e-12,'Mass mismatch')
        si=s.find(f"link[@name='{name}']/inertial");check(abs(float(si.findtext('mass'))-m.body_mass[i])<1e-12,'SDF mass mismatch')
        np.testing.assert_allclose(np.fromstring(inertia.find('origin').get('xyz'),sep=' '),m.body_ipos[i],atol=1e-12)
        vals=[float(inertia.find('inertia').get(k)) for k in ['ixx','iyy','izz']];np.testing.assert_allclose(vals,m.body_inertia[i],atol=1e-14)
    data=mujoco.MjData(scene);mujoco.mj_resetDataKeyframe(scene,data,0)
    for _ in range(200):mujoco.mj_step(scene,data)
    check(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all(),'Nonfinite simulation state')
    print(json.dumps({'physics':'PASS','mujoco':mujoco.__version__,'fk_samples':12,'max_fk_matrix_error':error,'nq':m.nq,'nv':m.nv,'actuators':m.nu,'cameras':m.ncam,'smoke_steps':200}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--physics',action='store_true');args=ap.parse_args();static_checks()
    if args.physics:physics_checks()
