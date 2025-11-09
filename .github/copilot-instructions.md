## 快速概览 — 目标与边界

这是一个面向 Abaqus/CAE 的单文件仿真控制脚本：`Wasserstrallmodell.py`。
主要用途是：启动/重启 Abaqus 作业（Job），从 ODB 中提取接触压力场 (CPRESS)，筛选节点并为下一步创建基于节点的解析场 (AnalyticalField) 与对流边界条件（FilmCondition）。

关键约束：脚本依赖 Abaqus 的 Python API（`from abaqus import *` 等），必须在 Abaqus 的 Python/CAE 环境中运行（不是系统 Python）。

## 主要文件

- `Wasserstrallmodell.py` — 主脚本，包含作业提交、等待、ODB 读取与 FilmCondition 应用逻辑（首要工作区）。
- `README.md` — 仓库说明（当前很简短，可在需要时扩展）。

## 运行与调试（具体命令示例）

1) 在 Windows 上常用的方式是在 Abaqus 环境下无 GUI 运行：

```
abaqus cae noGUI=Wasserstrallmodell.py
```

或如果你有 abaqus python：

```
abaqus python Wasserstrallmodell.py
```

不要使用系统的 `python` 去直接运行此文件（会因找不到 `abaqus` 模块而报错）。

调试技巧：
- 在关键位置插入 `print()`，例如在作业提交/完成前后打印 `mdb.jobs[...]` 与 `odb.steps.keys()`。
- 使用 Abaqus/CAE 的 GUI 快速加载生成的 `.odb` 以交叉验证脚本提取的场变量。

## 项目约定与常见模式

- 单脚本驱动：几乎所有控制逻辑都在 `Wasserstrallmodell.py` 中（全局常量驱动行为）。常见参数在顶部定义，例如 `MaxNum`, `lastModelName`, `nodesetname`。
- 命名与字符串化：作业/模型名以格式化字符串生成（例如：`Model-Restart-ts{}`、`Restart-ts{}`），修改索引或命名会影响后续打开的 ODB 步名（注意步名索引偏移）。
- 临时文件：脚本会写入和删除 `workpiece_nodes_list.txt`。注意并发/重入时的竞态和临时文件残留。
- 混合语言注释与变量：代码中夹杂德语/中文注释和若干未定义或错误的变量（例如 `mm2K`, `Re(x)` 的使用），在修改或重构时请先核对变量来源。

## 具体可搜索与编辑点（示例）

- 要调整重复运行次数：编辑顶部 `MaxNum`。
- 要切换目标节点集或表面：修改 `nodesetname`、`surfacename` 与 `instancename`。
- 作业名与步骤同步位于脚本中间块，改动时保持 `lastModelName/lastStepName/lastJobName` 的一致性。

代码片段示例（在脚本中查找并谨慎修改）：

```
# 控制重启次数
MaxNum = 3

# 节点集与表面名
instancename = 'WORKPIECE'
nodesetname = 'SET-4'
surfacename = 'Surf-Workpiece'
```

## 常见问题与注意事项（来自可见实现）

- 依赖环境：必须在 Abaqus 的 Python/CAE 运行时，且版本要与本地 Abaqus 安装匹配。
- 未定义/拼写错误：脚本中有未定义的标识符和可能的拼写错误（如 `lastNodeName` vs `lastModelName`、`LastJobName` vs `lastJobName`）。在批量重构前先手动运行并修复这些名字不匹配。
- 异常处理：脚本使用了宽泛的 `try/except: pass`，可能掩盖真实错误。调试时临时移除空的 except 或打印异常信息以便定位问题。
- 并发与文件 I/O：脚本写入临时文本文件并随后删除，若同时运行多个实例请改用基于作业名的临时文件名。

## 对 AI 代理的具体建议（Prompt 模板）

- 当你被指示修改仿真流程，先说明目的：调整哪些物理参数（例如 h、sinktemp）、改变哪些集合/表面，或是改为不同的重启策略。
- 在修改变量名或步骤索引前，搜索文件中所有对该名字的引用（全局替换风险高）。例如：`grep -n "lastModelName" Wasserstrallmodell.py`。
- 若要添加日志或更严格的错误处理，优先在作业提交/等待以及 ODB 打开/关闭处添加异常捕获并记录 `sys.exc_info()` 内容。

## 下一步建议（非强制）

- 把常量抽到顶部的 `CONFIG` 字典，添加注释说明单位与量纲（例如速度单位 mm/s，温度 K），减少魔法数字。
- 增加一个小的“运行说明”到 `README.md`，记录如何在本地 Abaqus 环境中执行脚本及常见依赖（例如 NumPy）。

如果这里有遗漏或需要我把某些发现直接修复（例如未定义变量或拼写冲突），告诉我优先级，我可以继续在代码里做小而安全的改进并运行检查。 
