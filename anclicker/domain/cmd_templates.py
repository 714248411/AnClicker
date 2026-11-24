"""Common Windows CMD templates; selecting a template never executes it."""
import ntpath

TEMPLATES = [
  [
    "文件",
    "列出文件",
    "dir /b {folder}",
    "列出指定文件夹中的文件和子目录。",
    [
      [
        "folder",
        "文件夹",
        "%USERPROFILE%\\Desktop",
        "folder"
      ]
    ]
  ],
  [
    "文件",
    "递归查找文件",
    "dir /s /b {pattern}",
    "按文件名或通配符递归搜索，例如 D:\\资料\\*.xlsx。",
    [
      [
        "pattern",
        "路径及通配符",
        "%USERPROFILE%\\Desktop\\*.txt",
        "text"
      ]
    ]
  ],
  [
    "文件",
    "查看目录树",
    "tree {folder} /f /a",
    "显示目录结构和文件名。",
    [
      [
        "folder",
        "文件夹",
        "%USERPROFILE%\\Desktop",
        "folder"
      ]
    ]
  ],
  [
    "文件",
    "读取文本文件",
    "type {file}",
    "在运行日志中显示文本文件内容。",
    [
      [
        "file",
        "文本文件",
        "C:\\资料\\说明.txt",
        "file"
      ]
    ]
  ],
  [
    "文件",
    "搜索文本内容",
    "findstr /n /i /l /c:{text} {file}",
    "查找匹配的文本行；没有匹配时命令返回非零退出码。",
    [
      [
        "text",
        "搜索文字",
        "关键词",
        "text"
      ],
      [
        "file",
        "文本文件",
        "C:\\资料\\说明.txt",
        "file"
      ]
    ]
  ],
  [
    "文件",
    "新建文件夹",
    "mkdir {folder}",
    "创建指定目录，缺少的父目录也会建立。",
    [
      [
        "folder",
        "新文件夹",
        "%USERPROFILE%\\Desktop\\新文件夹",
        "folder"
      ]
    ]
  ],
  [
    "文件",
    "复制文件",
    "copy /y {source} {target}",
    "复制文件；目标同名文件会被覆盖。",
    [
      [
        "source",
        "源文件",
        "C:\\资料\\示例.txt",
        "file"
      ],
      [
        "target",
        "目标文件",
        "C:\\备份\\示例.txt",
        "save"
      ]
    ]
  ],
  [
    "文件",
    "复制整个文件夹",
    "xcopy {source} {target} /e /i /y",
    "复制目录及子目录，包括空目录；覆盖目标同名文件。",
    [
      [
        "source",
        "源文件夹",
        "C:\\资料",
        "folder"
      ],
      [
        "target",
        "目标文件夹",
        "C:\\备份",
        "folder"
      ]
    ]
  ],
  [
    "文件",
    "移动文件",
    "move /y {source} {target}",
    "移动文件到目标位置；覆盖目标同名文件。",
    [
      [
        "source",
        "源文件",
        "C:\\资料\\示例.txt",
        "file"
      ],
      [
        "target",
        "目标位置",
        "C:\\备份\\示例.txt",
        "save"
      ]
    ]
  ],
  [
    "文件",
    "重命名文件",
    "ren {source} {name}",
    "在原目录内改名，新名称不包含路径。",
    [
      [
        "source",
        "源文件",
        "C:\\资料\\示例.txt",
        "file"
      ],
      [
        "name",
        "新文件名",
        "新的名称.txt",
        "text"
      ]
    ]
  ],
  [
    "文件",
    "计算 SHA256",
    "certutil -hashfile {file} SHA256",
    "计算文件 SHA256 校验值。",
    [
      [
        "file",
        "文件",
        "C:\\资料\\示例.zip",
        "file"
      ]
    ]
  ],
  [
    "压缩",
    "查看压缩包内容",
    "tar -tf {file}",
    "列出 ZIP/TAR 压缩包内容，需系统提供 tar。",
    [
      [
        "file",
        "压缩文件",
        "C:\\资料\\示例.zip",
        "file"
      ]
    ]
  ],
  [
    "压缩",
    "压缩文件夹为 ZIP",
    "tar -a -cf {target} -C {parent} {name}",
    "将父目录中的指定子文件夹打包；输出位置必须在被压缩目录外。",
    [
      [
        "target",
        "输出 ZIP",
        "C:\\备份\\资料.zip",
        "save"
      ],
      [
        "parent",
        "父目录",
        "C:\\",
        "folder"
      ],
      [
        "name",
        "子文件夹名",
        "资料",
        "text"
      ]
    ]
  ],
  [
    "压缩",
    "解压压缩包",
    "tar -xf {file} -C {folder}",
    "解压至已存在的目录；可能覆盖同名文件。",
    [
      [
        "file",
        "压缩文件",
        "C:\\资料\\示例.zip",
        "file"
      ],
      [
        "folder",
        "目标文件夹",
        "C:\\解压结果",
        "folder"
      ]
    ]
  ],
  [
    "网络",
    "检测连接 ping",
    "ping -n {count} {host}",
    "发送指定次数的网络连通性检查。",
    [
      [
        "host",
        "域名或 IP",
        "127.0.0.1",
        "text"
      ],
      [
        "count",
        "次数",
        "4",
        "number"
      ]
    ]
  ],
  [
    "网络",
    "查看 IP 配置",
    "ipconfig /all",
    "显示网卡、IP、网关及 DNS 配置。",
    []
  ],
  [
    "网络",
    "查询域名 DNS",
    "nslookup {host}",
    "查询域名解析结果。",
    [
      [
        "host",
        "域名",
        "example.com",
        "text"
      ]
    ]
  ],
  [
    "网络",
    "跟踪网络路由",
    "tracert -d -h 10 {host}",
    "最多检查 10 跳路由，不反查主机名。",
    [
      [
        "host",
        "域名或 IP",
        "example.com",
        "text"
      ]
    ]
  ],
  [
    "网络",
    "查看端口及连接",
    "netstat -ano",
    "显示网络连接、监听端口和进程 PID。",
    []
  ],
  [
    "网络",
    "查看 HTTP 响应头",
    "curl.exe -I -L --max-time 30 {url}",
    "查看网页响应头，最多等待 30 秒。",
    [
      [
        "url",
        "网址",
        "https://example.com",
        "text"
      ]
    ]
  ],
  [
    "网络",
    "下载文件",
    "curl.exe -fL --max-time 120 -o {file} {url}",
    "下载至指定文件，覆盖已有同名文件；父目录需存在。",
    [
      [
        "url",
        "下载网址",
        "https://example.com/file.zip",
        "text"
      ],
      [
        "file",
        "保存文件",
        "%USERPROFILE%\\Desktop\\下载.zip",
        "save"
      ]
    ]
  ],
  [
    "系统",
    "查看系统信息",
    "systeminfo",
    "显示 Windows 系统与硬件信息。",
    []
  ],
  [
    "系统",
    "查看计算机名称",
    "hostname",
    "显示当前计算机名称。",
    []
  ],
  [
    "系统",
    "查看当前用户",
    "whoami",
    "显示当前运行账户。",
    []
  ],
  [
    "系统",
    "查看 Windows 版本",
    "ver",
    "显示 Windows 版本号。",
    []
  ],
  [
    "系统",
    "查看进程列表",
    "tasklist",
    "显示正在运行的进程。",
    []
  ],
  [
    "系统",
    "查询服务状态",
    "sc query {service}",
    "读取服务状态，不修改服务。",
    [
      [
        "service",
        "服务名",
        "Spooler",
        "text"
      ]
    ]
  ],
  [
    "系统",
    "查找程序路径",
    "where {program}",
    "查找 PATH 中的程序；未找到时返回非零退出码。",
    [
      [
        "program",
        "程序名称",
        "cmd.exe",
        "text"
      ]
    ]
  ],
  [
    "启动",
    "打开文件夹",
    "explorer.exe {folder}",
    "使用资源管理器打开目录。",
    [
      [
        "folder",
        "文件夹",
        "%USERPROFILE%\\Desktop",
        "folder"
      ]
    ]
  ],
  [
    "启动",
    "启动程序",
    "start \"\" {program}",
    "启动指定程序。",
    [
      [
        "program",
        "程序路径或名称",
        "notepad.exe",
        "file"
      ]
    ]
  ],
  [
    "开发",
    "运行 Python 脚本",
    "py -3 {file}",
    "使用已安装的 Python 3 运行脚本，需 Python 启动器 py。",
    [
      [
        "file",
        "Python 文件",
        "C:\\脚本\\main.py",
        "file"
      ]
    ]
  ],
  [
    "开发",
    "查看 Python 包",
    "py -3 -m pip list",
    "查看 Python 3 环境中的已安装包。",
    []
  ],
  [
    "开发",
    "查看 Git 修改",
    "git -C {folder} status --short",
    "查看仓库当前修改，需已安装 Git。",
    [
      [
        "folder",
        "Git 仓库",
        "C:\\项目",
        "folder"
      ]
    ]
  ]
]


# Adapted from Microsoft Learn; sources and behavior: docs/CMD_TEMPLATES.md
TEMPLATES.extend([
  [
    "批量文件",
    "按类型批量复制",
    "xcopy {pattern} {target} /i /y",
    "仅复制当前目录匹配的文件；覆盖同名目标文件。",
    [
      [
        "pattern",
        "路径及通配符",
        "C:\\资料\\*.txt",
        "text"
      ],
      [
        "target",
        "目标文件夹",
        "C:\\备份",
        "folder"
      ]
    ]
  ],
  [
    "批量文件",
    "递归批量复制指定类型",
    "xcopy {pattern} {target} /s /i /y",
    "包含子目录并保留目录结构；覆盖同名文件；目标应在源目录之外。",
    [
      [
        "pattern",
        "路径及通配符",
        "C:\\资料\\*.txt",
        "text"
      ],
      [
        "target",
        "目标文件夹",
        "C:\\备份",
        "folder"
      ]
    ]
  ],
  [
    "批量备份",
    "增量备份文件夹",
    "xcopy {folder} {target} /d /e /i /y",
    "复制新增或源修改日期更新的文件，包括空目录；覆盖旧版本，不删除目标额外文件。",
    [
      [
        "folder",
        "文件夹",
        "C:\\资料",
        "folder"
      ],
      [
        "target",
        "目标文件夹",
        "C:\\备份",
        "folder"
      ]
    ]
  ],
  [
    "批量备份",
    "预览增量备份清单",
    "xcopy {folder} {target} /d /e /i /y /l",
    "仅列出计划复制的文件，不复制或覆盖文件。",
    [
      [
        "folder",
        "文件夹",
        "C:\\资料",
        "folder"
      ],
      [
        "target",
        "目标文件夹",
        "C:\\备份",
        "folder"
      ]
    ]
  ],
  [
    "批量文件",
    "批量修改扩展名",
    "ren {pattern} {extension}",
    "仅当前目录；例如 *.txt 改为 *.log。只改名称，不转换文件格式；重名会失败。",
    [
      [
        "pattern",
        "路径及通配符",
        "C:\\资料\\*.txt",
        "text"
      ],
      [
        "extension",
        "新扩展名匹配式",
        "*.log",
        "extension"
      ]
    ]
  ],
  [
    "批量清单",
    "导出递归文件清单",
    "dir /s /b /a-d {pattern} > {output}",
    "按通配符导出完整文件路径；覆盖输出文件，父目录需存在，输出应放在扫描目录外。",
    [
      [
        "pattern",
        "路径及通配符",
        "C:\\资料\\*.txt",
        "text"
      ],
      [
        "output",
        "输出文件",
        "C:\\备份\\清单.txt",
        "save"
      ]
    ]
  ],
  [
    "批量清单",
    "导出目录清单",
    "dir /s /b /ad {folder} > {output}",
    "导出所有子目录路径；覆盖输出文件，父目录需存在。",
    [
      [
        "folder",
        "文件夹",
        "C:\\资料",
        "folder"
      ],
      [
        "output",
        "输出文件",
        "C:\\备份\\清单.txt",
        "save"
      ]
    ]
  ],
  [
    "批量清单",
    "导出目录树",
    "tree {folder} /f /a > {output}",
    "导出带文件名的目录树；覆盖输出文件，输出应放在扫描目录外。",
    [
      [
        "folder",
        "文件夹",
        "C:\\资料",
        "folder"
      ],
      [
        "output",
        "输出文件",
        "C:\\备份\\清单.txt",
        "save"
      ]
    ]
  ],
  [
    "批量文本",
    "递归搜索文本行",
    "findstr /s /n /i /l /c:{text} {pattern}",
    "在匹配文件及子目录中查找文字并显示行号；无匹配返回非零状态；适合普通文本。",
    [
      [
        "text",
        "搜索文字",
        "error",
        "text"
      ],
      [
        "pattern",
        "路径及通配符",
        "C:\\资料\\*.txt",
        "text"
      ]
    ]
  ],
  [
    "批量文本",
    "列出包含关键词的文件",
    "findstr /s /m /i /l /c:{text} {pattern}",
    "只列出含关键词的文件路径；无匹配返回非零状态；适合普通文本。",
    [
      [
        "text",
        "搜索文字",
        "error",
        "text"
      ],
      [
        "pattern",
        "路径及通配符",
        "C:\\资料\\*.txt",
        "text"
      ]
    ]
  ],
  [
    "批量属性",
    "递归设置文件只读",
    "attrib +r {pattern} /s",
    "设置匹配文件的只读属性，包含子目录；不修改目录属性。",
    [
      [
        "pattern",
        "路径及通配符",
        "C:\\资料\\*.txt",
        "text"
      ]
    ]
  ],
  [
    "批量属性",
    "递归取消文件只读",
    "attrib -r {pattern} /s",
    "取消匹配文件的只读属性，包含子目录；隐藏或系统文件可能无法修改。",
    [
      [
        "pattern",
        "路径及通配符",
        "C:\\资料\\*.txt",
        "text"
      ]
    ]
  ],
  [
    "批量清单",
    "查找多天未修改的文件",
    "forfiles /p {folder} /s /m {mask} /d -{days} /c \"cmd /d /c if @isdir==FALSE echo @path\"",
    "列出至少指定天数未修改的文件，不删除；无匹配返回非零状态。",
    [
      [
        "folder",
        "文件夹",
        "C:\\资料",
        "folder"
      ],
      [
        "mask",
        "文件匹配式",
        "*.log",
        "text"
      ],
      [
        "days",
        "天数",
        "30",
        "days"
      ]
    ]
  ],
  [
    "批量文件",
    "批量创建编号目录",
    "for %D in ({folder}) do for /l %N in (1,1,{count}) do @if not exist \"%~D\\%N\" mkdir \"%~D\\%N\"",
    "在指定父目录下创建 1 到指定数量的文件夹；已有目录会跳过。",
    [
      [
        "folder",
        "文件夹",
        "C:\\资料",
        "folder"
      ],
      [
        "count",
        "目录数量（1–100）",
        "10",
        "number"
      ]
    ]
  ],
  [
    "批量校验",
    "批量计算 SHA256",
    "for %F in ({pattern}) do @certutil -hashfile \"%~fF\" SHA256",
    "计算当前目录匹配文件的 SHA256，在运行日志中查看结果；不递归。",
    [
      [
        "pattern",
        "路径及通配符",
        "C:\\资料\\*.txt",
        "text"
      ]
    ]
  ],
  [
    "批量文本",
    "排序文本清单",
    "sort {file} /o {output}",
    "将每行文本排序并写入另一个文件；覆盖输出文件，请勿选择原文件作为输出。",
    [
      [
        "file",
        "输入文本",
        "C:\\资料\\清单.txt",
        "file"
      ],
      [
        "output",
        "输出文件",
        "C:\\备份\\清单.txt",
        "save"
      ]
    ]
  ]
])

def render_template(template, values):
    arguments = {}
    for key, label, default, kind in template[4]:
        value = str(values.get(key, default)).strip()
        if not value:
            raise ValueError('请填写' + label)
        if any(char in value for char in ('"', '\r', '\n', '\0')):
            raise ValueError(label + '不能包含双引号或换行')
        if kind == 'extension':
            if not value.startswith('*.') or len(value) < 3 or any(c in value[2:] for c in '*?\\/:<>| '):
                raise ValueError(label + '应为 *.扩展名，例如 *.log')
            arguments[key] = '"' + value + '"'
        elif kind == 'days':
            if not value.isdecimal() or not 0 <= int(value) <= 32768:
                raise ValueError(label + '应为 0 到 32768 的整数')
            arguments[key] = str(int(value))
        elif kind == 'number':
            if not value.isdecimal() or not 1 <= int(value) <= 100:
                raise ValueError(label + '应为 1 到 100 的整数')
            arguments[key] = str(int(value))
        else:
            if kind in ('folder', 'file', 'save'):
                value = ntpath.normpath(value)
                if value.endswith('\\'):
                    value += '.'
            arguments[key] = '"' + value + '"'
    return template[2].format(**arguments)
