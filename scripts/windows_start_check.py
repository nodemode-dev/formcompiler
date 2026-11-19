import argparse
import ctypes
import glob
import json
import ntpath
import os
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stage import DEFAULT_ARTIFACTS

INSTALL_LIMIT = 150
WINDOW_LIMIT = 90
AFTER_EXIT_WAIT = 10
STAY_OPEN = 15
EXIT_LIMIT = 30
ENGINE_WAIT = 20
UNINSTALL_LIMIT = 60
BEFORE_UNINSTALL_LIMIT = 255
SHORTEST_WAIT = 5
POLL = 0.5
LOG_LINES = 40
LOG_FILES = 3
LOG_DEPTH = 3
LOG_BYTES = 65536

MODES = ("report", "gate", "off")
HELPER_ENDINGS = ("-engine", "-core", "-server", "-backend", "-host")
HELPER_PREFIX = "fw"
UNINSTALLER_PREFIX = "unins"
WINDOW_PROGRAM = 2
CONSOLE_PROGRAM = 3
SUBSYSTEMS = {WINDOW_PROGRAM: "window", CONSOLE_PROGRAM: "console"}
CONSOLE_CLASSES = ("ConsoleWindowClass", "CASCADIA_HOSTING_WINDOW_CLASS")
CONSOLE_HOSTS = ("conhost.exe", "openconsole.exe")
DIALOG_CLASS = "#32770"
SCRIPT_ERROR_TITLE = "Unhandled exception in script"
DIALOG_TEXT = 4000
DETACHED_PROCESS = 0x00000008
UNINSTALL_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
WEBVIEW2_KEYS = (
    r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
)
REPORT_NAME = "windows-start-check"


def pe_subsystem(data):
    if len(data) < 0x40 or data[:2] != b"MZ":
        return None
    at = struct.unpack_from("<I", data, 0x3C)[0]
    if data[at:at + 4] != b"PE\0\0":
        return None
    optional = at + 24
    if len(data) < optional + 70:
        return None
    if struct.unpack_from("<H", data, optional)[0] not in (0x10B, 0x20B):
        return None
    return struct.unpack_from("<H", data, optional + 68)[0]


def pe_head(path):
    try:
        with open(path, "rb") as handle:
            first = handle.read(64)
            if len(first) < 64:
                return None
            need = struct.unpack_from("<I", first, 0x3C)[0] + 24 + 70
            if not 64 <= need <= 1 << 20:
                return None
            return first + handle.read(need - 64)
    except OSError:
        return None


def subsystem_of(path):
    head = pe_head(path)
    return pe_subsystem(head) if head else None


def subsystem_word(value):
    if value is None:
        return "not a Windows program"
    return SUBSYSTEMS.get(value, f"subsystem {value}")


def program_stem(name):
    lower = name.lower()
    return lower[:-4] if lower.endswith(".exe") and len(lower) > 4 else None


def is_uninstaller(stem):
    return stem.startswith(UNINSTALLER_PREFIX)


def is_helper(stem):
    return stem.endswith(HELPER_ENDINGS) or stem.startswith(HELPER_PREFIX)


def plain_program(name):
    return bool(program_stem(name)) and len(name) <= 128 and not name.startswith(".") \
        and not re.search(r"[/\\:\x00-\x1f\x7f]", name)


def aliases(*texts):
    out = []
    for text in texts:
        lower = (text or "").lower()
        joined = re.sub(r"[^a-z0-9]", "", lower)
        dashed = "-".join(part for part in re.split(r"[^a-z0-9]+", lower) if part)
        for alias in (joined, dashed):
            if alias and alias not in out:
                out.append(alias)
    return out


def choose_program(product, known, declared, names, kind):
    programs = [(name, program_stem(name)) for name in names if program_stem(name)]
    if not programs:
        return None, "the install folder holds no .exe"
    if declared and plain_program(declared):
        for name, stem in programs:
            if name.lower() == declared.lower() and not is_uninstaller(stem) and kind(name) == WINDOW_PROGRAM:
                return name, "named by form-app.json"
    candidates = [(name, stem) for name, stem in programs if not is_uninstaller(stem) and not is_helper(stem)]
    wanted = [product.lower()] + [alias.lower() for alias in known]
    wanted += [f"{word}-desktop" for word in wanted]
    picked = None
    for word in wanted:
        picked = next(((name, stem) for name, stem in candidates if stem == word), None)
        if picked:
            break
    if not picked:
        if not candidates:
            return None, "it holds no program that is not a helper or an uninstaller"
        if len(candidates) > 1:
            return None, f"it holds {', '.join(name for name, _ in candidates)}, and none of them is named for the app"
        picked = candidates[0]
    found = kind(picked[0])
    if found == WINDOW_PROGRAM:
        return picked[0], "named for the app" if picked[1] in wanted else "the only program that is not a helper"
    if found == CONSOLE_PROGRAM:
        return None, f"{picked[0]} is a console program, not the app's window"
    return None, f"{picked[0]} could not be read as a Windows window program"


def pick_installer(paths):
    ordered = sorted(paths, key=lambda path: str(path).lower())
    for kind, ending in (("nsis", "-setup.exe"), ("msi", ".msi")):
        for path in ordered:
            if str(path).lower().endswith(ending):
                return kind, path
    return None, None


def matched_files(artifacts):
    patterns = [p.strip() for p in re.split(r"[\n,]+", artifacts) if p.strip()] or DEFAULT_ARTIFACTS
    found = []
    for pattern in patterns:
        for source in sorted(glob.glob(pattern, recursive=True)):
            path = Path(source)
            if path.is_file() and path.resolve() not in found:
                found.append(path.resolve())
    return found


def install_command(kind, installer, folder, log):
    if kind == "nsis":
        return f'"{installer}" /S /D={folder}'
    return subprocess.list2cmdline(["msiexec", "/i", str(installer), "/qn", "/norestart", "/l*v", str(log), f"INSTALLDIR={folder}"])


def uninstall_command(kind, installer, folder):
    if kind == "nsis":
        return f'"{ntpath.join(str(folder), "uninstall.exe")}" /S _?={folder}'
    return subprocess.list2cmdline(["msiexec", "/x", str(installer), "/qn", "/norestart"])


def under(path, folder):
    if not path or not folder:
        return False
    inner = ntpath.normcase(ntpath.normpath(str(path)))
    outer = ntpath.normcase(ntpath.normpath(str(folder))).rstrip("\\")
    return inner.startswith(outer + "\\")


def tree(snapshot, root):
    children = {}
    for row in snapshot:
        children.setdefault(row["parent"], []).append(row["pid"])
    found, queue = set(), [root]
    while queue:
        pid = queue.pop()
        if pid in found:
            continue
        found.add(pid)
        queue.extend(children.get(pid, []))
    return found & {row["pid"] for row in snapshot}


def app_windows(windows, pids):
    return [w for w in windows if w["pid"] in pids and w["class"] not in CONSOLE_CLASSES and w["class"] != DIALOG_CLASS
            and w["width"] > 0 and w["height"] > 0]


def error_dialogs(windows, pids):
    return [w for w in windows if (w["class"] == DIALOG_CLASS and w["pid"] in pids) or w["title"].strip() == SCRIPT_ERROR_TITLE]


def dialog_text(parts, most=DIALOG_TEXT):
    kept = []
    for part in parts:
        part = part.strip()
        if part and part not in kept:
            kept.append(part)
    return "\n".join(kept)[:most]


def is_engine(name):
    stem = program_stem(name.replace("/", "\\").rsplit("\\", 1)[-1])
    return bool(stem) and stem.endswith(HELPER_ENDINGS) and not is_uninstaller(stem)


def console_windows(windows, pids, before):
    return [w for w in windows if w["class"] in CONSOLE_CLASSES and (w["pid"] in pids or w["hwnd"] not in before)]


def console_hosts(rows):
    return [row for row in rows if row["name"].lower() in CONSOLE_HOSTS]


def process_words(rows):
    return [f"{row['name']} ({row['pid']}, started by {row['parent']})" for row in sorted(rows, key=lambda r: r["pid"])]


def window_words(windows):
    return [f"{w['title'] or '(no title)'} [{w['class']}, {w['width']}x{w['height']}, process {w['pid']}]" for w in windows]


def names_match(display, key, wanted):
    for text in (display, key):
        if re.sub(r"[^a-z0-9]", "", (text or "").lower()) in wanted:
            return True
    return False


def log_folders(env, names, folder, is_dir=os.path.isdir):
    found = []
    for root in (env.get("APPDATA"), env.get("LOCALAPPDATA"), env.get("USERPROFILE")):
        for name in names:
            if root and name:
                candidate = ntpath.join(root, name) if "\\" in root else os.path.join(root, name)
                if candidate not in found and is_dir(candidate):
                    found.append(candidate)
    if folder and is_dir(str(folder)) and str(folder) not in found:
        found.append(str(folder))
    return found


def newest_logs(folders, since, limit=LOG_FILES, depth=LOG_DEPTH):
    found = []
    for folder in folders:
        base = str(folder).rstrip("\\/")
        for current, dirs, files in os.walk(base):
            if current[len(base):].count(os.sep) >= depth:
                dirs[:] = []
            for name in files:
                if name.lower().endswith(".log"):
                    path = os.path.join(current, name)
                    try:
                        changed = os.path.getmtime(path)
                    except OSError:
                        continue
                    if changed >= since and (changed, path) not in found:
                        found.append((changed, path))
    return [path for _, path in sorted(found, reverse=True)[:limit]]


def tail(path, lines=LOG_LINES, most=LOG_BYTES):
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - most))
            text = handle.read().decode("utf-8", "replace")
    except OSError as error:
        return [f"could not be read: {error}"]
    return text.splitlines()[-lines:]


def identifier_from(conf="src-tauri/tauri.conf.json"):
    try:
        return str(json.loads(Path(conf).read_text(encoding="utf-8")).get("identifier", "") or "")
    except (OSError, ValueError, AttributeError):
        return ""


def step(name, passed, seconds, seen, processes=None):
    return {"step": name, "passed": passed, "seconds": round(seconds, 1), "seen": seen, "processes": processes or []}


def result_word(passed):
    return {True: "passed", False: "FAILED", None: "not run"}[passed]


def failed(report):
    return any(row["passed"] is False for row in report["steps"])


def cell(text):
    return str(text).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def markdown(report):
    lines = [
        f"### Windows start check: {report['app']} {report['version']} ({report['platform']})",
        "",
        f"Result: **{'a step failed' if failed(report) else 'every step that ran passed'}**. "
        f"Mode `{report['mode']}`: {'this fails the build' if report['mode'] == 'gate' else 'the build goes on either way'}. "
        f"Installer: `{report['installer'].get('file', 'none')}`. Program started: `{report.get('program') or 'none'}`. "
        f"WebView2 on the runner: {report.get('webview2') or 'not found'}. The whole check took {report['seconds']} s.",
        "",
        "| Step | Result | Seconds | What was seen |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["steps"]:
        lines.append(f"| {cell(row['step'])} | {result_word(row['passed'])} | {row['seconds']} | {cell(row['seen'])} |")
    if report["programs"]:
        lines += ["", "| Program in the install folder | Kind |", "| --- | --- |"]
        for program in report["programs"]:
            lines.append(f"| `{cell(program['name'])}` | {cell(program['kind'])} |")
    listed = [row for row in report["steps"] if row["processes"]]
    if listed:
        lines += ["", "<details><summary>Processes of the app at each step</summary>", ""]
        for row in listed:
            lines.append(f"- {row['step']}: {cell(', '.join(row['processes']))}")
        lines += ["", "</details>"]
    for entry in report.get("dialogs", []):
        lines += ["", f"<details><summary>Error dialog at \"{cell(entry['step'])}\": {cell(entry['title'] or '(no title)')}</summary>", "", "```text"]
        lines += [line.replace("```", "'''") for line in (entry["text"] or "(no text read)").splitlines()]
        lines += ["```", "", "</details>"]
    if report.get("stopped_by_the_check"):
        lines += ["", f"Stopped by the check at the end: {cell(', '.join(report['stopped_by_the_check']))}."]
    for entry in report["log_tails"]:
        lines += ["", f"<details><summary>Last lines of {cell(entry['file'])}</summary>", "", "```text"]
        lines += [line.replace("```", "'''") for line in entry["lines"]]
        lines += ["```", "", "</details>"]
    limits = ", ".join(f"{name} {value} s" for name, value in report["limits"].items())
    lines += ["", f"Time limits: {limits}.", ""]
    return "\n".join(lines)


def write_report(report, out, summary_path=""):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{REPORT_NAME}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    text = markdown(report)
    (out / f"{REPORT_NAME}.md").write_text(text, encoding="utf-8")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    return text


class Desktop:
    def __init__(self):
        from ctypes import wintypes
        self.types = wintypes
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)

        class Entry(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG), ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
            ]

        self.Entry = Entry
        self.Callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.invalid = ctypes.c_void_p(-1).value
        kernel, user = self.kernel, self.user
        kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
        kernel.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(Entry)]
        kernel.Process32FirstW.restype = wintypes.BOOL
        kernel.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(Entry)]
        kernel.Process32NextW.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle.restype = wintypes.BOOL
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
        kernel.TerminateProcess.argtypes = [ctypes.c_void_p, wintypes.UINT]
        kernel.TerminateProcess.restype = wintypes.BOOL
        user.EnumWindows.argtypes = [self.Callback, wintypes.LPARAM]
        user.EnumWindows.restype = wintypes.BOOL
        user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user.GetWindowThreadProcessId.restype = wintypes.DWORD
        user.IsWindowVisible.argtypes = [wintypes.HWND]
        user.IsWindowVisible.restype = wintypes.BOOL
        user.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user.GetClassNameW.restype = ctypes.c_int
        user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user.GetWindowTextW.restype = ctypes.c_int
        user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user.GetWindowRect.restype = wintypes.BOOL
        user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user.PostMessageW.restype = wintypes.BOOL
        user.EnumChildWindows.argtypes = [wintypes.HWND, self.Callback, wintypes.LPARAM]
        user.EnumChildWindows.restype = wintypes.BOOL
        user.SendMessageTimeoutW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, ctypes.c_void_p,
                                             wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
        user.SendMessageTimeoutW.restype = ctypes.c_ssize_t

    def text(self, hwnd):
        held = ctypes.create_unicode_buffer(DIALOG_TEXT)
        if self.user.GetWindowTextW(hwnd, held, DIALOG_TEXT) > 0:
            return held.value
        copied = ctypes.c_size_t(0)
        self.user.SendMessageTimeoutW(hwnd, 0x000D, DIALOG_TEXT, ctypes.cast(held, ctypes.c_void_p), 0x0002, 1000, ctypes.byref(copied))
        return held.value

    def texts(self, hwnd):
        parts = []

        def each(child, _):
            parts.append(self.text(child))
            return True

        self.user.EnumChildWindows(hwnd, self.Callback(each), 0)
        return dialog_text(parts)

    def snapshot(self):
        handle = self.kernel.CreateToolhelp32Snapshot(0x2, 0)
        if not handle or handle == self.invalid:
            return []
        entry = self.Entry()
        entry.dwSize = ctypes.sizeof(self.Entry)
        rows = []
        try:
            more = self.kernel.Process32FirstW(handle, ctypes.byref(entry))
            while more:
                rows.append({"pid": int(entry.th32ProcessID), "parent": int(entry.th32ParentProcessID), "name": entry.szExeFile})
                more = self.kernel.Process32NextW(handle, ctypes.byref(entry))
        finally:
            self.kernel.CloseHandle(handle)
        return rows

    def image(self, pid):
        handle = self.kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return ""
        try:
            size = self.types.DWORD(32768)
            text = ctypes.create_unicode_buffer(size.value)
            return text.value if self.kernel.QueryFullProcessImageNameW(handle, 0, text, ctypes.byref(size)) else ""
        finally:
            self.kernel.CloseHandle(handle)

    def windows(self):
        rows = []

        def each(hwnd, _):
            if self.user.IsWindowVisible(hwnd):
                pid = self.types.DWORD(0)
                self.user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                kind = ctypes.create_unicode_buffer(256)
                self.user.GetClassNameW(hwnd, kind, 256)
                title = ctypes.create_unicode_buffer(512)
                self.user.GetWindowTextW(hwnd, title, 512)
                rect = self.types.RECT()
                self.user.GetWindowRect(hwnd, ctypes.byref(rect))
                rows.append({"hwnd": int(hwnd or 0), "pid": int(pid.value), "class": kind.value, "title": title.value,
                             "width": int(rect.right - rect.left), "height": int(rect.bottom - rect.top)})
            return True

        self.user.EnumWindows(self.Callback(each), 0)
        return rows

    def close(self, hwnd):
        return bool(self.user.PostMessageW(hwnd, 0x0010, 0, 0))

    def stop(self, pid):
        handle = self.kernel.OpenProcess(0x0001, False, pid)
        if not handle:
            return False
        try:
            return bool(self.kernel.TerminateProcess(handle, 1))
        finally:
            self.kernel.CloseHandle(handle)


class Session:
    def __init__(self, desktop, folder, exe_names):
        self.desktop = desktop
        self.folder = str(folder)
        self.exe_names = exe_names
        self.roots = []
        self.children = []
        self.seen = set()
        self.before = {w["hwnd"] for w in desktop.windows()}
        self.consoles = {}
        self.hosts = set()
        self.dialogs = []
        self.asked = set()

    def look(self):
        snapshot = self.desktop.snapshot()
        pids = set()
        for root in self.roots:
            pids |= tree(snapshot, root)
        for row in snapshot:
            key = (row["pid"], row["name"].lower())
            if key in self.seen or (key[1] in self.exe_names and under(self.desktop.image(row["pid"]), self.folder)):
                pids.add(row["pid"])
        rows = [row for row in snapshot if row["pid"] in pids]
        self.seen |= {(row["pid"], row["name"].lower()) for row in rows}
        shown = self.desktop.windows()
        for window in console_windows(shown, pids, self.before):
            self.consoles[window["hwnd"]] = window
        self.hosts |= {row["name"] for row in console_hosts(rows)}
        for window in error_dialogs(shown, pids):
            if window["hwnd"] not in self.asked:
                self.asked.add(window["hwnd"])
                self.dialogs.append({"title": window["title"], "text": self.desktop.texts(window["hwnd"]), "process": window["pid"]})
                self.desktop.close(window["hwnd"])
        return rows, app_windows(shown, pids)

    def dialogs_shown(self):
        shown, self.dialogs = self.dialogs, []
        return shown

    def console_words(self):
        words = []
        if self.consoles:
            words.append("a console window showed: " + "; ".join(window_words(self.consoles.values())))
        if self.hosts:
            words.append(f"console host in the tree, which alone shows nothing: {', '.join(sorted(self.hosts))}")
        self.consoles, self.hosts = {}, set()
        return words

    def start(self, program, limit, alone=False):
        began = time.monotonic()
        if alone:
            child = subprocess.Popen([str(program)], cwd=self.folder, creationflags=DETACHED_PROCESS, close_fds=True)
        else:
            child = subprocess.Popen([str(program)], cwd=self.folder, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.children.append(child)
        self.roots.append(child.pid)
        gone = None
        while True:
            rows, found = self.look()
            now = time.monotonic()
            if child.poll() is not None and gone is None:
                gone = now
            waited_out = now - began >= limit or (gone is not None and now - gone >= AFTER_EXIT_WAIT)
            if found or (alone and self.dialogs) or (gone is not None and not rows) or waited_out:
                return child, rows, found, now - began
            time.sleep(POLL)

    def stay(self, seconds):
        began = time.monotonic()
        while time.monotonic() - began < seconds:
            time.sleep(POLL)
            self.look()
        rows, found = self.look()
        return rows, found, time.monotonic() - began

    def close(self, limit):
        began = time.monotonic()
        asked = set()
        while True:
            rows, found = self.look()
            for window in found:
                if window["hwnd"] not in asked:
                    asked.add(window["hwnd"])
                    self.desktop.close(window["hwnd"])
            if not rows or time.monotonic() - began >= limit:
                return rows, len(asked), time.monotonic() - began
            time.sleep(POLL)

    def stop_all(self):
        rows, _ = self.look()
        stopped = [row for row in rows if self.desktop.stop(row["pid"])]
        if stopped:
            time.sleep(2)
        return stopped


def registry_value(root, key, name, view=0):
    import winreg
    try:
        with winreg.OpenKey(root, key, 0, winreg.KEY_READ | view) as handle:
            return str(winreg.QueryValueEx(handle, name)[0])
    except OSError:
        return ""


def webview2_version():
    import winreg
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for key in WEBVIEW2_KEYS:
            version = registry_value(root, key, "pv")
            if version and version != "0.0.0.0":
                return version
    return ""


def registered_folders(wanted):
    import winreg
    found = []
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(root, UNINSTALL_KEY, 0, winreg.KEY_READ | view) as listing:
                    names = [winreg.EnumKey(listing, index) for index in range(winreg.QueryInfoKey(listing)[0])]
            except OSError:
                continue
            for name in names:
                key = f"{UNINSTALL_KEY}\\{name}"
                if names_match(registry_value(root, key, "DisplayName", view), name, wanted):
                    place = registry_value(root, key, "InstallLocation", view).strip('"')
                    if place and os.path.isdir(place) and place not in found:
                        found.append(place)
    return found


def top_programs(folder):
    try:
        return sorted(name for name in os.listdir(folder) if program_stem(name) and os.path.isfile(os.path.join(folder, name)))
    except OSError:
        return []


def all_programs(folder):
    rows = []
    for current, _, files in os.walk(folder):
        for name in sorted(files):
            if program_stem(name):
                path = os.path.join(current, name)
                value = subsystem_of(path)
                rows.append({"name": os.path.relpath(path, folder), "subsystem": value, "kind": subsystem_word(value)})
    return sorted(rows, key=lambda row: row["name"].lower())


def run_quiet(command, limit):
    began = time.monotonic()
    try:
        done = subprocess.run(command, timeout=limit, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return done.returncode, time.monotonic() - began
    except subprocess.TimeoutExpired:
        return None, time.monotonic() - began
    except OSError as error:
        return str(error), time.monotonic() - began


def dialog_words(dialogs):
    return [f"an error dialog showed and was closed by the check: {d['title'] or '(no title)'}: {d['text'][:300] or '(no text read)'}" for d in dialogs]


def note(report, name, session):
    dialogs = session.dialogs_shown()
    report["dialogs"] += [dict(d, step=name) for d in dialogs]
    return dialogs, dialog_words(dialogs) + session.console_words()


def one_start(session, program, label, report, left):
    steps = report["steps"]
    limit = left(WINDOW_LIMIT)
    name = f"{label} start: a window shows"
    if limit < SHORTEST_WAIT:
        steps.append(step(name, None, 0, "the check's time ran out"))
        return
    child, rows, found, seconds = session.start(program, limit)
    seen = [f"window after {seconds:.1f} s: " + "; ".join(window_words(found))] if found else \
        [f"no window of the app within {limit:.0f} s" if child.poll() is None else
         f"the program left with code {child.poll()} and no window showed" + (f"; still running: {', '.join(process_words(rows))}" if rows else "")]
    dialogs, more = note(report, name, session)
    steps.append(step(name, bool(found) and not dialogs, seconds, ". ".join(seen + more), process_words(rows)))
    name = f"{label} start: stays open"
    if found:
        rows, found, seconds = session.stay(left(STAY_OPEN))
        seen = ["still open: " + "; ".join(window_words(found))] if found else \
            ["the window went away" + ("" if rows else " and no process of the app is left")]
        dialogs, more = note(report, name, session)
        steps.append(step(name, bool(found) and not dialogs, seconds, ". ".join(seen + more), process_words(rows)))
    else:
        steps.append(step(name, None, 0, "no window to watch"))
    name = f"{label} close: nothing is left running"
    limit = max(left(EXIT_LIMIT), SHORTEST_WAIT)
    rows, asked, seconds = session.close(limit)
    seen = [f"asked {asked} window(s) to close; " + (f"still running after {limit:.0f} s: {', '.join(process_words(rows))}" if rows else "no process of the app is left")]
    dialogs, more = note(report, name, session)
    steps.append(step(name, not rows and not dialogs, seconds, ". ".join(seen + more), process_words(rows)))


def engine_outcome(code, rows, found, dialogs, waited):
    if dialogs:
        return False, "it stopped at an error dialog"
    if found:
        return True, "it opened the app: " + "; ".join(window_words(found))
    if code is not None and not rows:
        return True, f"it left with code {code} after {waited:.1f} s and nothing is left running"
    if code is not None:
        return True, f"it left with code {code} and these stayed: {', '.join(process_words(rows))}"
    return True, f"still running after {waited:.1f} s with no window: {', '.join(process_words(rows))}"


def engines_alone(desktop, folder, report, exe_names, left):
    steps = report["steps"]
    engines = [row["name"] for row in report["programs"] if is_engine(row["name"])]
    if not engines:
        steps.append(step("the engine alone", None, 0, "no helper program in the install folder"))
    for engine in engines:
        name = f"the engine alone: {engine}"
        limit = left(ENGINE_WAIT)
        if limit < SHORTEST_WAIT:
            steps.append(step(name, None, 0, "the check's time ran out"))
            continue
        session = Session(desktop, folder, exe_names)
        try:
            child, rows, found, seconds = session.start(folder / engine, limit, alone=True)
            dialogs, more = note(report, name, session)
            passed, seen = engine_outcome(child.poll(), rows, found, dialogs, seconds)
            steps.append(step(name, passed, seconds, ". ".join([seen] + more), process_words(rows)))
        finally:
            stopped = process_words(session.stop_all())
            report["stopped_by_the_check"] += stopped
            report["dialogs"] += [dict(d, step=name) for d in session.dialogs_shown()]


def check(args, report):
    steps = report["steps"]
    began = time.monotonic()
    left = lambda limit: max(0.0, min(limit, began + BEFORE_UNINSTALL_LIMIT - time.monotonic()))
    work = Path(args.work).resolve()
    folder = work / "app"
    known = aliases(args.app, args.title)
    report["webview2"] = webview2_version()

    files = matched_files(args.artifacts)
    kind, installer = pick_installer(files)
    if not installer:
        steps.append(step("installer found", False, 0, f"no -setup.exe or .msi among {len(files)} built file(s): {', '.join(path.name for path in files) or 'none'}"))
        return
    report["installer"] = {"kind": kind, "file": installer.name}
    steps.append(step("installer found", True, 0, f"{installer.name} ({kind})"))

    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    code, seconds = run_quiet(install_command(kind, installer, folder, work / "install.log"), INSTALL_LIMIT)
    chosen = True
    if not top_programs(folder):
        elsewhere = [place for place in registered_folders(set(known)) if top_programs(place)]
        if elsewhere:
            folder, chosen = Path(elsewhere[0]), False
    report["folder"] = str(folder)
    report["programs"] = all_programs(folder) if folder.is_dir() else []
    installed = code == 0 and bool(top_programs(folder))
    steps.append(step("install", installed, seconds, f"the installer {'did not finish in ' + str(INSTALL_LIMIT) + ' s' if code is None else 'ended with ' + str(code)}; "
                      f"{len(report['programs'])} program(s) in {folder}{'' if chosen else ' (where the installer put it, not the folder asked for)'}"))
    if kind == "msi" and not installed and (work / "install.log").is_file():
        report["log_tails"].append({"file": "install.log", "lines": tail(work / "install.log")})

    try:
        if top_programs(folder):
            declared = None
            try:
                declared = json.loads((folder / "form-app.json").read_text(encoding="utf-8")).get("launch", {}).get("windows")
            except (OSError, ValueError, AttributeError):
                pass
            name, why = choose_program(args.app, known, declared, top_programs(folder), lambda n: subsystem_of(folder / n))
            report["program"] = name
            steps.append(step("the program to start", bool(name), 0, f"{name}: {why}" if name else why))
            desktop = Desktop()
            exe_names = {row["name"].replace("/", "\\").rsplit("\\", 1)[-1].lower() for row in report["programs"]}
            if name:
                session = Session(desktop, folder, exe_names)
                try:
                    one_start(session, folder / name, "first", report, left)
                    one_start(session, folder / name, "second", report, left)
                finally:
                    report["stopped_by_the_check"] += process_words(session.stop_all())
            engines_alone(desktop, folder, report, exe_names, left)
        if failed(report):
            names = known + [identifier_from()]
            for path in newest_logs(log_folders(os.environ, names, folder), report["started"]):
                report["log_tails"].append({"file": path, "lines": tail(path)})
    finally:
        if top_programs(folder) and (kind == "msi" or (folder / "uninstall.exe").is_file()):
            code, seconds = run_quiet(uninstall_command(kind, installer, folder), UNINSTALL_LIMIT)
            if chosen:
                shutil.rmtree(folder, ignore_errors=True)
            steps.append(step("uninstall", code == 0, seconds, f"the uninstaller {'did not finish in ' + str(UNINSTALL_LIMIT) + ' s' if code is None else 'ended with ' + str(code)}"))
        elif chosen and folder.is_dir():
            shutil.rmtree(folder, ignore_errors=True)
            steps.append(step("uninstall", None, 0, "no uninstaller in the install folder; the folder was removed"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--version", default="")
    parser.add_argument("--platform", default="")
    parser.add_argument("--mode", default="report")
    parser.add_argument("--artifacts", default="")
    parser.add_argument("--out", default="formcompiler-start-check")
    parser.add_argument("--work", default=os.path.join(os.environ.get("RUNNER_TEMP", "."), "formcompiler-start-check"))
    args = parser.parse_args()
    if args.mode not in MODES:
        print(f"::error::windows start check mode {args.mode!r} must be one of {', '.join(MODES)}")
        sys.exit(1)
    if args.mode == "off":
        print("formcompiler: the Windows start check is off for this app")
        return
    if os.name != "nt":
        print("formcompiler: the Windows start check runs on Windows only")
        return

    began = time.monotonic()
    report = {
        "format": "formcompiler-windows-start-check", "format_version": 1, "app": args.app, "version": args.version,
        "platform": args.platform, "mode": args.mode, "started": time.time(), "installer": {}, "folder": "",
        "program": None, "webview2": "", "programs": [], "steps": [], "dialogs": [], "log_tails": [], "stopped_by_the_check": [],
        "limits": {"install": INSTALL_LIMIT, "window": WINDOW_LIMIT, "stay open": STAY_OPEN, "exit": EXIT_LIMIT,
                   "engine alone": ENGINE_WAIT, "uninstall": UNINSTALL_LIMIT, "everything before the uninstall": BEFORE_UNINSTALL_LIMIT},
    }
    try:
        check(args, report)
    except Exception as error:
        report["steps"].append(step("the check itself", False, 0, f"{type(error).__name__}: {error}"))
    report["seconds"] = round(time.monotonic() - began, 1)
    report["result"] = "failed" if failed(report) else "passed"
    print(write_report(report, args.out, os.environ.get("GITHUB_STEP_SUMMARY", "")))
    if failed(report):
        which = ", ".join(row["step"] for row in report["steps"] if row["passed"] is False)
        print(f"::{'error' if args.mode == 'gate' else 'warning'} title=Windows start check::{args.app} on {args.platform}: {which}")
        if args.mode == "gate":
            sys.exit(1)


if __name__ == "__main__":
    main()
