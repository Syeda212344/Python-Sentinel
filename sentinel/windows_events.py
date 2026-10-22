"""Optional REAL Windows event-log collector, separate from the portable demo.

Needs Windows + `pywin32`. Reading Security log may require elevated access.
Polls a bounded recent tail. Not a replacement for a production SIEM.
"""
import os
from pathlib import Path
from .services import now_text


class WindowsCollector:
    def __init__(self, watched_file=None, channels=('Security', 'System', 'Application')):
        if os.name != 'nt':
            raise RuntimeError('Real Windows monitoring requires Microsoft Windows.')
        try:
            import win32evtlog
        except ImportError as exc:
            raise RuntimeError('Install pywin32: py -m pip install pywin32') from exc
        self.win32evtlog = win32evtlog
        self.channels = tuple(channels)
        self.positions = {}
        self.watched_file = Path(watched_file) if watched_file else None
        self.file_mtime = None
        self.warnings = []
        self._prime()

    def _tail(self, channel, max_records=250):
        w = self.win32evtlog
        handle = w.OpenEventLog(None, channel)
        try:
            flags = w.EVENTLOG_BACKWARDS_READ | w.EVENTLOG_SEQUENTIAL_READ
            result = []
            while len(result) < max_records:
                batch = w.ReadEventLog(handle, flags, 0)
                if not batch:
                    break
                result.extend(batch)
            return result[:max_records]
        finally:
            w.CloseEventLog(handle)

    def _prime(self):
        available = []
        for channel in self.channels:
            try:
                records = self._tail(channel, max_records=1)
                self.positions[channel] = int(records[0].RecordNumber) if records else 0
                available.append(channel)
            except Exception as exc:
                self.warnings.append(f'{channel} log inaccessible: {exc}')
        self.channels = tuple(available)
        if not self.channels and not self.watched_file:
            raise RuntimeError('No supported Windows log could be opened. Try administrator access.')
        if self.watched_file:
            try:
                self.file_mtime = self.watched_file.stat().st_mtime_ns
            except OSError as exc:
                self.warnings.append(f'Watched file unavailable: {exc}')

    def poll(self):
        output = []
        for channel in self.channels:
            try:
                records = self._tail(channel)
            except Exception as exc:
                self.warnings.append(f'{channel} read error: {exc}')
                continue
            newest = max((int(r.RecordNumber) for r in records), default=self.positions[channel])
            for r in reversed(records):
                if int(r.RecordNumber) <= self.positions[channel]:
                    continue
                event_code = int(r.EventID) & 0xFFFF
                if channel == 'Security' and event_code == 4625:
                    event_type, severity = 'FAILED_LOGIN', 'Medium'
                elif channel == 'Security' and event_code == 4624:
                    event_type, severity = 'NORMAL_LOGIN', 'Normal'
                else:
                    event_type, severity = f'WINDOWS_EVENT_{event_code}', 'Info'
                inserts = list(r.StringInserts or [])
                username = str(inserts[5]) if channel == 'Security' and event_code in (4624, 4625) and len(inserts) > 5 else None
                try:
                    event_time = r.TimeGenerated.Format()[:19]
                    # pywintypes formats may be non-ISO; normalize them to local receipt time.
                    from datetime import datetime
                    datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    event_time = now_text()
                description = (f'Windows {channel} log event ID {event_code}, source {r.SourceName}. '
                               + ' | '.join(str(s) for s in inserts[:5]))[:1500]
                output.append(dict(event_time=event_time, source=f'Windows {channel} Log',
                                   event_type=event_type, username=username,
                                   message=description, severity=severity))
            self.positions[channel] = newest
        if self.watched_file:
            try:
                stamp = self.watched_file.stat().st_mtime_ns
                if self.file_mtime is not None and stamp != self.file_mtime:
                    output.append(dict(event_time=now_text(), source='Supported File',
                                       event_type='FILE_CHANGE', username=None,
                                       message=f'Monitored file changed: {self.watched_file.name}', severity='Low'))
                self.file_mtime = stamp
            except OSError as exc:
                self.warnings.append(f'File watch error: {exc}')
        return output
