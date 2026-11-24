using System;
using System.IO;
using System.IO.Compression;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using System.Collections.Generic;
internal static class StandaloneLauncher {
    const string Magic = "ANCLICKERAPP0001";
    [STAThread]
    static int Main() {
        try {
            AppContext.SetSwitch("Switch.System.IO.UseLegacyPathHandling", false);
            AppContext.SetSwitch("Switch.System.IO.BlockLongPaths", false);
            string self = System.Reflection.Assembly.GetExecutingAssembly().Location;
            using (var source = new FileStream(LongPath(self), FileMode.Open, FileAccess.Read, FileShare.Read)) {
                if (source.Length < 64) throw new InvalidDataException("应用文件不完整。");
                source.Position = source.Length - 64;
                var reader = new BinaryReader(source);
                if (Encoding.ASCII.GetString(reader.ReadBytes(16)) != Magic) throw new InvalidDataException("应用包标记无效。");
                long offset = reader.ReadInt64(), length = reader.ReadInt64();
                byte[] expected = reader.ReadBytes(32);
                if (offset < 1 || length < 22 || offset > source.Length - 64 || length != source.Length - 64 - offset)
                    throw new InvalidDataException("应用包长度无效。");
                string identity = BitConverter.ToString(expected).Replace("-", "").ToLowerInvariant();
                using (var segment = new SegmentStream(source, offset, length))
                using (var sha = SHA256.Create()) {
                    if (!Equal(sha.ComputeHash(segment), expected)) throw new InvalidDataException("应用包校验失败，请重新获取完整 EXE。");
                }
                string local = Environment.GetEnvironmentVariable("LOCALAPPDATA");
                if (String.IsNullOrWhiteSpace(local)) local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
                string parent = Path.Combine(Path.GetFullPath(local), "AnClicker", "StandaloneApps");
                string cache = Path.Combine(parent, identity);
                Directory.CreateDirectory(LongPath(parent));
                using (var mutex = new Mutex(false, "Local\\AnClickerStandaloneExtract-" + identity)) {
                    bool owned = false;
                    try {
                        try { owned = mutex.WaitOne(TimeSpan.FromMinutes(10)); }
                        catch (AbandonedMutexException) { owned = true; }
                        if (!owned) throw new IOException("另一个实例正在准备运行环境，请稍后重试。");
                        string ready = Path.Combine(cache, ".ready");
                        if (!File.Exists(LongPath(ready)) || File.ReadAllText(LongPath(ready)) != identity ||
                            !File.Exists(LongPath(Path.Combine(cache, "AnClicker.exe"))) ||
                            !File.Exists(LongPath(Path.Combine(cache, "standalone-project.json")))) {
                            if (Directory.Exists(LongPath(cache))) throw new IOException("运行缓存不完整，请移走以下目录后重试：\n" + cache);
                            string staged = Path.Combine(parent, ".partial-" + Guid.NewGuid().ToString("N"));
                            Directory.CreateDirectory(LongPath(staged));
                            try {
                                using (var segment = new SegmentStream(source, offset, length))
                                using (var archive = new ZipArchive(segment, ZipArchiveMode.Read, true)) {
                                    var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                                    foreach (var entry in archive.Entries) {
                                        string name = entry.FullName.Replace('\\', '/');
                                        if (name.StartsWith("/") || name.Contains(":") || Array.Exists(name.Split('/'), x => x == ".." || x == "."))
                                            throw new InvalidDataException("应用包包含非法路径。");
                                        string path = Path.GetFullPath(Path.Combine(staged, name.Replace('/', Path.DirectorySeparatorChar)));
                                        if (!path.StartsWith(staged + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) ||
                                            !seen.Add(path)) throw new InvalidDataException("应用包包含重复或越界路径。");
                                        if (name.EndsWith("/")) { Directory.CreateDirectory(LongPath(path)); continue; }
                                        Directory.CreateDirectory(LongPath(Path.GetDirectoryName(path)));
                                        using (var input = entry.Open())
                                        using (var output = new FileStream(LongPath(path), FileMode.CreateNew, FileAccess.Write)) input.CopyTo(output);
                                    }
                                }
                                if (!File.Exists(LongPath(Path.Combine(staged, "AnClicker.exe"))) || !File.Exists(LongPath(Path.Combine(staged, "standalone-project.json"))))
                                    throw new InvalidDataException("应用包缺少执行入口或项目。");
                                File.WriteAllText(LongPath(Path.Combine(staged, ".ready")), identity);
                                Directory.Move(LongPath(staged), LongPath(cache));
                            } finally {
                                if (Directory.Exists(LongPath(staged))) { try { Directory.Delete(LongPath(staged), true); } catch { } }
                            }
                        }
                    } finally { if (owned) mutex.ReleaseMutex(); }
                }
                var start = new ProcessStartInfo(Path.Combine(cache, "AnClicker.exe")) {
                    WorkingDirectory = cache, UseShellExecute = false, CreateNoWindow = true
                };
                start.EnvironmentVariables.Remove("PYTHONPATH");
                start.EnvironmentVariables.Remove("PYTHONHOME");
                start.EnvironmentVariables["ANCLICKER_DATA_DIR"] = Path.Combine(cache, "Data");
                start.EnvironmentVariables["ANCLICKER_STANDALONE_EXE"] = self;
                using (var process = Process.Start(start)) { process.WaitForExit(); return process.ExitCode; }
            }
        } catch (Exception error) {
            try { string logRoot = Environment.GetEnvironmentVariable("LOCALAPPDATA") ?? Path.GetTempPath(); File.AppendAllText(Path.Combine(logRoot, "AnClicker-standalone-error.log"), DateTime.Now.ToString("O") + "\n" + error.ToString() + "\n"); } catch { }
            if (Environment.GetEnvironmentVariable("ANCLICKER_STANDALONE_NO_ERROR_DIALOG") != "1") MessageBox.Show(error.Message, "独立应用无法启动", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
    static string LongPath(string path) {
        string full = Path.GetFullPath(path);
        return full.StartsWith(@"\\") ? @"\\?\UNC\" + full.Substring(2) : @"\\?\" + full;
    }
    static bool Equal(byte[] a, byte[] b) {
        if (a.Length != b.Length) return false;
        int diff = 0; for (int i = 0; i < a.Length; i++) diff |= a[i] ^ b[i]; return diff == 0;
    }
}
internal sealed class SegmentStream : Stream {
    readonly Stream source; readonly long offset, length; long position;
    public SegmentStream(Stream source, long offset, long length) { this.source = source; this.offset = offset; this.length = length; }
    public override bool CanRead { get { return true; } }
    public override bool CanSeek { get { return true; } }
    public override bool CanWrite { get { return false; } }
    public override long Length { get { return length; } }
    public override long Position { get { return position; } set { Seek(value, SeekOrigin.Begin); } }
    public override int Read(byte[] buffer, int index, int count) {
        source.Position = offset + position;
        int read = source.Read(buffer, index, (int)Math.Min(count, length - position));
        position += read; return read;
    }
    public override long Seek(long value, SeekOrigin origin) {
        long next = origin == SeekOrigin.Begin ? value : checked((origin == SeekOrigin.Current ? position : length) + value);
        if (next < 0 || next > length) throw new IOException("Invalid seek");
        return position = next;
    }
    public override void Flush() {}
    public override void SetLength(long value) { throw new NotSupportedException(); }
    public override void Write(byte[] buffer, int index, int count) { throw new NotSupportedException(); }
}
