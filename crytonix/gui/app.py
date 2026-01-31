import customtkinter as ctk
import threading
import sys
import os
from crytonix.dashboard import ProjectDashboard
from crytonix.tools import DesktopToolbox, FileToolbox, SystemToolbox, AutomationToolbox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CrytonixApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Crytonix AI - Professional Edition")
        self.geometry("1100x700")

        # Grid layout (2 columns)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="CRYTONIX", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.sidebar_btn_1 = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard)
        self.sidebar_btn_1.grid(row=1, column=0, padx=20, pady=10)

        self.sidebar_btn_2 = ctk.CTkButton(self.sidebar_frame, text="Tools", command=self.show_tools)
        self.sidebar_btn_2.grid(row=2, column=0, padx=20, pady=10)

        self.sidebar_btn_3 = ctk.CTkButton(self.sidebar_frame, text="Settings", command=self.show_settings)
        self.sidebar_btn_3.grid(row=3, column=0, padx=20, pady=10)

        # Main Content Area
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Frames
        self.dashboard_frame = DashboardFrame(self.main_frame)
        self.tools_frame = ToolsFrame(self.main_frame)
        self.settings_frame = ctk.CTkFrame(self.main_frame) # Placeholder

        self.show_dashboard()

    def show_dashboard(self):
        self.clear_main()
        self.dashboard_frame.grid(row=0, column=0, sticky="nsew")
        self.dashboard_frame.refresh_stats()

    def show_tools(self):
        self.clear_main()
        self.tools_frame.grid(row=0, column=0, sticky="nsew")

    def show_settings(self):
        self.clear_main()
        lbl = ctk.CTkLabel(self.main_frame, text="Settings coming soon...", font=("Arial", 24))
        lbl.grid(row=0, column=0)

    def clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.grid_forget()

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.dash_logic = ProjectDashboard()

        self.stats_label = ctk.CTkLabel(self, text="Project Health", font=("Arial", 20, "bold"))
        self.stats_label.pack(pady=20)

        self.info_box = ctk.CTkTextbox(self, width=600, height=400)
        self.info_box.pack(pady=10)

        self.refresh_btn = ctk.CTkButton(self, text="Refresh Data", command=self.refresh_stats)
        self.refresh_btn.pack(pady=10)

    def refresh_stats(self):
        self.info_box.delete("0.0", "end")
        self.info_box.insert("0.0", "Loading data... Please wait.")
        # Fetch data in background thread
        threading.Thread(target=self._fetch_stats_thread, daemon=True).start()

    def _fetch_stats_thread(self):
        stats = self.dash_logic.get_project_stats()
        git = self.dash_logic.get_git_status()
        tasks = self.dash_logic.scan_tasks()

        # Build report string
        report = f"📂 Files: {stats['files']}\n"
        report += f"📝 LOC: {stats['lines']:,}\n\n"

        if git['active']:
            report += f"🌿 Git Branch: {git['branch']}\n"
            report += f"📦 Changes: {git['changed_files']}\n\n"
        else:
            report += "🌿 Not a git repo\n\n"

        report += f"✅ Pending Tasks (TODOs): {len(tasks)}\n"
        for t in tasks[:5]:
            report += f"  - {t['file']}:{t['line']} {t['content'][:30]}...\n"

        # Update UI safely (customtkinter is reasonably thread-safe for simple updates, but best practice used here)
        self.after(0, lambda: self._update_stats_ui(report))

    def _update_stats_ui(self, report):
        self.info_box.delete("0.0", "end")
        self.info_box.insert("0.0", report)

class ToolsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.label = ctk.CTkLabel(self, text="Quick Tools", font=("Arial", 20, "bold"))
        self.label.pack(pady=20)

        # Grid of buttons
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(pady=10, fill="both", expand=True)

        # Tools
        btn1 = ctk.CTkButton(self.grid_frame, text="Open Browser", command=lambda: DesktopToolbox.browser_open("https://google.com"))
        btn1.grid(row=0, column=0, padx=10, pady=10)

        btn2 = ctk.CTkButton(self.grid_frame, text="System Info", command=self.show_sys_info)
        btn2.grid(row=0, column=1, padx=10, pady=10)

        btn3 = ctk.CTkButton(self.grid_frame, text="Screenshot", command=lambda: AutomationToolbox.take_screenshot())
        btn3.grid(row=1, column=0, padx=10, pady=10)

        self.output = ctk.CTkTextbox(self, height=200)
        self.output.pack(pady=10, padx=20, fill="x")

    def show_sys_info(self):
        info = SystemToolbox.get_system_info()
        self.output.delete("0.0", "end")
        self.output.insert("0.0", info)

if __name__ == "__main__":
    app = CrytonixApp()
    app.mainloop()
