"""The machine a test ran on, for the performance results (read-only
queries of this computer; nothing is sent anywhere)."""
import importlib.metadata
import os
import platform
import subprocess
import sys


def _version(package):
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def _cpu_name():
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    return platform.processor() or platform.machine()


def _tesseract():
    try:
        import pytesseract
        import ocr_tesseract
        ocr_tesseract._configure_tesseract()
        return str(pytesseract.get_tesseract_version())
    except Exception:
        return "not available"


def _gpu():
    try:
        import paddle
        return "GPU (CUDA)" if paddle.device.is_compiled_with_cuda() and paddle.device.cuda.device_count() else "CPU only"
    except Exception:
        return "unknown"


def machine_specs(extra=None):
    """[[label, value], ...]"""
    import psutil
    rows = [
        ["Processor", _cpu_name()],
        ["Physical / logical cores", f"{psutil.cpu_count(logical=False)} / {psutil.cpu_count(logical=True)}"],
        ["Memory (RAM)", f"{psutil.virtual_memory().total / 1024 ** 3:.1f} GB"],
        ["Operating system", f"{platform.system()} {platform.release()} ({platform.version()})"],
        ["Python", platform.python_version()],
        ["PaddleOCR / PaddlePaddle", f"{_version('paddleocr')} / {_version('paddlepaddle')}"],
        ["PaddleOCR runs on", _gpu()],
        ["Tesseract", _tesseract()],
        ["OpenCV", _version("opencv-python") if _version("opencv-python") != "not installed"
         else _version("opencv-contrib-python")],
        ["PyMuPDF", _version("PyMuPDF")],
        ["Flask", _version("Flask")],
        ["Power plan / battery", _power()],
    ]
    return rows + (extra or [])


def _power():
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery is None:
            return "mains (no battery)"
        return f"{'plugged in' if battery.power_plugged else 'on battery'}, {battery.percent:.0f}%"
    except Exception:
        return "unknown"
