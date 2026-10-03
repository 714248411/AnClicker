import time

# 获取当前时间并只保留日期部分
local_time = time.localtime(time.time())
formatted_date = time.strftime("%Y-%m-%d", local_time)
print(f"当前日期: {formatted_date}")
