---
name: rea-graphiphy
description: Automatically supplement REA reverse engineering with a local Graphiphy source graph when source, extracted JavaScript, or supported decompiled code for the selected target becomes available. Apply during REA investigations without requiring a separate user invocation.
---

# REA with Graphiphy

Use this alongside `reverse-engineer-anything`, preserving its target identity and evidence rules. During each REA investigation, check for known code directories belonging to the selected artifact at the first useful point, and again after extraction/decompilation creates code. Do not search unrelated applications or decompile an entire target just to obtain a graph. Supported extensions: C#, Java, Python, JS/JSX, TS/TSX, Go, Rust, C/C++ headers and sources, including Arduino `.ino` parsed as C++. Smali, APK/ASAR containers, native binaries and pseudocode text alone are not supported code inputs.

When eligible code exists, automatically run the helper; the user does not need to invoke this skill separately. Use the existing Python installation (`python`), paths relative to this skill, and explicit absolute paths for the artifact and code directories:

```powershell
python "<this-skill>/scripts/ensure_graph.py" --artifact "<selected-original-artifact>" --source "<confirmed-code-root>" --output "<workspace>/rea-graphiphy-out" --evidence "<REA Evidence ID or saved evidence path>"
```

Repeat `--source` for separate code roots; each remains a separate graph to avoid cross-language/cross-root invented links. Only select code established to belong to the current artifact/version. Existing human reports can establish that mapping; preserve their original provenance limitations. The helper does not establish that decompiled files exactly match an artifact merely because both paths were passed.

The helper invokes the installed Graphiphy .NET engine at `<configured-bridge>/ReaGraphiphy.dll`, offline, without an LLM/API call or target execution. It fingerprints the artifact, source contents, ignore files and engine dependencies; validates output hashes before reuse; and reports `built`, `cached`, `skipped_no_code`, `unavailable` or `failed`. Put output outside code roots. Do not run two builds concurrently into the same output directory. An engine change creates a separate extraction cache. No code means skip and continue REA; missing engine or failure means report that limitation and continue useful REA work without repeated identical attempts or automatic software installation.

After `built` or `cached`, inspect `summary.json` and relevant `warnings.json`, then use the graph for at least one focused navigation question relevant to the user's investigation:

```powershell
python "<this-skill>/scripts/query_graph.py" "<returned-output>/graph.json" "<class-or-method>" --limit 8
```

Open the original source at returned locations and verify relevant behavior with REA evidence where needed. Never treat graph edges as runtime observations or firmware support. Keep queries bounded and do not load an entire large graph into the conversation.

## Graph reliability

This Graphiphy revision merges same-named symbols across files in its standard pipeline. The adapter preserves that result as `upstream-graph.json` and its `report.md` for diagnostics, but uses cached AST extractions to produce a file-qualified navigation `graph.json` without cross-file name deduplication. Use the navigation graph for findings; do not use the upstream report's centrality ranking as architecture evidence.

Same-name overloads/nested declarations can still collapse within a file. The upstream Java extractor does not resolve dispatch or cross-file calls; navigation call edges are conservatively marked `AMBIGUOUS`. Dangling edges are dropped and counted in `summary.json`. Import nodes may represent references rather than definitions. Do not infer a dependency is absent from a failed graph search. Leiden community clustering is optional and unavailable on this installation; this does not prevent AST extraction/navigation. All graph results are ordinary source analysis, not new REA Evidence IDs.

## Shared project helper

The REA `scripts/ensure_graph.py` entrypoint delegates to
`<skills-root>/graphiphy-code/scripts/ensure_graph.py`.
Artifact-mode arguments remain unchanged. Ordinary source projects use that
skill's `--project` mode, without REA or an artifact file. `.ino` keeps its original
path and line numbers; no Arduino preprocessing or sketch-tab merging is performed.
