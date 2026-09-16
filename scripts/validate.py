"""Validate catalog metadata without third-party dependencies or network access."""
import base64
import json
import re
from pathlib import Path
from urllib.parse import urlparse, unquote

def semver(value):
    if not (isinstance(value, str) and re.fullmatch('(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)', value)):
        raise ValueError('invalid version')
    return tuple(map(int, value.split('.')))

def validate(entry):
    if not set(entry) == {'schemaVersion', 'id', 'name', 'description', 'repository', 'publisher', 'releases'}:
        raise ValueError('unexpected catalog fields')
    if not entry['schemaVersion'] == 1:
        raise ValueError('invalid catalog value')
    if not re.fullmatch('[a-z0-9]+(?:[.-][a-z0-9-]+)+', entry['id']):
        raise ValueError('invalid catalog value')
    if not (isinstance(entry['name'], str) and entry['name'].strip()):
        raise ValueError('invalid catalog value')
    if not set(entry['description']) >= {'en', 'ko'}:
        raise ValueError('invalid catalog value')
    if not all((isinstance(v, str) and v.strip() for v in entry['description'].values())):
        raise ValueError('invalid catalog value')
    repository = entry['repository']
    if not re.fullmatch('https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('invalid source repository')
    publisher = entry['publisher']
    if not (set(publisher) == {'id', 'keys'} and publisher['id']):
        raise ValueError('invalid catalog value')
    keys = set()
    for key in publisher['keys']:
        if not set(key) == {'id', 'publicKey'}:
            raise ValueError('invalid catalog value')
        if not (key['id'] not in keys and key['id']):
            raise ValueError('invalid catalog value')
        if not len(base64.b64decode(key['publicKey'], validate=True)) == 32:
            raise ValueError('invalid catalog value')
        keys.add(key['id'])
    versions = set()
    for release in entry['releases']:
        if not set(release) == {'version', 'api', 'url', 'sha256', 'keyID'}:
            raise ValueError('invalid catalog value')
        version = semver(release['version'])
        if not version not in versions:
            raise ValueError('duplicate release version')
        versions.add(version)
        if not set(release['api']) == {'minimum', 'maximumExclusive'}:
            raise ValueError('invalid catalog value')
        if not semver(release['api']['minimum']) < semver(release['api']['maximumExclusive']):
            raise ValueError('invalid catalog value')
        if not release['keyID'] in keys:
            raise ValueError('unknown publisher key')
        if not re.fullmatch('[0-9a-f]{64}', release['sha256']):
            raise ValueError('invalid checksum')
        url = urlparse(release['url'])
        if any(unquote(part) in ('.', '..') or '/' in unquote(part) or '\\' in unquote(part) for part in url.path.split('/')):
            raise ValueError('invalid release path segment')
        prefix = repository + '/releases/download/v' + release['version'] + '/'
        if not (release['url'].startswith(prefix) and url.path.endswith('.zip')):
            raise ValueError('release must reference its immutable version tag')
        if not (not url.query and (not url.fragment) and (not url.username) and (not url.password)):
            raise ValueError('invalid catalog value')
    return entry

def unique_object(pairs):
    result = {}
    for (k, v) in pairs:
        if k in result:
            raise ValueError('duplicate JSON key: ' + k)
        result[k] = v
    return result

def validate_catalog(root):
    seen = set()
    for path in sorted(Path(root).glob('*.json')):
        entry = validate(json.loads(path.read_text(), object_pairs_hook=unique_object))
        if not (path.stem == entry['id'] and entry['id'] not in seen):
            raise ValueError('duplicate or mismatched plugin identity')
        seen.add(entry['id'])
    return seen
def validate_index(index, expected_ids):
    if not isinstance(index, dict) or set(index) != {'schemaVersion', 'plugins'}:
        raise ValueError('unexpected index fields')
    if type(index['schemaVersion']) is not int or index['schemaVersion'] != 1:
        raise ValueError('unsupported index schema')
    if not isinstance(index['plugins'], list) or len(index['plugins']) > 1024:
        raise ValueError('invalid index size')
    seen = set()
    for entry in index['plugins']:
        if not isinstance(entry, dict) or set(entry) != {'id', 'path'}:
            raise ValueError('unexpected index entry fields')
        plugin_id = entry['id']
        if not isinstance(plugin_id, str) or not re.fullmatch('[a-z0-9]+(?:[.-][a-z0-9-]+)+', plugin_id):
            raise ValueError('invalid index identity')
        if plugin_id in seen or entry['path'] != f'plugins/{plugin_id}.json':
            raise ValueError('duplicate identity or noncanonical catalog path')
        seen.add(plugin_id)
    if seen != set(expected_ids):
        raise ValueError('index must reference every catalog entry exactly once')
    return seen


def validate_repository(root):
    root = Path(root)
    ids = validate_catalog(root / 'plugins')
    data = (root / 'index.json').read_bytes()
    if len(data) > 1_048_576:
        raise ValueError('index exceeds size limit')
    return validate_index(json.loads(data, object_pairs_hook=unique_object), ids)


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    print('Validated:', ', '.join(sorted(validate_repository(root))))
