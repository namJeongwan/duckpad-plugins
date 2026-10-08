# Duckpad Plugins

The plugin catalog for Duckpad. Plugin source code and release assets live in each plugin's own repository.

- App and host API: https://github.com/namJeongwan/duckpad
- Clipboard History: https://github.com/namJeongwan/duckpad-plugin-clipboard-history
- PlantUML: https://github.com/namJeongwan/duckpad-plugin-plantuml (Duckpad 0.10.0 / host API 1.4.0 or later)

Each `plugins/<plugin-id>.json` records identity, source repository, descriptions, publisher public keys, and immutable releases. A release records its version, supported host API range, package URL, SHA-256, and signing key ID. Plugin versions are independent of Duckpad versions.

Run `python3 -m unittest discover -s tests` and `python3 scripts/validate.py` before submitting a catalog PR. Draft entries have no releases and must not appear as installable plugins. Never put signing private keys or plugin implementation code here.

Publishing order: build and sign in the plugin repository, publish immutable release assets, then submit a catalog PR with the exact download URL and digest. Correct a bad release by adding a new version, never by replacing its bytes.

Developer documentation is maintained in the host repository under `docs/plugins/overview.md`, `developer-guide.md`, and `api-reference.md`. These documents accompany the unreleased host work; they are not a claim of a published SDK.

## Discovery index

Duckpad starts discovery at `index.json` in the repository root, fetched from the `main` branch through GitHub Raw. It contains only references; descriptions, publisher keys, and release versions remain in each per-plugin JSON file.

```json
{
  "schemaVersion": 1,
  "plugins": [
    {
      "id": "com.duckpad.clipboard-history",
      "path": "plugins/com.duckpad.clipboard-history.json"
    }
  ]
}
```

After adding or removing a plugin catalog, run:

```sh
python3 scripts/generate_index.py
python3 scripts/generate_index.py --check
python3 scripts/validate.py
python3 -m unittest discover -s tests
```

The generated index is deterministic and includes every catalog entry exactly once, including drafts. An entry with `releases: []` is discoverable metadata, not an installable release. Duckpad checks indexed installed plugins for compatible published updates. The index does not authorize publisher keys or replace package signature verification. A missing or invalid index is a failed catalog check, not proof that there are no updates. The all-plugins browsing/install screen is not implemented yet.

Publish the index and its per-plugin files together. `validate.py` rejects missing references, unknown entries, duplicate IDs, and paths other than `plugins/<id>.json`. The index supports up to 1,024 entries and a 1 MiB response.
