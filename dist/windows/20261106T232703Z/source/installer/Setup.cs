// SPDX-License-Identifier: GPL-2.0-or-later
using System;
using System.Diagnostics;
using System.IO;
class Setup {
    static int Main() {
        try {
            Console.Title = "Ag-GIS Setup";
            Console.WriteLine("Ag-GIS — Farming in view");
            Console.WriteLine("Built on open source tools");
            string root = AppDomain.CurrentDomain.BaseDirectory;
            string powershell = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), @"WindowsPowerShell\v1.0\powershell.exe");
            var info = new ProcessStartInfo(powershell, "-NoProfile -ExecutionPolicy Bypass -File \"" + Path.Combine(root, "Install.ps1") + "\"");
            info.UseShellExecute = false;
            var process = Process.Start(info);
            process.WaitForExit();
            Console.WriteLine(process.ExitCode == 0 ? "Ag-GIS setup finished." : "Ag-GIS setup did not finish. Review the error above.");
            Console.WriteLine("Press Enter to close.");
            Console.ReadLine();
            return process.ExitCode;
        } catch (Exception error) {
            Console.Error.WriteLine(error.Message);
            Console.ReadLine();
            return 1;
        }
    }
}
