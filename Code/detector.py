import threading
import logging
import numpy as np

class DetectionPlugin:
    """Base class for detection plugins."""
    def analyze(self, stats):
        """Return a list of anomalies detected."""
        return []

class AdaptiveThresholdPlugin(DetectionPlugin):
    """Rilevamento basato su soglie adattive (media mobile, dev. std)."""
    def __init__(self, window=10, std_factor=3):
        self.window = window
        self.std_factor = std_factor
        self.history = {}

    def analyze(self, stats):
        anomalies = []
        for key, value in stats.items():
            throughput = value.get('throughput', 0)
            hist = self.history.setdefault(key, [])
            hist.append(throughput)
            if len(hist) > self.window:
                hist.pop(0)
            if len(hist) >= self.window:
                mean = np.mean(hist)
                std = np.std(hist)
                if throughput > mean + self.std_factor * std:
                    anomalies.append({'key': key, 'throughput': throughput, 'mean': mean, 'std': std})
        return anomalies

class Detector:
    def __init__(self, controller, interval=2):
        self.controller = controller
        self.plugins = []
        self.lock = threading.Lock()
        self.logger = logging.getLogger("Detector")
        self.plugins.append(AdaptiveThresholdPlugin())
        self.running = True
        self.interval = interval
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def add_plugin(self, plugin):
        with self.lock:
            self.plugins.append(plugin)

    def analyze_stats(self, stats):
        anomalies = []
        with self.lock:
            for plugin in self.plugins:
                anomalies.extend(plugin.analyze(stats))
        if anomalies:
            self.logger.info(f"Anomalie rilevate: {anomalies}")
            self.notify_anomalies(anomalies)
        return anomalies

    def run(self):
        while self.running:
            stats = self.controller.monitor.get_stats()
            self.analyze_stats(stats['macs'])
            self.analyze_stats(stats['protocols'])
            self.analyze_stats(stats['ports'])
            # Puoi aggiungere altre analisi granulari qui
            import time
            time.sleep(self.interval)

    def stop(self):
        self.running = False

    def notify_anomalies(self, anomalies):
        # Notifica le anomalie al controller o mitigator
        # Puoi implementare una callback, una coda, o chiamare direttamente il mitigator
        if hasattr(self.controller, 'mitigator'):
            for anomaly in anomalies:
                self.controller.mitigator.handle_anomaly(anomaly)