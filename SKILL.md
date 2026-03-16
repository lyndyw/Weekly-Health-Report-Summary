---
name: health-weekly-report
description: '健康管理周总结报告生成。Use this skill whenever the user asks for a weekly health report, weekly adjustment summary, health-week recap, progress review across glucose/blood pressure/weight/diet/exercise/symptoms, or wants a structured weekly patient report in markdown. Prefer this for weekly summaries; use monthly-report skills for longer reporting cycles.'
disable-model-invocation: false
user-invocable: true
---

# 健康管理周总结报告

根据一周的健康监测与干预执行情况，生成结构化周报，适用于慢病管理、营养随访和患者教育。

## 适用场景
- 用户说“生成周报”“本周总结”“调理周报”“第 X 周健康报告”。
- 数据包含血糖、血压、体重、饮食、运动、用药、症状或依从性。
- 用户需要正式但易读的阶段总结。

## 核心规则
1. 先按“指标变化—行为执行—亮点—下周建议”组织内容。
2. 统计达标次数时，仅依据用户提供的数据；不自行补值。
3. 能做归因时，必须引用输入中的饮食/运动/作息线索；无法判断时写“可能相关因素”。
4. 输出专业 Markdown，不放入代码块。
5. 若用户要求与上周对比，需显式列出“较上周改善 / 持平 / 需关注”。

## 默认输出结构
1. 基本信息（姓名、周次、时间范围）
2. 核心指标变化情况
   - 血糖
   - 血压
   - 体重
3. 症状与体征记录
4. 行为与治疗依从性回顾
5. 本周亮点与进步
6. 下周重点与建议

## 输出风格
- 医学表达准确，但尽量清晰易懂。
- 给出鼓励性反馈，不夸大成果。
- 建议要具体到下一周可执行。

## 边界
- 不替代医生诊断。
- 不直接输出药物处方调整。
- 对严重异常指标需提醒用户联系医生。

## 实施说明
若引用仓库脚本生成周报，应先确认输入 JSON 结构与脚本期望一致；当前仓库脚本中混合了单周与多周总结逻辑，因此正式交付时建议优先按照本技能模板直接生成，再把脚本作为辅助参考。
