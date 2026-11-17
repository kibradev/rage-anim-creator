// ycd2xml <gtaDir> <outDir> <name|prefix*> ...   (names without extension)
// Reads .ycd directly from the game RPFs via CodeWalker.Core and writes <name>.ycd.xml (read-only on the game).
using CodeWalker.GameFiles;

if (args.Length < 3) { Console.Error.WriteLine("usage: ycd2xml <gtaDir> <outDir> <name|prefix*>..."); return 1; }
string gta = args[0], outDir = args[1];
var patterns = args.Skip(2).Select(a => a.ToLowerInvariant()).ToList();
Directory.CreateDirectory(outDir);

GTA5Keys.LoadFromPath(gta, false, null);
var man = new RpfManager();
man.Init(gta, false, s => { }, e => Console.Error.WriteLine("ERR " + e), false, false);

bool Match(string n) => patterns.Any(p => p.EndsWith("*") ? n.StartsWith(p[..^1]) : n == p);

var chosen = new Dictionary<string, RpfFileEntry>();
foreach (var rpf in man.AllRpfs)
{
    if (rpf.AllEntries == null) continue;
    foreach (var e in rpf.AllEntries)
    {
        if (e is not RpfFileEntry fe || !fe.NameLower.EndsWith(".ycd")) continue;
        var n = fe.NameLower[..^4];
        if (Match(n)) chosen[n] = fe; // later archives (DLC) override earlier ones
    }
}
Console.WriteLine($"matched {chosen.Count} ycd");
int ok = 0;
foreach (var (n, fe) in chosen)
{
    try
    {
        var ycd = man.GetFile<YcdFile>(fe);
        if (ycd == null) { Console.Error.WriteLine("load failed " + n); continue; }
        var xml = MetaXml.GetXml(ycd, out _);
        File.WriteAllText(Path.Combine(outDir, n + ".ycd.xml"), xml);
        ok++;
    }
    catch (Exception ex) { Console.Error.WriteLine("ERR " + n + ": " + ex.Message); }
}
Console.WriteLine($"exported {ok}");
return 0;
