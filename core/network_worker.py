import socket
import time
from PyQt6.QtCore import QThread, pyqtSignal

TARGET_HOSTS = [("8.8.8.8", 53), ("1.1.1.1", 53)]

class NetworkWorker(QThread):
    status_updated = pyqtSignal(bool, float, str)
    
    def run(self):
        import datetime
        while True:
            online, ping = self.check_internet()
            self.status_updated.emit(online, ping, datetime.datetime.now().strftime("%H:%M:%S"))
            self.msleep(1000)

    def check_internet(self):
        start_time = time.time()
        for host, port in TARGET_HOSTS:
            try:
                socket.setdefaulttimeout(2)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((host, port))
                    return True, (time.time() - start_time) * 1000
            except:
                continue
        return False, 999.0
