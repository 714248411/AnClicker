"""Normalize persisted old image-wait options without executing expressions."""


def normalize_image_wait(parameters):
    result = dict(parameters)
    mode = result.get('等待类型', '等待出现')
    if mode == '等待到指定图像出现':
        result['等待类型'] = '等待出现'
    elif mode == '等待到指定图像消失':
        result['等待类型'] = '等待消失'
        # Legacy disappearance never used its timeout field.
        result['超时时间'] = 0
    area = result.get('区域')
    if str(area).replace(' ', '') in ('(0,0,0,0)', '[0,0,0,0]'):
        result['区域'] = ''
    return result
