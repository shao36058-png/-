# HFSS 宽带带通滤波器 Skill

用于 HFSS 射频带通滤波器的复现、结果检查和尺寸寻优，重点覆盖 LTCC 多层陶瓷、内部导体与 PCB 馈电结构。

提供绝对 −3 dB 与峰值下降 3 dB 两种带宽口径、通带边界、插损、两端回损、纹波、群时延和完整两端口无源性检查，并核对材料、终端端口、实际收敛和扫频来源。

## 分类与检索

**作者分类：电子工程 → 射频与微波工程 / Electronics Engineering → RF and Microwave Engineering。**

| 技能 | 器件细分 |
|---|---|
| HFSS 宽带带通滤波器 | 射频无源器件 → 带通滤波器 → LTCC 滤波器 / RF Bandpass Filters |

职业参考：[Electronics Engineers, Except Computer（SOC 17-2072）](https://skillsmp.com/occupations/electronics-engineers-except-computer)。技能的 `metadata` 记录作者建议分类，`description` 提供中英文器件名称，方便识别与检索。

这些是作者维护的分类信息。SkillsMP 的职业和类别标签由平台维护；其公开文档未承诺依据这些自定义字段自动分类。本节不表示网页上的“分类待定”已解除。

## 安装

```bash
npx skills add shao36058-png/- --skill hfss-wideband-bandpass-filter
```

也可复制 `skills/hfss-wideband-bandpass-filter` 到支持 Agent Skills 的工具的 skill 目录。

在 Codex 中调用 `$hfss-wideband-bandpass-filter`，例如：“检查我已打开的滤波器，核对中心频率、−3 dB 带宽和收敛情况。”

## 脚本与范围

- `filter_metrics.py` 只用 Python 标准库，读取完整复数两端口 CSV，输出曲线指标；退出 0 表示处理完成。
- `export_saved_filter.py` 需要 PyAEDT 和 psutil，只读导出明确指定的已有 HFSS 会话，不运行仿真或保存模型。

数据格式见 skill 的 `references/validation.md`。带宽合格不自动意味着插损、回损或阻带合格，验收容差应由用户确定。参数搜索以实际 HFSS 结果验证，脚本不能代替材料验证、充分采样或实物测试。

公开内容仅为通用流程和脚本，不包含 HFSS 原项目、论文、具体尺寸和本地结果。MIT 许可证。
