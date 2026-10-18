import json
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

# Connected remotes + USB peripherals, classified as bluetooth / usb_receiver / usb.
_PS_LIST_DEVICES = r"""
$ErrorActionPreference = 'SilentlyContinue'
$results = @()

function Get-BusName($inst) {
    try {
        return (Get-PnpDeviceProperty -InstanceId $inst -KeyName DEVPKEY_Device_BusReportedDeviceDesc).Data
    } catch {
        return $null
    }
}

function Get-Kind($name) {
    if ($name -match 'Receiver|Dongle|Unifying|Wireless|2\.4\s*G|Nano Receiver') {
        return 'usb_receiver'
    }
    return 'usb'
}

Get-PnpDevice -Class Bluetooth |
    Where-Object { $_.InstanceId -like 'BTHENUM\DEV_*' -and $_.Status -eq 'OK' } |
    ForEach-Object {
        $results += [pscustomobject]@{ name = $_.FriendlyName; kind = 'bluetooth' }
    }

Get-PnpDevice -Class USB |
    Where-Object {
        $_.Status -eq 'OK' -and
        $_.InstanceId -like 'USB\VID_*' -and
        $_.FriendlyName -notmatch 'Hub|Host Controller|Root|Bluetooth'
    } |
    ForEach-Object {
        $name = $_.FriendlyName
        if ($name -match '^(USB Composite Device|USB Device|Generic USB Device)$') {
            $bus = Get-BusName $_.InstanceId
            if ($bus) { $name = $bus }
        }
        if ($name -match '^(USB Composite Device|USB Device|Generic USB Device)$') { return }
        $results += [pscustomobject]@{ name = $name; kind = (Get-Kind $name) }
    }

$results | ConvertTo-Json -Compress
"""

_KIND_ORDER = {"bluetooth": 0, "usb_receiver": 1, "usb": 2}
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class DeviceWorker(QThread):
    devices_updated = pyqtSignal(list)

    def __init__(self, poll_ms=8000, parent=None):
        super().__init__(parent)
        self.poll_ms = poll_ms
        self._running = True
        self._proc = None

    def stop(self):
        self._running = False
        proc = self._proc
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass

    def run(self):
        while self._running:
            self.devices_updated.emit(self.list_connected())
            # Sleep in short slices so stop() can exit quickly
            remaining = self.poll_ms
            while self._running and remaining > 0:
                step = min(200, remaining)
                self.msleep(step)
                remaining -= step

    def list_connected(self):
        if not self._running:
            return []
        try:
            self._proc = subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-NoLogo",
                    "-Command",
                    _PS_LIST_DEVICES,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=_CREATE_NO_WINDOW,
            )
            try:
                stdout, _ = self._proc.communicate(timeout=45)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.communicate()
                return []
            finally:
                self._proc = None

            if not stdout or not stdout.strip():
                return []
            return self._parse_devices(stdout)
        except Exception:
            self._proc = None
            return []

    def _parse_devices(self, raw: str):
        raw = raw.strip()
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []

        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            return []

        devices = []
        seen = set()
        for item in data:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            kind = str(item.get("kind") or "usb").strip().lower()
            if not name or kind not in _KIND_ORDER:
                continue
            key = (name.lower(), kind)
            if key in seen:
                continue
            seen.add(key)
            devices.append({"name": name, "kind": kind})

        devices.sort(key=lambda d: (_KIND_ORDER[d["kind"]], d["name"].lower()))
        return devices
