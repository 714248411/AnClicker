"""Pure window layout geometry in physical desktop coordinates."""
import math

LAYOUT_MODES=('平铺','网格','对角线','水平层叠','垂直层叠','堆叠')


def _legacy_layout(windows, area, parameters):
    count=len(windows)
    if not 1<=count<=100:raise ValueError('请选择 1 至 100 个窗口')
    mode=parameters.get('排布方式','网格')
    if mode not in LAYOUT_MODES:raise ValueError('不支持的排布方式')
    margin=int(parameters.get('边距',8));gap=int(parameters.get('间距',8))
    if not -20000<=margin<=500 or not -20000<=gap<=500:raise ValueError('边距和间距须在 -20000 至 500 之间')
    x,y,right,bottom=map(int,area);x+=margin;y+=margin;right-=margin;bottom-=margin
    width,height=right-x,bottom-y
    if width<50 or height<50:raise ValueError('屏幕可用区域过小，请减小边距')
    vertical=parameters.get('排布方向','横向优先')=='纵向优先'
    boxes=[]
    if mode in ('网格','平铺'):
        if mode=='网格':rows=int(parameters.get('行数',2));cols=int(parameters.get('列数',3))
        else:
            cols=min(count,max(1,math.ceil(math.sqrt(count*width/max(height,1)))))
            rows=math.ceil(count/cols)
        if not 1<=rows<=100 or not 1<=cols<=100:raise ValueError('行列数须在 1 至 100 之间')
        if rows*cols<count:raise ValueError('网格位置不足，请增加行列数或点击自动计算')
        usable_w=width-gap*(cols-1);usable_h=height-gap*(rows-1)
        if usable_w<cols*30 or usable_h<rows*30:raise ValueError('网格过密，请减少行列数或间距')
        for i in range(count):
            row,col=(i%rows,i//rows) if vertical else (i//cols,i%cols)
            left=x+col*gap+usable_w*col//cols;top=y+row*gap+usable_h*row//rows
            boxes.append((left,top,x+col*gap+usable_w*(col+1)//cols,y+row*gap+usable_h*(row+1)//rows))
    else:
        step=max(24,gap)
        dx=min(step,width//max(2*count,1)) if mode in ('对角线','水平层叠') else 0
        dy=min(step,height//max(2*count,1)) if mode in ('对角线','垂直层叠') else 0
        w=width-dx*(count-1);h=height-dy*(count-1)
        boxes=[(x+i*dx,y+i*dy,x+i*dx+w,y+i*dy+h) for i in range(count)]
    results=[]
    for item,box in zip(windows,boxes):
        left,top,r,b=box;w,h=r-left,b-top
        if parameters.get('窗口大小','自动')=='自定义':
            requested_w=int(parameters.get('宽度',960));requested_h=int(parameters.get('高度',640))
            if requested_w<50 or requested_h<50:raise ValueError('自定义宽高不能小于 50 像素')
            w=min(w,requested_w);h=min(h,requested_h)
        if parameters.get('保持比例',False):
            old=item.get('rect',(0,0,w,h));client=item.get('client_size',(old[2]-old[0],old[3]-old[1]))
            extra_w=max(0,old[2]-old[0]-client[0]);extra_h=max(0,old[3]-old[1]-client[1])
            scale=min(max(1,w-extra_w)/max(1,client[0]),max(1,h-extra_h)/max(1,client[1]))
            w=min(w,max(1,round(client[0]*scale)+extra_w));h=min(h,max(1,round(client[1]*scale)+extra_h))
        results.append((left+(r-left-w)//2,top+(b-top-h)//2,w,h))
    return results


# Only these rows belong to each mode. The UI and validation use the same
# contract so a hidden parameter cannot unexpectedly change a layout.
MODE_ROWS={
    '平铺':('direction','grid','gaps','aspect'),
    '网格':('size','custom_size','direction','grid','gaps','aspect'),
    '对角线':('origin','diagonal_step','size','custom_size','aspect'),
    '水平层叠':('origin','x_step','size','custom_size','aspect'),
    '垂直层叠':('origin','y_step','size','custom_size','aspect'),
    '堆叠':('origin','x_step','y_step'),
}
MODE_HINTS={
    '平铺':'按行列分配屏幕空间；负边距可延伸至屏幕外，负间距可让窗口边框重叠。',
    '网格':'按行列定位，可自定义窗口大小；负边距延伸至屏幕外，负间距让窗口重叠。',
    '对角线':'从首窗 X/Y 开始，每个窗口向 X 和 Y 同时偏移一个斜向间距。自动大小保留各窗口原尺寸。',
    '水平层叠':'首窗位置固定；后续窗口只沿 X 偏移，Y 保持一致。自动大小保留各窗口原尺寸。',
    '垂直层叠':'首窗位置固定；后续窗口只沿 Y 偏移，X 保持一致。自动大小保留各窗口原尺寸。',
    '堆叠':'只设置首窗左上角 X/Y 和后续 X/Y 间距，保留每个窗口原大小。间距为 0 时重合，负数向左／上偏移。',
}


def _integer(parameters,key,default,minimum=-100000,maximum=100000):
    raw=parameters.get(key,default)
    try:value=int(raw)
    except (TypeError,ValueError,OverflowError) as error:raise ValueError(key+'必须是整数') from error
    if isinstance(raw,float) and raw!=value:raise ValueError(key+'必须是整数')
    if not minimum<=value<=maximum:raise ValueError(key+f'须在 {minimum} 至 {maximum} 之间')
    return value


def _original_size(item):
    rect=item.get('normal_rect') if item.get('minimized') else item.get('rect')
    rect=rect or (0,0,960,640)
    return max(1,int(rect[2]-rect[0])),max(1,int(rect[3]-rect[1]))


def _aspect_size(item,width,height):
    old_w,old_h=_original_size(item);client=item.get('client_size',(old_w,old_h))
    cw,ch=max(1,int(client[0])),max(1,int(client[1]))
    extra_w=max(0,old_w-cw);extra_h=max(0,old_h-ch)
    scale=min(max(1,width-extra_w)/cw,max(1,height-extra_h)/ch)
    return min(width,max(1,round(cw*scale)+extra_w)),min(height,max(1,round(ch*scale)+extra_h))


def layout_rectangles(windows,area,parameters):
    # Untouched 1.6.5 workflow files keep their recorded behavior. Opening and
    # saving the new editor writes version 2 and its visible mode-specific data.
    if int(parameters.get('排布版本',1))<2:
        return _legacy_layout(windows,area,parameters)
    count=len(windows);mode=parameters.get('排布方式','网格')
    if not 1<=count<=100:raise ValueError('请选择 1 至 100 个窗口')
    if mode not in MODE_ROWS:raise ValueError('不支持的排布方式')
    if mode in ('平铺','网格'):
        margin=_integer(parameters,'边距',8,-20000,500);gap=_integer(parameters,'间距',8,-20000,500)
        x,y,right,bottom=map(int,area);x+=margin;y+=margin;right-=margin;bottom-=margin
        width,height=right-x,bottom-y
        rows=_integer(parameters,'行数',2,1,100);cols=_integer(parameters,'列数',3,1,100)
        if rows*cols<count:raise ValueError('行列位置不足，请增加行列数或点击自动计算')
        usable_w=width-gap*(cols-1);usable_h=height-gap*(rows-1)
        if usable_w<cols*30 or usable_h<rows*30:raise ValueError('行列过密，请减少行列数、边距或间距')
        vertical=parameters.get('排布方向','横向优先')=='纵向优先'
        boxes=[]
        for index in range(count):
            row,col=(index%rows,index//rows) if vertical else (index//cols,index%cols)
            left=x+col*gap+usable_w*col//cols;top=y+row*gap+usable_h*row//rows
            boxes.append((left,top,x+col*gap+usable_w*(col+1)//cols,y+row*gap+usable_h*(row+1)//rows))
        results=[]
        for item,(left,top,r,b) in zip(windows,boxes):
            w,h=r-left,b-top
            if mode=='网格' and parameters.get('窗口大小','自动')=='自定义':
                w=min(w,_integer(parameters,'宽度',960,50,20000));h=min(h,_integer(parameters,'高度',640,50,20000))
            if parameters.get('保持比例',False):w,h=_aspect_size(item,w,h)
            results.append((left+(r-left-w)//2,top+(b-top-h)//2,w,h))
        return results
    x=_integer(parameters,'起点X',int(area[0]));y=_integer(parameters,'起点Y',int(area[1]))
    if mode=='对角线':dx=dy=_integer(parameters,'对角间距',32,-20000,20000)
    else:
        dx=_integer(parameters,'X间距',32,-20000,20000) if mode in ('水平层叠','堆叠') else 0
        dy=_integer(parameters,'Y间距',32,-20000,20000) if mode in ('垂直层叠','堆叠') else 0
    results=[]
    for index,item in enumerate(windows):
        w,h=_original_size(item)
        if mode!='堆叠' and parameters.get('窗口大小','自动')=='自定义':
            w=_integer(parameters,'宽度',960,50,20000);h=_integer(parameters,'高度',640,50,20000)
            if parameters.get('保持比例',False):w,h=_aspect_size(item,w,h)
        # Absolute desktop coordinates and corner-to-corner offsets are exact;
        # never center, clamp, or add tile margins in a positioned mode.
        results.append((x+index*dx,y+index*dy,w,h))
    return results
