using System.Text.Json;
using Graphiphy.Pipeline;
using Graphiphy.Models;
using Graphiphy.Validation;
using Graphiphy.Cache;

// Offline adapter: use the actual Graphiphy pipeline, export its final graph.
if (args.Length != 2) { Console.Error.WriteLine("Usage: ReaGraphiphy <source-root> <output-dir>"); return 2; }
var root = Path.GetFullPath(args[0]);
var output = Path.GetFullPath(args[1]);
Directory.CreateDirectory(output);
var warnings = new List<string>();
var json = new JsonSerializerOptions { WriteIndented = true };
try
{
    var result = await RepositoryAnalysis.RunAsync(root,
        cacheDir: Path.Combine(output, "extraction-cache"),
        malformedEdgeBehavior: MalformedEdgeBehavior.Warn,
        onProgress: message => {
            if (message.StartsWith("Warning")) { lock (warnings) warnings.Add(message); }
            else Console.Error.WriteLine(message);
        });
    var graph = new GraphData {
        Nodes = result.Graph.Vertices.ToList(),
        Edges = result.Graph.Edges.Select(edge => edge.Tag).ToList(),
        Metadata = new() { ["source_root"] = root, ["engine"] = "Graphiphy", ["evidence_type"] = "static-source-analysis" }
    };
    await File.WriteAllTextAsync(Path.Combine(output, "upstream-graph.json"), JsonSerializer.Serialize(graph, json));
    // Upstream merges same-named methods across files, even when unrelated.
    // Keep an auditable per-file navigation graph from its cached extractions.
    var navigation = new GraphData { Metadata = new() {
        ["source_root"] = root, ["engine"] = "Graphiphy cached AST extractions",
        ["limitations"] = "File-scoped symbols; overloads and nested same-name declarations may collapse. Calls are candidates, not resolved dispatch. Cross-file calls are not resolved."
    }};
    var cache = new ExtractionCache(Path.Combine(output, "extraction-cache"));
    var dropped = 0;
    foreach (var file in result.Files)
    {
        var item = cache.Load(ExtractionCache.FileHash(file.AbsolutePath, root));
        if (item is null) continue;
        var prefix = Path.GetRelativePath(root, file.AbsolutePath).Replace('\\', '/') + "::";
        var ids = item.Nodes.Select(n => n.Id).ToHashSet();
        foreach (var node in item.Nodes) { node.Id = prefix + node.Id; navigation.Nodes.Add(node); }
        foreach (var edge in item.Edges)
        {
            if (!ids.Contains(edge.Source) || !ids.Contains(edge.Target)) { dropped++; continue; }
            edge.Source = prefix + edge.Source;
            edge.Target = prefix + edge.Target;
            if (edge.Relation == "calls") edge.ConfidenceString = "AMBIGUOUS";
            navigation.Edges.Add(edge);
        }
    }
    await File.WriteAllTextAsync(Path.Combine(output, "graph.json"), JsonSerializer.Serialize(navigation, json));
    await File.WriteAllTextAsync(Path.Combine(output, "report.md"), result.Report);
    await File.WriteAllTextAsync(Path.Combine(output, "warnings.json"), JsonSerializer.Serialize(warnings, json));
    var summary = new { files = result.Files.Count, nodes = navigation.Nodes.Count, edges = navigation.Edges.Count,
        upstream_nodes = graph.Nodes.Count, upstream_edges = graph.Edges.Count, dropped_unresolved_edges = dropped,
        warnings = warnings.Count, source_root = root };
    await File.WriteAllTextAsync(Path.Combine(output, "summary.json"), JsonSerializer.Serialize(summary, json));
    Console.WriteLine(JsonSerializer.Serialize(summary));
    return navigation.Nodes.Count > 0 ? 0 : 3;
}
catch (Exception ex)
{
    Console.Error.WriteLine(ex);
    return 1;
}
