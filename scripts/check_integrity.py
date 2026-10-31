#!/usr/bin/env python3
"""Check preserved source text, variant index, provenance and local links."""
import hashlib
import json
import re
from pathlib import Path
from read_methods import ROOT, get_method, manifest

def main():
    errors = []
    data = manifest()
    ids = [m['id'] for m in data['methods']]
    if ids != list(range(1, 34)) or data['method_count'] != 33:
        errors.append('方法集合应为 1–33，不能遗漏或重复。')
    index = (ROOT / 'references/method-index.md').read_text(encoding='utf-8')
    sections = re.findall(r'^## (\d+)\. ([^\n]+)\n(.*?)(?=^## |\Z)', index, re.M | re.S)
    if [int(n) for n, _, _ in sections] != ids:
        errors.append('索引编号集合或顺序与来源清单不一致。')
    indexed = {int(n): (title, block) for n, title, block in sections}
    refs = set()
    for item in data['methods']:
        n = item['id']
        try:
            block = get_method(n, data)
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
            continue
        fields = dict(re.findall(r'^- \*\*(.+?)\*\*：(.+)$', block, re.M))
        index_title, index_block = indexed.get(n, ('', ''))
        index_fields = dict(re.findall(r'^- (变体|材料条件)：(.+)$', index_block, re.M))
        for name, key in [('变体', 'variants'), ('素材里要有', 'materials')]:
            index_name = '变体' if key == 'variants' else '材料条件'
            if fields.get(name) != item[key] or index_fields.get(index_name) != item[key]:
                errors.append(f'{n} 的 {name} 与索引／来源不一致。')
        if index_title != item['title']:
            errors.append(f'{n} 的索引标题与来源不一致。')
        expected_link = item['file'].removeprefix('references/')
        if f'[完整条目]({expected_link})' not in index_block or f'`concepts/ending#{n}`' not in index_block:
            errors.append(f'{n} 的索引定位与来源不一致。')
        actual_refs = list(dict.fromkeys(re.findall(r'\[\[([^\]]+)\]\]', block)))
        if actual_refs != item['source_refs']:
            errors.append(f'{n} 的来源边丢失或变化。')
        refs.update(actual_refs)
    if sorted(refs) != data['referenced_source_slugs']:
        errors.append('去重出处集合与清单不一致。')
    guidance = (ROOT / 'references/source-guidance.md').read_text(encoding='utf-8')
    if hashlib.sha256(guidance.encode('utf-8')).hexdigest() != data['source_guidance_sha256']:
        errors.append('原页指导／边界／缺口的来源指纹不一致。')
    checked_links = 0
    for file in ROOT.rglob('*.md'):
        for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)]+)\)', file.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            path = (file.parent / target.split('#', 1)[0]).resolve()
            checked_links += 1
            if not path.is_file():
                errors.append(f'{file.relative_to(ROOT)} 链接不存在：{target}')
    print(json.dumps(dict(methods=len(ids), source_refs=len(refs), local_links=checked_links,
                          errors=errors, error_count=len(errors)), ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == '__main__':
    raise SystemExit(main())
