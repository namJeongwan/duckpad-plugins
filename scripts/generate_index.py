"""Generate the discovery index from validated per-plugin catalog files."""
import argparse
import json
from pathlib import Path
from validate import validate_catalog, validate_index


def generate(root):
    ids = validate_catalog(Path(root) / 'plugins')
    index = {'schemaVersion': 1, 'plugins': [
        {'id': plugin_id, 'path': f'plugins/{plugin_id}.json'}
        for plugin_id in sorted(ids)
    ]}
    validate_index(index, ids)
    return index


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if index.json needs regeneration')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = json.dumps(generate(root), ensure_ascii=False, indent=2) + '\n'
    path = root / 'index.json'
    if args.check:
        if not path.is_file() or path.read_text() != output:
            parser.exit(1, 'index.json is stale; run python3 scripts/generate_index.py\n')
        print('Index is up to date')
    else:
        path.write_text(output)
        print('Generated index.json')
