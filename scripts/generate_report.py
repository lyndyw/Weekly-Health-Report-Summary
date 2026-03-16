#!/usr/bin/env python3
"""
健康管理周报生成器
- 支持单周周报（默认）
- 支持 9 周整合报告（需显式指定报告类型）
- 支持从文件或 stdin 读取 JSON
"""

import argparse
import json
import sys
from datetime import datetime

# 干预目标配置
TARGETS = {
    "血糖": {
        "空腹": {"min": 3.9, "max": 7.0, "unit": "mmol/L"},
        "餐后 2 小时": {"max": 10.0, "unit": "mmol/L"}
    },
    "血压": {
        "收缩压": {"max": 130, "unit": "mmHg"},
        "舒张压": {"max": 80, "unit": "mmHg"}
    },
    "体重": {
        "每周目标下降": {"min": 0.5, "max": 1.0, "unit": "kg"}
    }
}


def analyze_blood_sugar(fasting_data, postprandial_data, diet_log):
    """分析血糖数据"""
    fasting_target = TARGETS["血糖"]["空腹"]
    postprandial_target = TARGETS["血糖"]["餐后 2 小时"]

    fasting_data = [v for v in fasting_data if v is not None]
    fasting_normal = [v for v in fasting_data if fasting_target["min"] <= v <= fasting_target["max"]]
    fasting_high = [v for v in fasting_data if v > fasting_target["max"]]
    fasting_low = [v for v in fasting_data if v < fasting_target["min"]]

    postprandial_data = [v for v in postprandial_data if v is not None]
    postprandial_normal = [v for v in postprandial_data if v <= postprandial_target["max"]]
    postprandial_high = [v for v in postprandial_data if v > postprandial_target["max"]]

    return {
        "fasting": {
            "normal_count": len(fasting_normal),
            "high_count": len(fasting_high),
            "low_count": len(fasting_low),
            "values": fasting_data,
            "avg": sum(fasting_data) / len(fasting_data) if fasting_data else 0
        },
        "postprandial": {
            "normal_count": len(postprandial_normal),
            "high_count": len(postprandial_high),
            "values": postprandial_data,
            "avg": sum(postprandial_data) / len(postprandial_data) if postprandial_data else 0,
            "max_value": max(postprandial_data) if postprandial_data else 0
        }
    }


def analyze_blood_pressure(bp_data):
    """分析血压数据"""
    systolic_target = TARGETS["血压"]["收缩压"]["max"]
    diastolic_target = TARGETS["血压"]["舒张压"]["max"]

    systolic_normal = [v[0] for v in bp_data if v[0] <= systolic_target]
    systolic_high = [v[0] for v in bp_data if v[0] > systolic_target]

    diastolic_normal = [v[1] for v in bp_data if v[1] <= diastolic_target]
    diastolic_high = [v[1] for v in bp_data if v[1] > diastolic_target]

    avg_systolic = sum(v[0] for v in bp_data) / len(bp_data) if bp_data else 0
    avg_diastolic = sum(v[1] for v in bp_data) / len(bp_data) if bp_data else 0

    return {
        "systolic": {
            "normal_count": len(systolic_normal),
            "high_count": len(systolic_high),
            "avg": avg_systolic,
            "values": [v[0] for v in bp_data]
        },
        "diastolic": {
            "normal_count": len(diastolic_normal),
            "high_count": len(diastolic_high),
            "avg": avg_diastolic,
            "values": [v[1] for v in bp_data]
        }
    }


def analyze_weight(before_weight, after_weight, last_week_weight=None):
    """分析体重数据"""
    weight_change = after_weight - before_weight
    bmi_before = calculate_bmi(before_weight)
    bmi_after = calculate_bmi(after_weight)
    bmi_change = bmi_after - bmi_before

    result = {
        "before": before_weight,
        "after": after_weight,
        "change": weight_change,
        "bmi_before": bmi_before,
        "bmi_after": bmi_after,
        "bmi_change": bmi_change
    }

    if last_week_weight is not None:
        result["cumulative_change"] = after_weight - last_week_weight

    return result


def generate_final_report(data):
    """生成 9 周调理总结 + 体检整合报告"""
    customer_name = data.get("客户姓名", "客户")
    report_period = data.get("报告周期", "")
    exam_date = data.get("体检日期", "")
    exam_hospital = data.get("体检医院", "")

    report = f"""# {customer_name} 9 周调理总结 + 体检整合报告

**报告周期：** {report_period}  
**体检日期：** {exam_date}  
**体检医院：** {exam_hospital}

---

## 📋 一、主要诊断

"""

    diagnoses = data.get("主要诊断", [])
    for i, diag in enumerate(diagnoses, 1):
        report += f"{i}. **{diag}**\n"

    report += f"""
---

## 🏥 二、体检关键指标（{exam_date}）

| 项目 | 结果 | 参考值 | 状态 |
|------|------|--------|------|
"""

    exam_indicators = data.get("体检关键指标", {})
    for key, value in exam_indicators.items():
        status = "⚠️ 异常" if any(token in str(value) for token in ["异常", "偏高", "偏低", "升高"]) else "✅ 正常"
        report += f"| **{key}** | {value} | - | {status} |\n"

    report += f"""
---

## 📊 三、9 周调理成果对比

| 指标 | 干预前 | 第 9 周 | 变化 | 状态 |
|------|--------|--------|------|------|
"""

    before_data = data.get("干预前数据", {})
    week9_data = data.get("第 9 周数据", {})
    changes = data.get("9 周累计变化", {})

    for key in ["体重", "空腹血糖", "血压", "水肿", "精神状态"]:
        before = before_data.get(key, "N/A")
        week9 = week9_data.get(key, "N/A")
        change = changes.get(f"{key}变化", changes.get(key, "N/A"))
        if isinstance(change, float):
            change = f"{change:+.1f}" if key == "体重" else change
        status = "✅ 改善" if key in ["体重", "血压", "水肿"] else "✅ 稳定"
        report += f"| **{key}** | {before} | {week9} | {change} | {status} |\n"

    report += f"""
### 9 周体重变化曲线

| 周次 | 体重 (kg) | 周变化 | 累计变化 |
|------|-----------|--------|----------|
"""

    weekly_data = data.get("周报告汇总", [])
    initial_weight = before_data.get("体重", 62.3)
    for index, week in enumerate(weekly_data):
        weight = week.get("体重", 0)
        prev_weight = initial_weight if index == 0 else weekly_data[index - 1].get("体重", initial_weight)
        weekly_change = weight - prev_weight
        cumulative = weight - initial_weight
        report += f"| 第{week.get('周次', index + 1)}周 | {weight} | {weekly_change:+.2f} | {cumulative:+.2f} |\n"

    report += f"""
---

## 🎯 四、9 周调理亮点与进步

"""

    for i, highlight in enumerate(data.get("亮点与进步", []), 1):
        report += f"{i}. ✅ **{highlight}**\n"

    report += f"""
---

## ⚠️ 五、需持续关注的问题

"""

    for i, concern in enumerate(data.get("需持续关注", []), 1):
        report += f"{i}. ⚠️ {concern}\n"

    report += f"""
---

## 💡 六、后续健康建议

"""

    for i, suggestion in enumerate(data.get("后续建议", []), 1):
        report += f"{i}. **{suggestion}**\n"

    report += f"""
---

## 📈 七、每周数据汇总

| 周次 | 体重 (kg) | 空腹达标 | 餐后达标 | 关键事件 |
|------|-----------|----------|----------|----------|
"""

    for week in weekly_data:
        report += f"| 第{week.get('周次', '?')}周 | {week.get('体重', 'N/A')} | {week.get('空腹达标', 'N/A')} | {week.get('餐后达标', 'N/A')} | {week.get('事件', 'N/A')} |\n"

    report += f"""
---

## 💊 八、当前用药方案

**胰岛素：** {data.get("用药方案", {}).get("胰岛素", "待确认")}

**慢性病用药：** {data.get("用药方案", {}).get("慢性病用药", "待确认")}

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*  
*温馨提示：本报告仅供参考，具体治疗方案请遵医嘱*  
*下次复查建议：请结合临床复诊安排*
"""

    return report


def calculate_bmi(weight_kg, height_m=1.65):
    """计算 BMI（默认身高 1.65m，可根据实际情况调整）"""
    return weight_kg / (height_m ** 2) if height_m else 0


def normalize_weekly_data(data):
    """把常见同义字段归一化到脚本期望结构。"""
    normalized = dict(data)

    field_aliases = {
        "客户姓名": ["姓名", "患者姓名", "name"],
        "第几周": ["周次", "week", "week_num"],
        "空腹血糖": ["fasting_glucose", "fasting", "空腹血糖值"],
        "餐后血糖": ["postprandial_glucose", "postprandial", "餐后2h血糖", "餐后2小时血糖"],
        "血压": ["blood_pressure", "bp"],
        "干预前体重": ["weight_before", "基线体重"],
        "干预后体重": ["weight_after", "本周体重", "当前体重"],
        "上周体重": ["last_week_weight"],
        "饮食日志": ["diet_log"],
        "饮食执行": ["diet_adherence"],
        "运动情况": ["exercise"],
        "用药情况": ["medication"],
        "监测习惯": ["monitoring"],
    }

    for canonical, aliases in field_aliases.items():
        if canonical not in normalized:
            for alias in aliases:
                if alias in normalized:
                    normalized[canonical] = normalized[alias]
                    break

    if isinstance(normalized.get("血压"), dict):
        systolic = normalized["血压"].get("systolic", [])
        diastolic = normalized["血压"].get("diastolic", [])
        normalized["血压"] = list(zip(systolic, diastolic))

    if normalized.get("上周体重") is None and normalized.get("干预前体重") not in (None, 0):
        normalized["上周体重"] = normalized.get("干预前体重")

    return normalized


def validate_weekly_input(data):
    missing = []
    for key in ["客户姓名", "第几周", "空腹血糖", "餐后血糖", "血压", "干预前体重", "干预后体重"]:
        if key not in data:
            missing.append(key)
    return missing


def generate_weekly_report(data):
    """生成单周调理总结"""
    data = normalize_weekly_data(data)
    missing = validate_weekly_input(data)
    if missing:
        raise ValueError(f"缺少必要字段: {', '.join(missing)}")

    customer_name = data.get("客户姓名", "客户")
    week_num = data.get("第几周", "X")

    blood_sugar = analyze_blood_sugar(
        data.get("空腹血糖", []),
        data.get("餐后血糖", []),
        data.get("饮食日志", "")
    )
    blood_pressure = analyze_blood_pressure(data.get("血压", []))
    weight = analyze_weight(
        data.get("干预前体重", 0),
        data.get("干预后体重", 0),
        data.get("上周体重")
    )

    report = f"""# {customer_name}第{week_num}周调理总结

## 1. 核心指标变化情况

### 1.1 血糖变化情况

| 干预目标 | 干预结果 | 原因 |
|----------|----------|------|
| 空腹血糖 {TARGETS['血糖']['空腹']['min']}-{TARGETS['血糖']['空腹']['max']} mmol/L | {blood_sugar['fasting']['normal_count']}次达标，{blood_sugar['fasting']['high_count']}次超标 | 饮食控制良好，用药依从性高 |
| 餐后 2 小时 <{TARGETS['血糖']['餐后 2 小时']['max']} mmol/L | {blood_sugar['postprandial']['normal_count']}次达标，{blood_sugar['postprandial']['high_count']}次超标 | 需结合饮食日志分析 |

**空腹血糖数据：** {', '.join(map(str, blood_sugar['fasting']['values']))}
**餐后血糖数据：** {', '.join(map(str, blood_sugar['postprandial']['values']))}

#### 总结及建议：

您的空腹血糖整体控制{'良好' if blood_sugar['fasting']['high_count'] == 0 else '有待改善'}，{blood_sugar['fasting']['normal_count']}次测量在正常范围。

"""

    if blood_sugar['postprandial']['high_count'] > 0:
        report += f"""但餐后血糖存在波动，最高达 **{blood_sugar['postprandial']['max_value']} mmol/L**。

**建议：**
- **严格控制添加糖摄入**，避免含糖饮料和甜点
- **选择低 GI 主食**如燕麦、糙米、全麦面包
- **注意进食顺序**：先吃蔬菜，再吃蛋白质，最后吃主食
- **餐后适量活动**，如散步 15-20 分钟

"""

    report += f"""### 1.2 血压变化情况

| 干预目标 | 干预结果 | 原因 |
|----------|----------|------|
| 收缩压 ≤{TARGETS['血压']['收缩压']['max']} mmHg | {blood_pressure['systolic']['normal_count']}次达标，{blood_pressure['systolic']['high_count']}次超标 | 需结合日志分析 |
| 舒张压 ≤{TARGETS['血压']['舒张压']['max']} mmHg | {blood_pressure['diastolic']['normal_count']}次达标，{blood_pressure['diastolic']['high_count']}次超标 | 需结合日志分析 |

**血压数据：** {', '.join(f'{s}/{d}' for s, d in zip(blood_pressure['systolic']['values'], blood_pressure['diastolic']['values']))}
**平均值：** {blood_pressure['systolic']['avg']:.1f}/{blood_pressure['diastolic']['avg']:.1f} mmHg

#### 总结及建议：

您的血压控制总体{'稳定' if blood_pressure['systolic']['high_count'] <= 2 else '有波动'}。

**建议：**
- **每日食盐摄入量控制在 5g 以下**，可使用限盐勺
- **下午 4-5 点可饮用玉米须水**辅助利尿降压
- **保持规律作息**，避免情绪波动
- **出锅前放盐**，减少盐用量但保持风味

### 1.3 体重变化情况

| 指标 | 干预前 | 干预后 | 变化幅度 |
|------|--------|--------|----------|
| 体重 | {weight['before']:.2f} kg | {weight['after']:.2f} kg | {weight['change']:+.2f} kg {'↓' if weight['change'] < 0 else '↑'} |
| BMI | {weight['bmi_before']:.1f} | {weight['bmi_after']:.1f} | {weight['bmi_change']:+.1f} {'↓' if weight['bmi_change'] < 0 else '↑'} |

"""

    if 'cumulative_change' in weight:
        report += f"**累计减重：** {weight['cumulative_change']:+.2f} kg\n\n"

    weight_trend = "良好" if -1.0 <= weight['change'] <= -0.5 else "需调整" if weight['change'] > 0 else "较快"
    report += f"""#### 总结及建议：

{'恭喜您！' if weight['change'] < 0 else '需关注'}本周体重{'下降' if weight['change'] < 0 else '上升'}{abs(weight['change']):.2f}kg，趋势{weight_trend}。

"""

    if weight['change'] < 0:
        report += """**健康益处：**
- **减轻心肾负担**，有助于改善血压和血糖
- **提高胰岛素敏感性**，有利于血糖控制
- **降低心血管疾病风险**

**建议：** 继续保持当前饮食节奏，每周减重 0.5-1kg 为宜，避免过快减重导致营养不良。

"""

    report += f"""## 2. 症状与体征记录

| 观察项目 | 本周情况 | 趋势变化 |
|----------|----------|----------|
| 水肿情况 | {data.get('水肿情况', '待记录')} | {data.get('水肿趋势', '待观察')} |
| 自我感觉 | {data.get('自我感觉', '待记录')} | {data.get('感觉趋势', '待观察')} |
| 尿量 | {data.get('尿量', '待记录')} | {data.get('尿量趋势', '待观察')} |
| 尿泡沫 | {data.get('尿泡沫', '待记录')} | {data.get('尿泡沫趋势', '待观察')} |

## 3. 行为与治疗依从性回顾

| 项目 | 执行情况 | 评价 |
|------|----------|------|
| 饮食执行 | {data.get('饮食执行', '待记录')} | ★★★★☆ 良好 |
| 运动情况 | {data.get('运动情况', '待记录')} | ★★★★☆ 良好 |
| 用药依从性 | {data.get('用药情况', '待记录')} | ★★★★★ 优秀 |
| 监测习惯 | {data.get('监测习惯', '待记录')} | ★★★★★ 优秀 |

## 4. 本周亮点与进步

1. **数据监测完整** — 连续 7 天记录健康数据，为分析提供宝贵依据
2. **用药依从性高** — 按时服药，这是慢病管理成功的关键
3. **主动学习健康知识** — 积极了解饮食调理方法
4. **体重管理初见成效** — {'下降' if weight['change'] < 0 else '稳定'}趋势{'良好' if -1.0 <= weight['change'] <= -0.5 else '需调整'}

## 5. 本周知识分享与下周建议

| 细则 | 本周回顾 | 下周计划 |
|------|----------|----------|
| **核心知识点** | 食物如何去钾 | **如何看懂食物成分表**，识别隐形的\"钠\" |
| **监测计划** | 血糖有波动 | 重点监测**早餐后**及**疑似摄入高碳日**的餐后血糖 |
| **体重目标** | {'↓' if weight['change'] < 0 else '→'}{abs(weight['change']):.2f}kg，趋势良好 | 维持平稳下降，目标波动在**-0.5~1kg** |
| **饮食执行重点** | 钠摄入不稳定 | 挑战连续**2 天\"无添加酱料日\"**，仅用天然香料调味 |

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*
*温馨提示：本报告仅供参考，具体治疗方案请遵医嘱*
"""

    return report


def detect_report_type(data, explicit_type=None):
    if explicit_type:
        return explicit_type
    if data.get("报告类型") == "9 周调理总结 + 体检整合报告":
        return "final"
    if any(key in data for key in ["周报告汇总", "体检关键指标", "第 9 周数据"]):
        return "final"
    return "weekly"


def generate_report(data, report_type=None):
    actual_type = detect_report_type(data, report_type)
    if actual_type == "final":
        return generate_final_report(data)
    return generate_weekly_report(data)


def load_input(path=None):
    if path:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return json.load(sys.stdin)


def build_parser():
    parser = argparse.ArgumentParser(
        description='健康管理报告生成器（支持单周周报与 9 周整合报告）'
    )
    parser.add_argument('input', nargs='?', help='输入 JSON 文件路径；省略时从 stdin 读取')
    parser.add_argument('--report-type', choices=['weekly', 'final'], help='显式指定报告类型')
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    data = load_input(args.input)
    report = generate_report(data, args.report_type)
    print(report)


if __name__ == '__main__':
    main()
