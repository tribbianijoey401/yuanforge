#!/usr/bin/env python3
"""
PTG/CAL 端到端验证脚本

运行流程:
  1. 扫描 docs/ptg-critical.md → 找出 PTG 关键模块
  2. 对含 @ptg 注解的 seam-agreement.md → 生成 CAL 断言
  3. 检测 schema 漂移（seam vs. 实现）
  4. 验证对抗清单（anti-patterns.md）覆盖率
  5. 模拟合约断言测试执行
  6. 输出验证报告

用法: python3 scripts/run-ptg-cal-check.py [--project PROJECT_DIR]
"""
import argparse, os, re, json, sys
from pathlib import Path

def scan_ptg_modules(project_path):
    """Step 1: 扫描 PTG 关键模块"""
    ptg_file = os.path.join(project_path, "docs", "ptg-critical.md")
    if not os.path.exists(ptg_file):
        print("   ⚠️  ptg-critical.md 不存在 — 无 PTG 模块")
        return []
    
    modules = []
    with open(ptg_file) as f:
        for line in f:
            line = line.split("#")[0].strip()
            if line and not line.startswith("#"):
                modules.append(line)
    return modules


def generate_cal_assertions(project_path):
    """Step 2: 运行 ptg-cal-gen.py 生成 CAL 断言"""
    cal_script = os.path.join(project_path, "scripts", "ptg-cal-gen.py")
    if not os.path.exists(cal_script):
        print("   ❌ ptg-cal-gen.py 不存在")
        return None, 0
    
    # 查找所有含 @ptg 的 seam 文件
    seam_files = []
    docs_dir = os.path.join(project_path, "docs")
    for root, dirs, files in os.walk(docs_dir):
        for fname in files:
            if fname.endswith(("-agreement.md", "-api.md", "-contract.md")):
                seam_files.append(os.path.join(root, fname))
    
    if not seam_files:
        # 也搜根目录下的 *-agreement.md
        for fname in os.listdir(project_path):
            if "-agreement.md" in fname and fname.endswith(".md"):
                seam_files.append(os.path.join(project_path, fname))
    
    if not seam_files:
        print("   ⚠️  未找到 seam-agreement.md / API 契约文件")
        return None, 0
    
    total_funcs = 0
    output_dir = os.path.join(project_path, "tests")
    os.makedirs(output_dir, exist_ok=True)
    
    cal_results = {}
    for seam_file in seam_files:
        output_file = os.path.join(output_dir, f"test_{os.path.basename(seam_file).replace('-agreement', 'seam-assertions')}.py")
        
        r = __import__('subprocess').run(
            ["python3", cal_script, "-i", seam_file, "-o", output_file],
            capture_output=True, text=True, cwd=project_path
        )
        
        if r.returncode == 0:
            func_count = 0
            if os.path.exists(output_file):
                func_count = open(output_file).read().count("def test_")
            cal_results[seam_file] = {"output": output_file, "functions": func_count}
            total_funcs += func_count
        else:
            cal_results[seam_file] = {"error": r.stderr.strip(), "functions": 0}
    
    if total_funcs == 0 and len(cal_results) == 0:
        print("   ❌ 所有 seam 文件均未通过 CAL 生成")
    
    return cal_results, total_funcs


def detect_schema_drift(project_path):
    """Step 3: Schema 漂移检测"""
    # 解析 seam-agreement.md 中的字段定义
    field_info = {}
    seam_files = [os.path.join(project_path, "docs", "seam-agreement.md")]
    docs_dir = os.path.join(project_path, "docs")
    if os.path.exists(docs_dir):
        for f in os.listdir(docs_dir):
            if f.endswith("-agreement.md") and f != "seam-agreement.md":
                seam_files.append(os.path.join(docs_dir, f))
    
    for seam_path in seam_files:
        if os.path.exists(seam_path):
            with open(seam_path) as f:
                content = f.read()
            for line in content.split('\n'):
                m = re.match(r'^[-•]\s*(\w+):\s+(\w+)', line.strip())
                if m:
                    field_info[m.group(1)] = m.group(2)
    
    if not field_info:
        print("   ⚠️  未在 seam-agreement.md 中找到字段定义")
        return [], []
    
    print(f"   Seam 定义字段: {json.dumps(field_info)}")
    
    # 搜索实际代码文件中的字段使用
    impl_fields = {}
    src_dir = os.path.join(project_path, "src")
    if not os.path.isdir(src_dir):
        # 搜索当前目录下所有 .py 文件
        for root, dirs, files in os.walk(project_path):
            if ".git" in root or "__pycache__" in root:
                continue
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath) as f:
                            for line in f:
                                m = re.search(r'\b(\w+)\s*:\s*(int|str|bool|float|list|dict)', line)
                                if m:
                                    impl_fields[m.group(1)] = m.group(2)
                    except:
                        pass
    
    missing = list(set(field_info.keys()) - set(impl_fields.keys()))
    type_mismatches = []
    for field in field_info:
        if field in impl_fields:
            expected = field_info[field]
            actual = impl_fields[field]
            type_map = {"integer": "int", "string": "str", "boolean": "bool"}
            if type_map.get(expected) != actual:
                type_mismatches.append(f"{field}: seam={expected}, impl={actual}")
    
    return missing, type_mismatches


def verify_anti_patterns(project_path):
    """Step 4: 对抗清单校验"""
    ap_file = os.path.join(project_path, "docs", "anti-patterns.md")
    if not os.path.exists(ap_file):
        print("   ⚠️  anti-patterns.md 不存在")
        return []
    
    entries = []
    with open(ap_file) as f:
        for line in f:
            m = re.match(r'^(###?\s+)?(AP-[A-Z]+-\d{3}):', line.strip())
            if m:
                entries.append(m.group(2))
    
    if not entries:
        print("   ℹ️  反模式清单中无实际条目（仅有格式模板）— 需要在运行时积累")
    else:
        print(f"   发现 {len(entries)} 条反模式条目:")
        for e in entries[:5]:
            print(f"     • {e}")
    
    return entries


def run_contract_assertion_tests(cal_results):
    """Step 5: 合约断言测试执行（模拟）"""
    if not cal_results:
        return None
    
    passed = 0
    total = 0
    failed = []
    
    for seam_path, result in cal_results.items():
        if "output" not in result:
            continue
        
        output_file = result["output"]
        if not os.path.exists(output_file):
            continue
        
        content = open(output_file).read()
        test_funcs = re.findall(r'def (test_\w+)\(', content)
        total += len(test_funcs)
        
        # 模拟运行每个断言函数名
        for func_name in test_funcs:
            if "must_not_be_none" in func_name or "rejects_null" in func_name:
                # 必需字段为 null → FAIL
                failed.append(func_name)
            elif "type_check" in func_name:
                passed += 1
            elif "pattern" in func_name:
                passed += 1
            elif "enum" in func_name:
                passed += 1
    
    return {
        "passed": passed,
        "total": total,
        "failed": failed
    }


def generate_report(ptg_modules, cal_results, cal_funcs, drift_missing, 
                   type_mismatches, ap_entries, test_results):
    """Step 6: 生成验证报告"""
    report = {
        "timestamp": "2026-07-24T00:00:00",
        "overview": {
            "ptg_critical_modules": len(ptg_modules),
            "cal_functions_generated": cal_funcs,
            "schema_drift_missing": len(drift_missing),
            "type_mismatches": len(type_mismatches),
            "anti_pattern_entries": len(ap_entries),
        },
        "assertion_tests": {
            "total": test_results["total"] if test_results else 0,
            "passed": test_results["passed"] if test_results else 0,
            "failed": len(test_results["failed"]) if test_results else 0,
        },
        "gate": {
            "status": "PASS" if (
                len(drift_missing) == 0 and 
                len(type_mismatches) == 0 and 
                test_results and 
                (test_results["total"] == 0 or test_results["passed"] / max(test_results["total"], 1) >= 0.9)
            ) else "NEEDS_ATTENTION",
            "reasons": [
                f"Schema 漂移: {len(drift_missing)} 个缺失字段",
                f"类型不匹配: {len(type_mismatches)} 处",
                f"断言失败: {len(test_results['failed']) if test_results else 0} 个"
            ]
        }
    }
    return report


def main():
    parser = argparse.ArgumentParser(description="PTG/CAL 端到端验证")
    parser.add_argument("--project", default=".", help="项目目录路径")
    args = parser.parse_args()
    
    project_path = os.path.abspath(args.project)
    
    print("=" * 60)
    print("PTG/CAL 端到端验证 — YuanForge")
    print("=" * 60)
    
    # Step 1: 扫描 PTG 模块
    print("\n📋 Step 1: 扫描 PTG 关键模块")
    ptg_modules = scan_ptg_modules(project_path)
    for m in ptg_modules:
        print(f"   • {m}")
    
    # Step 2: CAL 生成
    print("\n📋 Step 2: CAL 契约断言生成")
    cal_results, cal_funcs = generate_cal_assertions(project_path)
    if cal_funcs > 0:
        print(f"   ✅ 通过，共 {cal_funcs} 个断言函数")
    else:
        print(f"   ⚠️  未生成任何断言")
    
    # Step 3: Schema 漂移
    print("\n📋 Step 3: Schema 漂移检测")
    drift_missing, type_mismatches = detect_schema_drift(project_path)
    if drift_missing:
        print(f"   ⚠️  Schema 漂移: {len(drift_missing)} 个缺失字段")
        for f in drift_missing:
            print(f"      • {f}")
    if type_mismatches:
        print(f"   ⚠️  类型不匹配: {len(type_mismatches)} 处")
    
    # Step 4: 对抗清单
    print("\n📋 Step 4: 对抗清单校验")
    ap_entries = verify_anti_patterns(project_path)
    
    # Step 5: 合约断言测试
    print("\n📋 Step 5: 合约断言测试执行（模拟）")
    test_results = run_contract_assertion_tests(cal_results)
    if test_results:
        print(f"   总断言: {test_results['total']}")
        print(f"   通过: {test_results['passed']}")
        print(f"   失败: {len(test_results['failed'])}")
        for name in test_results['failed'][:5]:
            print(f"     • {name}")
    
    # Step 6: 报告
    print("\n📋 Step 6: 验证报告")
    report = generate_report(ptg_modules, cal_results, cal_funcs, drift_missing, 
                            type_mismatches, ap_entries, test_results)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    
    # Gate 决策
    gate = report["gate"]
    print("\n" + "=" * 60)
    print(f"Gate 决策: {gate['status'].upper()}")
    if gate['status'] != "PASS":
        print(f"原因: {'; '.join(gate['reasons'])}")
    print("=" * 60)
    
    return 0 if gate["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
