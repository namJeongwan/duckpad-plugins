import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validate', ROOT / 'scripts/validate.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.entry = json.loads((ROOT / 'plugins/com.duckpad.clipboard-history.json').read_text())
    def test_draft_is_valid_and_not_installable(self):
        self.entry['releases'] = []
        module.validate(self.entry)
        self.assertEqual(self.entry['releases'], [])
    def test_release_requires_publisher_and_immutable_asset(self):
        self.entry['publisher']['keys'] = [{'id': 'test', 'publicKey': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='}]
        release = {'version':'0.1.0', 'api':{'minimum':'1.1.0','maximumExclusive':'2.0.0'}, 'keyID':'test', 'sha256':'a'*64, 'url':self.entry['repository']+'/releases/download/v0.1.0/plugin.zip'}
        self.entry['releases'] = [release]
        module.validate(self.entry)
        for field, value in [('keyID','unknown'), ('sha256','x'), ('url','https://example.com/latest.zip'), ('url', self.entry['repository']+'/releases/download/v0.1.0/../evil.zip'), ('url', self.entry['repository']+'/releases/download/v0.1.0/%2e%2e/evil.zip')]:
            bad = copy.deepcopy(self.entry); bad['releases'][0][field] = value
            with self.assertRaises(ValueError): module.validate(bad)
        self.entry['releases'].append(copy.deepcopy(release))
        with self.assertRaises(ValueError): module.validate(self.entry)
    def test_duplicate_keys_and_versions_rejected(self):
        with self.assertRaises(ValueError): json.loads('{"id":1,"id":2}', object_pairs_hook=module.unique_object)
        self.entry['schemaVersion'] = 99
        with self.assertRaises(ValueError): module.validate(self.entry)
    def test_catalog_files_match_identities(self):
        self.assertEqual(module.validate_catalog(ROOT/'plugins'), {'com.duckpad.clipboard-history', 'com.duckpad.plantuml'})

    def test_index_matches_all_catalogs(self):
        self.assertEqual(module.validate_repository(ROOT), {'com.duckpad.clipboard-history', 'com.duckpad.plantuml'})

    def test_index_rejects_missing_extra_duplicate_and_unsafe_paths(self):
        index = json.loads((ROOT / 'index.json').read_text())
        expected = {'com.duckpad.clipboard-history', 'com.duckpad.plantuml'}
        for path in ['../plugin.json', 'https://example.com/plugin.json', 'plugins/wrong.json', 'plugins/%2e%2e/plugin.json']:
            bad = copy.deepcopy(index); bad['plugins'][0]['path'] = path
            with self.assertRaises(ValueError): module.validate_index(bad, expected)
        bad = copy.deepcopy(index); bad['plugins'].append(copy.deepcopy(bad['plugins'][0]))
        with self.assertRaises(ValueError): module.validate_index(bad, expected)
        with self.assertRaises(ValueError): module.validate_index(index, set())
        with self.assertRaises(ValueError): module.validate_index(index, expected | {'com.example.missing'})
        with self.assertRaises(ValueError): module.validate_index({'schemaVersion': 2, 'plugins': []}, set())
        with self.assertRaises(ValueError): module.validate_index({'schemaVersion': True, 'plugins': []}, set())
        module.validate_index({'schemaVersion': 1, 'plugins': []}, set())

if __name__ == '__main__': unittest.main()
