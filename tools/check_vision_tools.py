"""Offline vision integration checks; synthetic images, no real input."""
import os,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import cv2,numpy as np
from anclicker.domain.instructions import ExecutionContext,InstructionDraft
from anclicker.storage.database import DatabaseOperation
from anclicker.instructions.registry import get_instruction_spec
from anclicker.platform.vision_tools.runtime import execute,health_percent,save_image,close_monitors,validate
from anclicker.platform.vision_tools.maps import astar_path
from anclicker.domain.instruction_fields.vision_tools import TYPES
from anclicker.platform.qt_compat.QtWidgets import QApplication
app=QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary);db=DatabaseOperation(str(root/'命令集.db'))
    image=np.zeros((50,100,3),np.uint8)
    cv2.putText(image,'AB',(5,30),cv2.FONT_HERSHEY_SIMPLEX,.8,(0,0,255),2)
    events=[]
    context=ExecutionContext(metadata={'database':db},services={'离线视觉截图':lambda p:(image.copy(),(10,20),None),'离线视觉输入':lambda *args:events.append(args)})
    common={'区域':'10,20,100,50','目标文字':'AB','颜色模式':'红字'}
    assert execute('制作字库',common,context)==2
    point=execute('字库点击',dict(common,偏移='3,4',相似度=.78),context)
    assert events and events[-1][1]==point and point[0]>10 and point[1]>20
    assert (root/'glyphs'/'index.json').is_file()
    print('PASS real glyph capture, persistent templates, matching and offset click')
    image=np.zeros((10,100,3),np.uint8);image[:,:25]=(0,0,255)
    assert health_percent(image,(255,0,0),0)==25
    p={'区域':'0,0,100,10','操作':'启动监控','间隔':.05,'冷却':.1,'连续次数':2}
    execute('多线程血量判断',dict(p,监控名='a'),context)
    execute('多线程血量判断',dict(p,监控名='b',响应='鼠标点击',点击位置='12,13'),context)
    deadline=time.monotonic()+2
    before=len(events)
    while len(events)<before+2 and time.monotonic()<deadline:time.sleep(.02)
    assert len(events)>=before+2
    assert context.variables['血量']==25
    close_monitors(context);count=len(events);time.sleep(.15);assert len(events)==count
    assert not context.metadata['vision_monitors'] if 'vision_monitors' in context.metadata else True
    print('PASS concurrent health monitors, keyboard/mouse routes, stop joins all threads')
    assert astar_path((0,0),(2,2),{(0,0)},bounds=(0,0,2,2)) is None
    assert astar_path((0,0),(2,2),{(1,0),(1,1),(1,2)},bounds=(0,0,2,2)) is None
    assert astar_path((0,0),(1,1),{(1,0),(0,1)},bounds=(0,0,1,1)) is None
    grid=np.full((80,80,3),255,np.uint8);grid[:60,35:45]=0;save_image(root/'map.png',grid)
    points=execute('A星寻路',{'地图路径':'map.png','起始坐标':'5,5','终点坐标':'75,5','网格大小':5,'保存路径':'route.png'},context)
    assert points[0]==(5,5) and points[-1]==(75,5) and max(y for x,y in points)>=60
    assert (root/'route.png').is_file()
    print('PASS bounded A star, blocked endpoints, no corner cutting, no unsafe fallback, preview output')
    rng=np.random.default_rng(42);world=rng.integers(0,255,(140,180,3),dtype=np.uint8)
    frames=[world[20:100,20+i*3:100+i*3].copy() for i in range(4)];index=[0]
    def frame(p):
        out=frames[min(index[0],3)];index[0]+=1;return out,(0,0),None
    context.services={'离线视觉截图':frame}
    path=execute('小地图拼接制作大地图',{'区域':'0,0,80,80','帧数':4,'间隔':.1,'画布大小':256,'保存路径':'map2.png'},context)
    assert Path(path).is_file() and (root/'map2.json').is_file()
    print('PASS translated minimap frames stitched and metadata saved')
    for name in TYPES:
        spec=get_instruction_spec(name);editor=spec.create_editor(context=context)
        assert editor.windowTitle()==name
        if name=='多线程血量判断':
            editor._controls['操作'].setCurrentText('停止监控');editor.get_draft()
        editor.close()
    print('PASS all registered vision editors and stop-monitor parameters')
    import sqlite3,json,contextlib
    from anclicker.storage.data_bundle import export_data,prepare_import,apply_import
    with contextlib.closing(sqlite3.connect(db.db_path)) as conn:
        for ident,name,params in [(1,'字库点击',dict(common,字库目录=str(root/'glyphs'))),(2,'A星寻路',{'地图路径':str(root/'map.png')})]:
            conn.execute('INSERT INTO 命令 (ID,类型标识,参数JSON,重复次数,异常处理,备注,排序) VALUES (?,?,?,1,?,?,?)',(ident,name,json.dumps(params),'自动跳过','',ident))
            conn.execute('INSERT INTO 节点 VALUES (?, ?, ?, 0, 0)',('node-'+str(ident),ident,'instruction'))
        conn.commit()
    with tempfile.TemporaryDirectory() as imported_temp:
        target=Path(imported_temp)/'Data'
        archive=export_data(root,Path(imported_temp)/'vision.zip')
        stage=prepare_import(archive,Path(imported_temp))
        apply_import(stage,target)
        with contextlib.closing(sqlite3.connect(str(target/'命令集.db'))) as conn:
            params=[json.loads(row[0]) for row in conn.execute('SELECT 参数JSON FROM 命令 ORDER BY ID')]
        assert (Path(params[0]['字库目录'])/'index.json').is_file()
        assert Path(params[1]['地图路径']).is_file()
        assert Path(params[0]['字库目录']).is_relative_to(target)
    print('PASS glyph directory and map assets relocate with whole project import')
print('PASS offline vision suite')
