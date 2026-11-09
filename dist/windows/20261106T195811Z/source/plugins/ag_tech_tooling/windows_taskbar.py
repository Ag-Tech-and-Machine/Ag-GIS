# SPDX-License-Identifier: GPL-2.0-or-later
"""Windows shell identity for our window and shortcut, without patching the host EXE."""
import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path
import re
import subprocess
import uuid


class GUID(C.Structure):
    _fields_ = [("data", C.c_ubyte * 16)]

    @classmethod
    def parse(cls, text):
        result = cls()
        result.data[:] = uuid.UUID(text).bytes_le
        return result


class PropertyKey(C.Structure):
    _fields_ = [("fmtid", GUID), ("pid", W.DWORD)]


class Blob(C.Structure):
    _fields_ = [("size", W.ULONG), ("data", C.c_void_p)]


class VariantValue(C.Union):
    _fields_ = [("text", C.c_wchar_p), ("number", C.c_longlong), ("blob", Blob)]


class PropVariant(C.Structure):
    _anonymous_ = ("value",)
    _fields_ = [("vt", W.USHORT), ("reserved1", W.USHORT),
                ("reserved2", W.USHORT), ("reserved3", W.USHORT), ("value", VariantValue)]


PROPERTY_SET = GUID.parse("9f4c2855-9f79-4b39-a8d0-e1d42de1d5f3")
STORE_IID = GUID.parse("886d8eeb-8cf2-4446-8d02-cdba1dbdcf99")
COMMAND, ICON, NAME, APP_ID = 2, 3, 4, 5


def application_id(profile):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", profile):
        raise ValueError("Unsupported profile name for Windows identity")
    return "AgTechAndMachine.AgGIS" + ("." + profile if profile != "default" else "")


def _check(result):
    if result < 0:
        raise OSError(result, "Windows taskbar property operation failed")


class PropertyStore:
    def __init__(self, hwnd=None, shortcut=None):
        if os.name != "nt":
            raise OSError("Windows shell properties require Windows")
        self.pointer = C.c_void_p()
        self.shell = C.WinDLL("shell32")
        self.ole = C.WinDLL("ole32")
        self.ole.CoInitializeEx.argtypes = [C.c_void_p, W.DWORD]
        self.ole.CoInitializeEx.restype = C.c_long
        self.initialized = self.ole.CoInitializeEx(None, 2) in (0, 1)
        try:
            if shortcut is None:
                method = self.shell.SHGetPropertyStoreForWindow
                method.argtypes = [W.HWND, C.POINTER(GUID), C.POINTER(C.c_void_p)]
                method.restype = C.c_long
                _check(method(hwnd, C.byref(STORE_IID), C.byref(self.pointer)))
            else:
                method = self.shell.SHGetPropertyStoreFromParsingName
                method.argtypes = [W.LPCWSTR, C.c_void_p, W.DWORD, C.POINTER(GUID), C.POINTER(C.c_void_p)]
                method.restype = C.c_long
                _check(method(str(shortcut), None, 2, C.byref(STORE_IID), C.byref(self.pointer)))
        except Exception:
            self.close()
            raise

    def _call(self, index, *arguments):
        types = [C.c_void_p] + [C.POINTER(type(value)) for value in arguments]
        method = C.WINFUNCTYPE(C.c_long, *types)(C.cast(self.pointer, C.POINTER(C.POINTER(C.c_void_p))).contents[index])
        return method(self.pointer, *(C.byref(value) for value in arguments))

    def get(self, pid):
        result = PropVariant()
        _check(self._call(5, PropertyKey(PROPERTY_SET, pid), result))
        return result

    def read(self, pid):
        value = self.get(pid)
        try:
            return value.text if value.vt == 31 else None
        finally:
            self.clear(value)

    def set(self, pid, value):
        _check(self._call(6, PropertyKey(PROPERTY_SET, pid), value))

    def write(self, pid, text):
        value = PropVariant()
        if text is not None:
            value.vt = 31
            value.text = text
        self.set(pid, value)  # IPropertyStore copies the caller-owned string.

    def clear(self, value):
        self.ole.PropVariantClear.argtypes = [C.POINTER(PropVariant)]
        self.ole.PropVariantClear.restype = C.c_long
        _check(self.ole.PropVariantClear(C.byref(value)))

    def commit(self):
        _check(self._call(7))

    def close(self):
        if self.pointer:
            self._call(2)
            self.pointer = C.c_void_p()
        if self.initialized:
            self.ole.CoUninitialize()
            self.initialized = False


class TaskbarIdentity:
    def __init__(self, hwnd, profile, icon=None, launcher=None):
        self.store = PropertyStore(hwnd=hwnd)
        self.previous = {}
        self.owned = {}
        try:
            icon = Path(icon or Path(__file__).with_name("app_icon.ico")).resolve()
            if not icon.is_file():
                raise OSError("Missing Windows product icon")
            launcher = Path(launcher or Path(os.environ["LOCALAPPDATA"]) / "Ag-GIS" / profile / "Ag-GIS.exe")
            properties = {ICON: str(icon) + ",0", APP_ID: application_id(profile)}
            if launcher.is_file():
                properties = {COMMAND: subprocess.list2cmdline([str(launcher)]), ICON: properties[ICON],
                              NAME: "Ag-GIS", APP_ID: properties[APP_ID]}
            for pid, text in properties.items():
                self.previous[pid] = self.store.get(pid)
                self.store.write(pid, text)
                self.owned[pid] = text
        except Exception:
            self.close()
            raise

    def close(self):
        if self.store is None:
            return
        try:
            # Restore the identity first, then relaunch metadata. Retain later owners' values.
            for pid in reversed(self.owned):
                if self.store.read(pid) == self.owned[pid]:
                    self.store.set(pid, self.previous[pid])
        finally:
            for value in self.previous.values():
                self.store.clear(value)
            self.store.close()
            self.store = None


def set_shortcut_identity(path, profile="default"):
    store = PropertyStore(shortcut=path)
    try:
        store.write(APP_ID, application_id(profile))
        store.commit()
    finally:
        store.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--shortcut", type=Path, required=True)
    parser.add_argument("--profile", default="default")
    args = parser.parse_args()
    set_shortcut_identity(args.shortcut, args.profile)
