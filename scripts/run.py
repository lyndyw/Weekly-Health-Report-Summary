#!/usr/bin/env python3
"""
健康管理周报生成器 - 命令行入口
"""

import sys
import os

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from generate_report import generate_report, TARGETS
import json


def parse_input(text):
    """解析用户输入的健康数据"""
    data = {}
    
    lines = text.strip().split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 解析键值对
        if ':' in line or '：' in line:
            normalized = line.replace('：', ':')
            key, value = normalized.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if key == "客户姓名":
                data["客户姓名"] = value
            elif key == "第几周":
                data["第几周"] = value
            elif key == "空腹血糖":
                data["空腹血糖"] = parse_numbers(value)
            elif key == "餐后血糖":
                data["餐后血糖"] = parse_numbers(value)
            elif key == "血压":
                data["血压"] = parse_blood_pressure(value)
            elif key == "干预前体重":
                data["干预前体重"] = float(value.replace('kg', ''))
            elif key == "干预后体重":
                data["干预后体重"] = float(value.replace('kg', ''))
            elif key == "上周体重":
                data["上周体重"] = float(value.replace('kg', ''))
            elif key == "水肿情况":
                data["水肿情况"] = value
            elif key == "自我感觉":
                data["自我感觉"] = value
            elif key == "尿量":
                data["尿量"] = value
            elif key == "尿泡沫":
                data["尿泡沫"] = value
            elif key == "饮食执行":
                data["饮食执行"] = value
            elif key == "运动情况":
                data["运动情况"] = value
            elif key == "用药情况":
                data["用药情况"] = value
            elif key == "监测习惯":
                data["监测习惯"] = value
            elif key == "饮食日志":
                data["饮食日志"] = value
    
    return data


def parse_numbers(text):
    """解析数字列表"""
    import re
    numbers = re.findall(r'[\d.]+', text)
    return [float(n) for n in numbers]


def parse_blood_pressure(text):
    """解析血压数据"""
    import re
    pairs = re.findall(r'(\d+)/(\d+)|(\d+)\s*/\s*(\d+)|(\d+)\s+(\d+)', text)
    result = []
    for pair in pairs:
        if pair[0] and pair[1]:
            result.append([int(pair[0]), int(pair[1])])
        elif pair[2] and pair[3]:
            result.append([int(pair[2]), int(pair[3])])
        elif pair[4] and pair[5]:
            result.append([int(pair[4]), int(pair[5])])
    
    if not result:
        # 尝试解析为两个独立的数字列表
        numbers = [int(n) for n in re.findall(r'\d+', text)]
        for i in range(0, len(numbers), 2):
            if i + 1 < len(numbers):
                result.append([numbers[i], numbers[i + 1]])
    
    return result


def main():
    """主函数"""
    print("=" * 60)
    print("🩺 健康管理周报生成器")
    print("=" * 60)
    print()
    
    # 交互式输入
    print("请输入健康数据（每行一个字段，输入空行结束）：")
    print("示例格式：")
    print("  客户姓名：张三")
    print("  第几周：3")
    print("  空腹血糖：5.2, 5.8, 5.3, 6.1, 5.5, 5.9, 5.4")
    print("  餐后血糖：8.2, 9.1, 7.8, 10.2, 8.5, 7.9, 8.1")
    print("  血压：128/82, 132/85, 125/80, 135/88, 130/83, 127/81, 129/82")
    print("  干预前体重：65kg")
    print("  干预后体重：64.2kg")
    print()
    
    input_lines = []
    while True:
        try:
            line = input()
            if not line.strip():
                break
            input_lines.append(line)
        except EOFError:
            break
    
    if not input_lines:
        print("❌ 未输入数据，退出")
        sys.exit(1)
    
    # 解析数据
    data = parse_input('\n'.join(input_lines))
    
    if not data.get("客户姓名"):
        print("❌ 缺少必要字段：客户姓名")
        sys.exit(1)
    
    if not data.get("空腹血糖") or not data.get("餐后血糖"):
        print("❌ 缺少必要字段：空腹血糖 或 餐后血糖")
        sys.exit(1)
    
    if not data.get("血压"):
        print("❌ 缺少必要字段：血压")
        sys.exit(1)
    
    if not data.get("干预前体重") or not data.get("干预后体重"):
        print("❌ 缺少必要字段：干预前体重 或 干预后体重")
        sys.exit(1)
    
    # 生成报告
    print()
    print("📊 正在生成报告...")
    print()
    
    report = generate_report(data)
    print(report)
    
    # 保存到文件
    output_file = f"{data['客户姓名']}_第{data['第几周']}周调理总结.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print()
    print("=" * 60)
    print(f"✅ 报告已保存到：{output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
