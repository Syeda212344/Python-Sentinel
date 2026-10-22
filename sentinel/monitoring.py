"""Monitoring runtime: simulated controlled events OR supported real Windows logs."""
import logging,os,threading
from .services import process_event,generate_scenario
from .windows_events import WindowsCollector
LOG=logging.getLogger(__name__)

class MonitoringService:
    def __init__(self):
        self.mode='demo' if os.getenv('SENTINEL_PUBLIC_DEMO')=='1' else (
            'windows' if os.getenv('SENTINEL_MODE','demo').lower()=='windows' else 'demo')
        self.active=False
        self.warning=None
        self.error=None
        self._lock=threading.RLock()
        self._stop=threading.Event()
        self._thread=None

    def start(self):
        with self._lock:
            if self.active:return self.status()
            collector=None
            if self.mode=='windows':
                collector=WindowsCollector(watched_file=os.getenv('SENTINEL_WATCH_FILE') or None)
                self.warning=' | '.join(collector.warnings) if collector.warnings else None
            self._stop.clear()
            self.error=None
            self.active=True
            if collector:
                self._thread=threading.Thread(target=self._loop,args=(collector,),daemon=True)
                self._thread.start()
            return self.status()

    def _loop(self,collector):
        while not self._stop.is_set():
            try:
                for e in collector.poll():process_event(e)
                if collector.warnings:self.warning=' | '.join(collector.warnings[-3:])
            except Exception as exc:
                LOG.exception('Recoverable Windows event monitoring error')
                self.error=f'Windows monitoring error: {exc}'
            self._stop.wait(3)

    def stop(self):
        with self._lock:
            self._stop.set()
            self.active=False
            return self.status()

    def status(self):
        return dict(active=self.active,mode=self.mode,warning=self.warning,error=self.error,
                    public_demo=(os.getenv('SENTINEL_PUBLIC_DEMO') == '1'))

    def demo_event(self,kind):
        if self.mode!='demo':raise ValueError('Test scenarios run only in DEMO mode.')
        if not self.active:raise ValueError('Start Monitoring before sending a test event.')
        return generate_scenario(kind)

monitor=MonitoringService()
