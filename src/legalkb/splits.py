"""One split resolver for batch and injection; injected siblings inherit base IDs."""
from __future__ import annotations
import json
import re
from pathlib import Path
from .compile import ROOT

DOMAIN_PATHS = {
    'bhxh': ['bhxh_v1/bhxh_90.jsonl'],
    'doanh_nghiep': ['dn_v1/dn_dev.jsonl', 'dn_v1/dn_test.jsonl'],
    'thue': ['thue_v1/thue_dev.jsonl', 'thue_v1/thue_test.jsonl'],
    'lao_dong': ['ld_v1/ld_dev.jsonl', 'ld_v1/ld_test.jsonl'],
    'lien_nganh': ['ln_v1/ln_dev.jsonl', 'ln_v1/ln_test.jsonl'],
}
PREFIX = {'BHXH': 'bhxh', 'DN': 'doanh_nghiep', 'THUE': 'thue', 'LD': 'lao_dong', 'LN': 'lien_nganh'}


def split_of(item_id: str, domain: str | None = None, *, root: Path | None = None,
             fallback: str | None = None) -> str:
    root = root or ROOT / 'data' / 'dataset'
    item_id = item_id.split('/')[0]
    domain = domain or PREFIX.get(item_id.split('-')[0])
    if domain not in DOMAIN_PATHS:
        raise ValueError(f'Unknown domain for {item_id}: {domain}')
    paths = [root / domain / 'split.json', root / Path(DOMAIN_PATHS[domain][0]).parent / 'split.json']
    manifest = next((p for p in paths if p.exists()), None)
    if manifest:
        data = json.loads(manifest.read_text(encoding='utf-8'))
        dev, test = data['dev'], data['test']
        if len(set(dev)) != len(dev) or len(set(test)) != len(test) or set(dev) & set(test):
            raise ValueError(f'Duplicate or overlapping split IDs: {manifest}')
        if item_id in dev:
            return 'dev'
        if item_id in test:
            return 'test'
        raise ValueError(f'{item_id} is missing from {manifest}')
    # BHXH historically uses parity; the other domains have named split files.
    if domain == 'bhxh':
        return 'dev' if int(re.sub(r'\D', '', item_id) or 0) % 2 else 'test'
    if fallback in ('dev', 'test'):
        return fallback
    for rel in DOMAIN_PATHS[domain]:
        path = root / rel
        if path.exists():
            for line in path.read_text(encoding='utf-8').splitlines():
                if line.strip() and json.loads(line)['id'] == item_id:
                    return 'test' if rel.endswith('_test.jsonl') else 'dev'
    raise ValueError(f'Cannot resolve split for {item_id}')
