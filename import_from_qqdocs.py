"""
腾讯文档单词库导入工具
用法：python import_from_qqdocs.py <腾讯文档URL>
输出：同目录生成 import_output.json 和 import_output.txt

依赖：pip install requests beautifulsoup4
"""

import sys
import re
import json
import os
import argparse
from pathlib import Path

def fetch_qqdocs_content(url: str) -> str:
    """通过腾讯文档开放接口获取文档纯文本内容"""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ 缺少依赖，请先安装：pip install requests beautifulsoup4")
        sys.exit(1)

    # 腾讯文档的 docx 导出接口
    # 方法：使用腾讯文档的分享链接获取 docId
    match = re.search(r'/doc/([A-Za-z0-9]+)', url)
    if not match:
        print("❌ 无法从 URL 中提取文档 ID，请检查链接格式。")
        print("   正确的格式示例：https://docs.qq.com/doc/DZHV3dVdkRnh0R2hR")
        sys.exit(1)

    doc_id = match.group(1)
    print(f"📄 检测到文档 ID：{doc_id}")

    # 尝试多种方式获取内容
    content = None

    # 方式1：通过腾讯文档导出为纯文本
    export_url = f"https://docs.qq.com/dop-api/get/summary?outformat=1&docId={doc_id}"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://docs.qq.com/',
        }
        resp = requests.get(export_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if 'data' in data and 'content' in data['data']:
                content = data['data']['content']
                print("✅ 通过导出接口获取内容成功")
    except Exception as e:
        print(f"   导出接口尝试失败：{e}")

    # 方式2：直接抓取 HTML 页面（作为备选）
    if not content:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # 尝试提取表格内容
                tables = soup.find_all('table')
                if tables:
                    rows = []
                    for table in tables:
                        for row in table.find_all('tr'):
                            cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                            rows.append('\t'.join(cells))
                    content = '\n'.join(rows)
                    print("✅ 通过 HTML 表格提取内容成功")
                else:
                    # 尝试提取 pre 或特定 div
                    for tag in soup.find_all(['pre', 'div'], class_=re.compile('content|doc|body', re.I)):
                        if len(tag.get_text()) > 50:
                            content = tag.get_text(separator='\n', strip=True)
                            print("✅ 通过 HTML div 提取内容成功")
                            break
        except Exception as e:
            print(f"   HTML 抓取尝试失败：{e}")

    if not content:
        print("❌ 无法获取文档内容，请确保：")
        print("   1. 文档已设置为「任何人可查看」或「获得链接的人可查看」")
        print("   2. 网络可以正常访问 docs.qq.com")
        sys.exit(1)

    return content


def parse_content(content: str) -> list[dict]:
    """
    解析内容，提取英文-中文词条
    支持的格式：
      focus on the key points | 专注于关键点
      curiosity | 好奇心 | n.
      appeal | 呼吁；恳求；上诉；吸引力 | n./v.
    自动识别：
      词组（含空格）：pos 留空，默认识别为词组
      单词（无空格）：pos 留空，默认填充为 n.
    """
    lines = content.split('\n')
    entries = []
    skipped = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 跳过标题行、说明行
        skip_patterns = [
            r'^[\d一二三四五六七八九十]+[.、\s]?每日词汇',
            r'^每日词汇',
            r'^腾讯文档',
            r'^链接：',
            r'^http',
            r'^#',
            r'^\*\*',
            r'^说明：',
            r'^【',
            r'^--+$',
            r'^\s*$',
        ]
        if any(re.match(p, line, re.I) for p in skip_patterns):
            skipped += 1
            continue

        en = zh = pos = ''
        # 格式1：英文 | 中文 | 词性（可选）
        if ' | ' in line:
            parts = line.split(' | ')
            en = parts[0].strip()
            zh = parts[1].strip()
            pos = parts[2].strip() if len(parts) > 2 else ''
        # 格式2：英文 — 中文（长破折号）
        elif ' — ' in line:
            parts = line.split(' — ', 1)
            en = parts[0].strip()
            zh = parts[1].strip()
        # 格式3：英文    中文（多个空格分隔）
        elif re.match(r'^[a-zA-Z(].*\s{2,}.*[\u4e00-\u9fff]', line):
            parts = re.split(r'\s{2,}', line, 1)
            en = parts[0].strip()
            zh = parts[1].strip() if len(parts) > 1 else ''
        else:
            skipped += 1
            continue

        # 过滤无效行
        if not en or not zh:
            skipped += 1
            continue
        if len(en) < 2:
            skipped += 1
            continue
        if re.match(r'^[\u4e00-\u9fff]+$', en):
            skipped += 1
            continue

        # 自动识别词性：含空格视为词组；无空格且无词性则默认 n.
        if not pos:
            if ' ' in en or "'" in en or en.startswith('('):
                pos = 'phr.'
            else:
                pos = 'n.'

        entries.append({'en': en, 'zh': zh, 'pos': pos})

    return entries


def interactive_mode():
    """交互模式：引导用户输入"""
    print("\n" + "="*50)
    print("  腾讯文档单词库导入工具")
    print("="*50)
    print()

    # 获取 URL
    url = input("📎 请粘贴腾讯文档链接（直接回车使用示例）：\n   ").strip()
    if not url:
        url = "https://docs.qq.com/doc/DZHV3dVdkRnh0R2hR"
        print(f"   使用默认示例文档\n")

    # 分组名称
    group_name = input("📁 请输入分组名称（如：Unit 1 / 每日词汇21）：\n   ").strip()
    if not group_name:
        # 从 URL 中提取
        doc_id = re.search(r'/doc/([A-Za-z0-9]+)', url)
        group_name = f"导入词库_{doc_id.group(1) if doc_id else 'unknown'}"

    print(f"\n🔄 正在抓取文档内容...")
    content = fetch_qqdocs_content(url)

    print(f"🔍 正在解析词条...")
    entries = parse_content(content)

    if not entries:
        print("❌ 未能解析到任何词条，请检查文档格式。")
        print("\n支持的格式：")
        print("   focus on the key points | 专注于关键点")
        print("   curiosity | 好奇心")
        sys.exit(1)

    print(f"✅ 成功解析 {len(entries)} 条词条（跳过 {len(content.split(chr(10)))} - {len(entries)} = {len(content.split(chr(10))) - len(entries)} 行无效内容）")

    # 预览
    print(f"\n📋 预览前 5 条：")
    for i, e in enumerate(entries[:5], 1):
        pos_hint = f" [{e['pos']}]" if e['pos'] else ''
        print(f"   {i}. {e['en']}{pos_hint} → {e['zh']}")
    if len(entries) > 5:
        print(f"   ... 还有 {len(entries) - 5} 条")

    # 确认
    confirm = input(f"\n是否生成导入文件？（y/n）：").strip().lower()
    if confirm not in ('y', 'yes', ''):
        print("已取消。")
        return

    # 输出
    output_dir = Path(__file__).parent
    json_path = output_dir / "import_output.json"
    txt_path = output_dir / "import_output.txt"
    meta_path = output_dir / "import_meta.json"

    # JSON（完整格式，含分组元信息）
    output_data = {
        'version': '1.0',
        'group': {
            'name': group_name,
            'id': f"import_{int(os.path.getmtime(__file__))}" if os.path.exists(__file__) else f"import_{int(os.times().elapsed*1000)}"
        },
        'words': entries
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # TXT（批量导入格式，支持第三字段词性）
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"# 分组：{group_name}\n")
        for e in entries:
            # 词组不写 pos（网页会自动按空格判断），单词写上词性
            pos_part = f" | {e['pos']}" if e['pos'] != 'phr.' else ''
            f.write(f"{e['en']} | {e['zh']}{pos_part}\n")

    # 元信息
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump({'group_name': group_name, 'count': len(entries), 'source_url': url}, f, ensure_ascii=False)

    print(f"\n🎉 生成成功！")
    print(f"   📄 JSON 格式：{json_path}")
    print(f"   📄 TXT 格式：{txt_path}")
    print(f"\n使用方法：")
    print(f"   1. 打开英语默写网页 → 词库页面 → 批量导入")
    print(f"   2. 选择分组，输入 TXT 内容即可导入")
    print()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 命令行模式
        url = sys.argv[1]
        group_name = sys.argv[2] if len(sys.argv) > 2 else "导入词库"
        content = fetch_qqdocs_content(url)
        entries = parse_content(content)
        if not entries:
            print("❌ 未能解析到词条")
            sys.exit(1)
        print(f"✅ 解析到 {len(entries)} 条词条")
        output = {
            'version': '1.0',
            'group': {'name': group_name, 'id': f"import_{int(os.times().elapsed*1000)}"},
            'words': entries
        }
        output_path = Path(__file__).parent / "import_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存至：{output_path}")
    else:
        interactive_mode()
