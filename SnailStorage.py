import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import os
import sys
import platform

class DarkThemeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SnailStorage - Storage Viewer")
        self.configure(bg="#181818")
        self.geometry("600x400")
        self.style = ttk.Style(self)
        self._set_dark_theme()
        self._create_tabs()

    def _set_dark_theme(self):
        self.style.theme_use('clam')
        self.style.configure('.',
            background='#181818',
            foreground='#f0f0f0',
            fieldbackground='#222222',
            bordercolor='#333333',
            lightcolor='#222222',
            darkcolor='#111111',
            highlightthickness=0
        )
        self.style.configure('TNotebook', background='#181818', borderwidth=0)
        self.style.configure('TNotebook.Tab',
            background='#222222',
            foreground='#f0f0f0',
            lightcolor='#222222',
            borderwidth=0
        )
        self.style.map('TNotebook.Tab',
            background=[('selected', '#333333')],
            foreground=[('selected', '#ffffff')]
        )
        self.style.configure('TCombobox',
            fieldbackground='white',
            background='white',
            foreground='black',
            arrowcolor='black'
        )
        self.style.map('TCombobox',
            fieldbackground=[('readonly', 'white')],
            background=[('readonly', 'white')],
            foreground=[('readonly', 'black')]
        )

    def _create_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.storage_tab = tk.Frame(self.notebook, bg='#181818')
        self.scan_tab = tk.Frame(self.notebook, bg='#181818')
        self.scan_results_tab = tk.Frame(self.notebook, bg='#181818')
        self.extra_options_tab = tk.Frame(self.notebook, bg='#181818')

        self.notebook.add(self.storage_tab, text='Storage Devices')
        self.notebook.add(self.scan_tab, text='Scan Storage Device')
        self.notebook.add(self.scan_results_tab, text='Scan Results')
        self.notebook.add(self.extra_options_tab, text='Extra Options')

        self._populate_storage_devices()
        self._populate_scan_tab()
        self._populate_scan_results_tab()
        self._populate_extra_options_tab()

    def _populate_extra_options_tab(self):
        for widget in self.extra_options_tab.winfo_children():
            widget.destroy()
        admin_btn = ttk.Button(self.extra_options_tab, text="Run Snail Storage As Admin", command=self._run_as_admin)
        admin_btn.pack(pady=20)

    def _run_as_admin(self):
        system = platform.system()
        if system == 'Windows':
            try:
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, '"' + sys.argv[0] + '"', None, 1)
                self.destroy()
                sys.exit()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restart as admin: {e}")
        else:
            messagebox.showinfo("Info", "On Linux/macOS, please restart the program with sudo privileges.")

    def _populate_storage_devices(self):
        for widget in self.storage_tab.winfo_children():
            widget.destroy()
        tk.Label(self.storage_tab, text="Storage Devices:", bg='#181818', fg='#f0f0f0', font=("Arial", 14, "bold")).pack(pady=(10,5))
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total_gb = usage.total / (1024 ** 3)
                used_gb = usage.used / (1024 ** 3)
                percent = usage.percent
                info = f"{part.device} ({part.mountpoint}) - {used_gb:.2f} GB used / {total_gb:.2f} GB ({percent}%)"
            except PermissionError:
                info = f"{part.device} ({part.mountpoint}) - Access Denied"
            tk.Label(self.storage_tab, text=info, bg='#181818', fg='#f0f0f0', anchor='w').pack(fill='x', padx=20, pady=2)

    def _populate_scan_tab(self):
        for widget in self.scan_tab.winfo_children():
            widget.destroy()
        tk.Label(self.scan_tab, text="Pick Storage Device To Scan", bg='#181818', fg='#f0f0f0', font=("Arial", 12)).pack(pady=(20, 5))
        self.devices = [f"{part.device} ({part.mountpoint})" for part in psutil.disk_partitions()]
        self.device_mounts = [part.mountpoint for part in psutil.disk_partitions()]
        self.selected_device = tk.StringVar()
        if self.devices:
            self.selected_device.set(self.devices[0])
        dropdown = ttk.Combobox(self.scan_tab, values=self.devices, textvariable=self.selected_device, state="readonly")
        dropdown.pack(pady=5)
        start_btn = ttk.Button(self.scan_tab, text="Start Scan", command=self._start_scan)
        start_btn.pack(pady=20)

    def _start_scan(self):
        idx = self.devices.index(self.selected_device.get())
        mountpoint = self.device_mounts[idx]
        self.root_scan_path = mountpoint
        self.current_scan_path = mountpoint
        self.scan_results = self._scan_folders(mountpoint)
        self.selected_folder = None
        self._populate_scan_results_tab()
        self.notebook.select(self.scan_results_tab)

    def _scan_folders(self, root_path):
        folder_sizes = []
        for entry in os.scandir(root_path):
            if entry.is_dir(follow_symlinks=False):
                size = self._get_folder_size(entry.path)
                folder_sizes.append({'path': entry.path, 'size': size})
        folder_sizes.sort(key=lambda x: x['size'], reverse=True)
        return folder_sizes

    def _get_folder_size(self, folder):
        total = 0
        for dirpath, dirnames, filenames in os.walk(folder, onerror=lambda e: None):
            for f in filenames:
                try:
                    fp = os.path.join(dirpath, f)
                    if os.path.isfile(fp):
                        total += os.path.getsize(fp)
                        print(f"Scanning: {fp}")
                except Exception:
                    pass
        return total

    def _populate_scan_results_tab(self):
        for widget in self.scan_results_tab.winfo_children():
            widget.destroy()
        if not hasattr(self, 'scan_results') or not self.scan_results:
            tk.Label(self.scan_results_tab, text="No scan results yet.", bg='#181818', fg='#f0f0f0').pack(pady=20)
            return
        container = tk.Frame(self.scan_results_tab, bg='#181818')
        container.pack(fill='both', expand=True)
        left = tk.Frame(container, bg='#181818')
        left.pack(side='left', fill='y', padx=(10,5), pady=10)
        right = tk.Frame(container, bg='#181818')
        right.pack(side='left', fill='both', expand=True, padx=(5,10), pady=10)
        # Back button logic
        if hasattr(self, 'root_scan_path') and hasattr(self, 'current_scan_path') and self.current_scan_path != self.root_scan_path:
            back_btn = ttk.Button(left, text="Back", command=self._back_to_root)
            back_btn.pack(fill='x', pady=(0,10))
        self.folder_buttons = []
        for folder in self.scan_results:
            btn = tk.Button(left, text=f"{os.path.basename(folder['path'])}\n{self._format_size(folder['size'])}", anchor='w', justify='left', bg='#222222', fg='#f0f0f0', relief='flat', command=lambda f=folder: self._show_folder_details(f, right))
            btn.pack(fill='x', pady=2)
            self.folder_buttons.append(btn)
        if self.selected_folder:
            self._show_folder_details(self.selected_folder, right)

    def _show_folder_details(self, folder, right_frame):
        self.selected_folder = folder
        for widget in right_frame.winfo_children():
            widget.destroy()
        tk.Label(right_frame, text=f"Path: {folder['path']}", bg='#181818', fg='#f0f0f0', anchor='w', wraplength=350).pack(anchor='w', pady=(10,5))
        tk.Label(right_frame, text=f"Size: {self._format_size(folder['size'])}", bg='#181818', fg='#f0f0f0', anchor='w').pack(anchor='w', pady=(0,10))
        scan_btn = ttk.Button(right_frame, text="Scan This Folder", command=lambda: self._scan_selected_folder(folder['path']))
        scan_btn.pack(anchor='w', pady=(0,10))
        del_btn = ttk.Button(right_frame, text="Delete", command=lambda: self._delete_folder(folder))
        del_btn.pack(anchor='w', pady=10)

    def _scan_selected_folder(self, folder_path):
        self.current_scan_path = folder_path
        self.scan_results = self._scan_folders(folder_path)
        self.selected_folder = None
        self._populate_scan_results_tab()

    def _back_to_root(self):
        self.current_scan_path = self.root_scan_path
        self.scan_results = self._scan_folders(self.root_scan_path)
        self.selected_folder = None
        self._populate_scan_results_tab()

    def _delete_folder(self, folder):
        if messagebox.askyesno("Delete Folder", f"Are you sure you want to delete this folder?\n{folder['path']}"):
            try:
                import shutil
                shutil.rmtree(folder['path'])
                messagebox.showinfo("Deleted", f"Folder deleted: {folder['path']}")
                self._start_scan()  # Refresh results
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete folder: {e}")

    def _format_size(self, size):
        for unit in ['B','KB','MB','GB','TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

if __name__ == "__main__":
    app = DarkThemeApp()
    app.mainloop() 