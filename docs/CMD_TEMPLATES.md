# CMD 常用与批量操作模板

在“运行cmd”中搜索或选择模板，修改中文参数后查看生成的命令，再测试或保存。选择模板不会执行。手动编辑命令后，参数不会覆盖手动内容，点击“应用参数到命令”可重新生成。保存的是命令文本，重新打开仍可直接编辑。

现有 33 个常用模板，新增 16 个批量模板：按类型复制、递归复制指定类型、增量备份、预览备份、修改扩展名、导出文件清单、导出目录清单、导出目录树、递归搜索文本、列出含关键词文件、设置只读、取消只读、查找多天未修改的文件、创建编号目录、计算 SHA256、排序文本。

参数支持通配符，例如 `C:\资料\*.txt`。界面说明标出是否递归、覆盖或仅预览；输出文件的父目录需存在。修改扩展名不会转换文件格式。文本命令沿用 Windows 命令的编码支持，复杂 Unicode 文本建议使用专用文本工具。

命令由现有执行器直接交给 CMD，FOR 使用单百分号 `%F`；复制到 .bat 文件时需改成 `%%F`。批量命令执行可能部分成功，错误时应检查运行日志和文件结果。

## 网络资料来源

2026-10-16 查阅并按 AnClicker 参数界面整理，未复制网上的完整脚本。

- [Microsoft Learn：FOR](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/for) — 遍历文件、编号循环。
- [Microsoft Learn：FORFILES](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/forfiles) — 按日期筛选文件。
- [Microsoft Learn：XCOPY](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/xcopy) — 通配符复制、递归、增量、预览。
- [Microsoft Learn：REN](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/ren) — 通配符改名。
- [Microsoft Learn：ATTRIB](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/attrib) — 递归修改只读属性。
- [Microsoft Learn：FINDSTR](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/findstr) — 批量文本搜索。
- [Microsoft Learn：SORT](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sort) — 文本排序输出。

## 验证

`python tools/check_cmd_batch_templates.py` 在独立临时目录中验证全部新增模板的实际执行及输出，不使用用户文件。
