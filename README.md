# Graphiphy integration for Codex and REA

Source-only offline adapter and two companion skills. The adapter calls the real
Graphiphy AST pipeline, then exports a file-qualified navigation graph. No API key,
LLM call, target execution or proprietary application source is required.

Upstream: [tmcqueen/ngraphify](https://github.com/tmcqueen/ngraphify), pinned commit
`6cddd335596f8dbf93ec9018752190379603e29f`. Its full source is not vendored.
The small included patch adds `.ino`/`.hxx` detection, C++ extraction for Arduino
and build-directory ignores. This project is distributed under GPLv3; preserve
upstream licensing and attribution when building or redistributing it.

## Build once

Requirements: Git, Python **3.12+**, .NET SDK **10**, and package/network access for
the initial clone and NuGet restore. Run from this repository's root:

```sh
git clone https://github.com/tmcqueen/ngraphify.git vendor/ngraphify
git -C vendor/ngraphify checkout 6cddd335596f8dbf93ec9018752190379603e29f
git -C vendor/ngraphify apply ../../patches/arduino-and-build-ignores.patch
dotnet publish bridge/ReaGraphiphy.csproj -c Release -o bridge-bin -p:GraphiphyEnabled=false
```

The relative patch path is interpreted from the upstream working tree. Build
outputs, NuGet caches and the downloaded vendor checkout stay ignored. No built
DLL/EXE, third-party package, Microsoft application file or analysis output is
included in this repository.

## Run without installation

```sh
python skills/graphiphy-code/scripts/ensure_graph.py --project /absolute/source --output /absolute/output
python skills/rea-graphiphy/scripts/ensure_graph.py --artifact /absolute/app.bin --source /absolute/recovered-code --output /absolute/output
python skills/graphiphy-code/scripts/query_graph.py /absolute/output/namespace/fingerprint/graph.json Symbol --limit 8
```

Keep output outside the selected project. Artifact mode records the supplied
artifact hash; it does not prove provenance of recovered source. Use REA evidence
to establish the artifact/code mapping. Normal source-repository work needs no REA.

The helper finds `bridge-bin/ReaGraphiphy.dll` in this checkout. Override with
`--bridge /absolute/ReaGraphiphy.dll` or the `GRAPHIPHY_BRIDGE` environment variable.
No machine-specific paths are embedded in the published helpers.

## Install the two skills

```sh
python scripts/install_skills.py --bridge /absolute/bridge-bin/ReaGraphiphy.dll
```

This explicit command copies only these skills into `$CODEX_HOME/skills` (default
`~/.codex/skills`). It refuses to overwrite existing skills. It writes the local
engine path to an ignored `scripts/engine.json`; keep that machine-local file
private. Use `--codex-home` to choose a different installation directory.
The installer does not edit an existing REA skill, AGENTS.md or application settings.

For automatic use, add an instruction to your project's AGENTS.md to apply the
installed `graphiphy-code` skill at the first substantive source investigation.
In an existing REA workflow, request the companion `rea-graphiphy` skill when
supported recovered code for the selected artifact is available.

## Cache and limitations

Source contents, ignore files, helper and engine dependencies are fingerprinted.
Unchanged verified graphs are reused; changed or corrupted products are rebuilt.
Generated products remain outside input roots. Do not build concurrently into the
same project namespace. Symlink/junction directories and common build noise are
excluded. This integration does not upload source or generated graphs.

Use `graph.json` for file-qualified navigation. Upstream same-name merging remains
visible in `upstream-graph.json` and `report.md`; their rankings are diagnostic.
Calls are ambiguous candidates, not resolved dispatch. Overloads can collapse;
some dangling edges are dropped and counted. Optional Leiden clustering may be
unavailable. `.ino` is parsed as C++ without Arduino preprocessing or tab merging.
Compilation and runtime/hardware evidence remain authoritative.

## Verify

```sh
python -m unittest discover -s tests -v
```

Tests use synthetic source fixtures. Set `GRAPHIPHY_TEST_BRIDGE` to an existing
adapter DLL to enable the real engine/cache/Arduino smoke test; it is skipped if
no engine is configured. No proprietary files or device logs are test fixtures.

## Polski

Repozytorium zawiera adapter, dwa skille i małą łatkę Arduino do upstreamu.
Nie zawiera SDK, gotowych bibliotek, aplikacji Microsoft, kluczy ani logów telefonu.
Kod użytkownika i wyniki grafów pozostają lokalne. Powyższe polecenia pozwalają
odtworzyć integrację bez kopiowania prywatnego środowiska autora.
