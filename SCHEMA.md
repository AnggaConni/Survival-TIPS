# JSON Catalogue Schema (v2)

Each catalogue is valid UTF-8 JSON and has an `articles` array.

Required article fields: `id`, `title`, `status`.
Recommended fields: `category`, `stage_ids`, `summary`, `body`, `environment`, `climate`, `season`, `materials`, `tools`, `steps`, `safety`, `limitations`, `images`, `sources`, `review`.

Image objects support `url`, `alt`, `caption`, `credit`, `role`. Use repository-relative paths like `thumb/galon.png`.

The catalogue manifest at `data/index.json` lists the JSON files to load. Add new catalogues there.