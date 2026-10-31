#!/usr/bin/env python3
"""Read complete, fingerprint-checked ending methods without network access."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def manifest():
    return json.loads((ROOT / 'references/provenance.json').read_text(encoding='utf-8'))

def get_method(number, data=None):
    data = data or manifest()
    item = next((m for m in data['methods'] if m['id'] == number), None)
    if item is None:
        raise ValueError(f'没有方法 {number}；当前有效编号为 1–33。')
    path = (ROOT / item['file']).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('方法路径超出技能目录。')
    text = path.read_text(encoding='utf-8')
    heading = re.search(rf'^#### {number}\. .+$', text, re.M)
    if heading is None:
        raise ValueError(f'文件缺少方法 {number}。')
    following = re.search(r'^#{1,4} ', text[heading.end():], re.M)
    end = heading.end() + following.start() if following else len(text)
    block = text[heading.start():end].strip()
    if hashlib.sha256(block.encode('utf-8')).hexdigest() != item['section_sha256']:
        raise ValueError(f'方法 {number} 的正文与来源指纹不一致，请核对更新记录。')
    return block

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--method', type=int, nargs='+', help='读取一个或多个完整方法')
    mode.add_argument('--list', action='store_true', help='列出全部名称、变体和材料条件')
    args = parser.parse_args(argv)
    try:
        data = manifest()
        if args.list:
            blocks = [f"{m['id']}. {m['title']}\n变体：{m['variants']}\n材料条件：{m['materials']}" for m in data['methods']]
        else:
            # Validate the entire request before printing any partial result.
            blocks = [get_method(n, data) for n in dict.fromkeys(args.method)]
    except (OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print('\n\n'.join(blocks))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
