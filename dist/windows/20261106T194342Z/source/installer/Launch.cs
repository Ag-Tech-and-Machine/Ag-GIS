// SPDX-License-Identifier: GPL-2.0-or-later
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Text.RegularExpressions;
using System.Windows.Forms;

class StartupScreen : Form {
    static Bitmap LoadSymbol(string path) {
        // Our generated ICO stores PNG frames. Decode the largest frame directly;
        // Framework Icon.ToBitmap does not reliably handle PNG-backed ICO files.
        byte[] data = File.ReadAllBytes(path);
        if (data.Length < 22 || BitConverter.ToUInt16(data, 2) != 1)
            throw new Exception("Invalid Ag-GIS icon file. Run setup again.");
        int count = BitConverter.ToUInt16(data, 4);
        int entry = 6 + (count - 1) * 16;
        if (count < 1 || entry + 16 > data.Length) throw new Exception("Invalid Ag-GIS icon directory.");
        int length = checked((int)BitConverter.ToUInt32(data, entry + 8));
        int offset = checked((int)BitConverter.ToUInt32(data, entry + 12));
        if (offset < 0 || length < 8 || offset > data.Length - length) throw new Exception("Invalid Ag-GIS icon image.");
        using (var stream = new MemoryStream(data, offset, length))
        using (var image = Image.FromStream(stream)) return new Bitmap(image);
    }
    protected override bool ShowWithoutActivation { get { return true; } }
    public StartupScreen(string root) {
        Text = "Ag-GIS";
        FormBorderStyle = FormBorderStyle.None;
        StartPosition = FormStartPosition.CenterScreen;
        ClientSize = new Size(500, 250);
        BackColor = Color.FromArgb(245, 242, 232);
        ForeColor = Color.FromArgb(23, 63, 53);
        ShowInTaskbar = false;
        Controls.Add(new PictureBox { Image = LoadSymbol(Path.Combine(root, "Ag-GIS.ico")),
            SizeMode = PictureBoxSizeMode.Zoom, Location = new Point(28, 30), Size = new Size(96, 96) });
        Controls.Add(new Label { Text = "Ag-GIS", Font = new Font("Segoe UI", 32, FontStyle.Bold),
            AutoSize = true, Location = new Point(142, 30) });
        Controls.Add(new Label { Text = "FARMING IN VIEW", Font = new Font("Segoe UI", 11),
            AutoSize = true, Location = new Point(147, 94) });
        Controls.Add(new Label { Text = "Built on open source tools", Font = new Font("Segoe UI", 12),
            AutoSize = true, Location = new Point(32, 158) });
        Controls.Add(new Label { Text = "Opening your workspace...", Font = new Font("Segoe UI", 10),
            AutoSize = true, ForeColor = Color.FromArgb(82, 102, 93), Location = new Point(32, 205) });
    }
}

class Launch {
    [STAThread] static int Main(string[] args) {
        try {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            string root = AppDomain.CurrentDomain.BaseDirectory;
            if (args.Length == 2 && args[0] == "--render-splash") {
                using (var preview = new StartupScreen(root))
                using (var bitmap = new Bitmap(preview.Width, preview.Height)) {
                    preview.StartPosition = FormStartPosition.Manual;
                    preview.Location = new Point(-32000, -32000);
                    preview.Show();
                    Application.DoEvents();
                    preview.DrawToBitmap(bitmap, new Rectangle(Point.Empty, bitmap.Size));
                    preview.Close();
                    bitmap.Save(args[1], ImageFormat.Png);
                }
                return 0;
            }
            bool noSplash = args.Length == 1 && args[0] == "--no-splash";
            if (args.Length != 0 && !noSplash) throw new Exception("Unsupported Ag-GIS launcher option.");
            string[] config = File.ReadAllLines(Path.Combine(root, "launch.txt"));
            if (config.Length != 2 || !Regex.IsMatch(config[1], @"^[A-Za-z0-9_-]+$"))
                throw new Exception("Invalid Ag-GIS launcher configuration. Run setup again.");
            string runner = Path.Combine(config[0], @"bin\qgis-ltr.bat");
            if (!File.Exists(runner)) throw new Exception("The mapping runtime was not found. Repair the installation or run Ag-GIS setup again.");
            var existing = new HashSet<int>();
            foreach (var process in Process.GetProcessesByName("qgis-ltr-bin")) {
                using (process) existing.Add(process.Id);
            }
            // Preserve the native environment bootstrap; suppress only its startup artwork.
            var info = new ProcessStartInfo(runner, "--nologo --profile " + config[1]);
            info.UseShellExecute = true;
            info.WindowStyle = ProcessWindowStyle.Hidden;
            Process.Start(info);
            if (!noSplash) {
                using (var splash = new StartupScreen(root))
                using (var timer = new Timer()) {
                    var elapsed = Stopwatch.StartNew();
                    timer.Interval = 500;
                    timer.Tick += delegate {
                        bool ready = false;
                        foreach (var process in Process.GetProcessesByName("qgis-ltr-bin")) {
                            using (process) {
                                try {
                                    if (!existing.Contains(process.Id) && process.MainWindowTitle.StartsWith("Ag-GIS")) ready = true;
                                } catch (InvalidOperationException) { }
                            }
                        }
                        if (ready || elapsed.Elapsed.TotalSeconds >= 45) splash.Close();
                    };
                    timer.Start();
                    Application.Run(splash);
                }
            }
            return 0;
        } catch (Exception error) {
            if (args.Length > 0) { Console.Error.WriteLine(error.ToString()); return 1; }
            MessageBox.Show(error.Message, "Ag-GIS", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
