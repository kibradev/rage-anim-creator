// ycd2xml <gtaDir> <outDir> <name|prefix*> ...   (names without extension)
// Reads .ycd directly from the game RPFs via CodeWalker.Core and writes <name>.ycd.xml (read-only on the game).
using CodeWalker.GameFiles;

// xml2ycd <in.ycd.xml> <out.ycd>   |   ycd2xmlfile <in.ycd> <out.ycd.xml>  (standalone files, no game keys needed)
if (args.Length == 3 && args[0] == "xml2ycd")
{
    var doc = new System.Xml.XmlDocument(); doc.LoadXml(File.ReadAllText(args[1]));
    var data = XmlMeta.GetYcdData(doc);
    if (data == null) { Console.Error.WriteLine("xml has no ClipDictionary"); return 2; }
    File.WriteAllBytes(args[2], data);
    Console.WriteLine($"wrote {args[2]} ({data.Length} bytes)");
    return 0;
}
if (args.Length == 3 && args[0] == "ycd2xmlfile")
{
    var ycd = new YcdFile();
    RpfFile.LoadResourceFile(ycd, File.ReadAllBytes(args[1]), 46);
    File.WriteAllText(args[2], MetaXml.GetXml(ycd, out _));
    Console.WriteLine($"wrote {args[2]}");
    return 0;
}

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
