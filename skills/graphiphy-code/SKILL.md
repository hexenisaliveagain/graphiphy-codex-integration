---
name: graphiphy-code
description: Automatically use local Graphiphy graphs during ordinary source-code work, including reading projects, debugging, implementing features, refactoring and reviewing changes. Supports Arduino .ino as C++ as well as C/C++, C#, Java, Python, JS/TS, Go and Rust. Use without a separate user invocation; REA is not needed for source repositories.
---

# Graphiphy for everyday coding

For an ordinary coding task, automatically inspect or refresh the selected project's graph at the first substantive source investigation or edit. The user need not invoke this skill. Follow repository instructions first. Identify the actual source repository/subproject, not a parent documents folder, SDK installation, generated build tree or unrelated project. Skip when no supported code exists, or the user excludes graph analysis. This is local static analysis; do not invoke REA for an ordinary source repository.

Run the installed helper with the explicit project root; `--source` can narrow to a known relevant directory within it, and may be repeated:

```powershell
python "<this-skill>/scripts/ensure_graph.py" --project "<absolute-project-root>" --output "<workspace>/graphiphy-project-out"
```

No binary, API key, remote service or application execution is required. `.ino` is parsed directly as C++ by the patched Graphiphy classifier/extractor. Original `.ino` paths and line numbers are retained. This does not run Arduino preprocessing, create prototypes, expand macros or merge multiple sketch tabs; compilation remains authoritative.

The helper hashes source contents, ignore rules, its own implementation and engine files. It reuses verified output and automatically builds when code changes. Results include `built`, `cached`, `skipped_no_code`, `unavailable`, or `failed`. The selected project gets a distinct namespace; `latest.json` points to the latest requested result. Keep all generated products outside the project/source roots. Do not build concurrently into the same namespace. Built-in noise directories and symlinks/junctions are excluded from fingerprint discovery; engine file selection additionally honors nested `.gitignore` rules.

Read the returned `summary.json` and relevant warnings, then use a focused query for the current task:

```powershell
python "<this-skill>/scripts/query_graph.py" "<returned-output>/graph.json" "<symbol>" --limit 8
```

Open returned source locations. Use the graph to orient edits and locate candidate relationships; use normal language tools, searches, compiler results and tests to establish behavior and impact. After code changes that affect the current investigation, refresh once before using the graph for final conclusions; avoid rebuilding after every keystroke. If graph generation is unavailable or fails, report that limitation once and continue normal coding. Do not automatically install software or retry unchanged failures.

## Reliability and installed tools

The installed adapter is `<configured-bridge>/ReaGraphiphy.dll`; it uses actual Graphiphy AST extractions. `graph.json` qualifies symbols by file and avoids upstream's global name deduplication. `upstream-graph.json` and `report.md` preserve upstream output for diagnostics; their rankings can merge unrelated same-name symbols and must not be used as architecture evidence.

Calls are `AMBIGUOUS` candidates. Cross-file dispatch, includes, templates, function pointers, preprocessor conditions and overloads are not fully resolved; same-name symbols within a file can collapse. Some external/dangling edges are dropped and counted. Absence from the graph does not establish dead code or missing dependencies. Optional Leiden clustering is unavailable on this installation. No graph result proves firmware or hardware behavior.

For binary/package reverse engineering, apply `reverse-engineer-anything` and `rea-graphiphy` instead; their existing helper delegates to this shared implementation in artifact mode.
