import atexit
import os
import queue
import signal
import sys
import threading


class Monitor:
    def __init__(self, interval=1.0):
        self.interval = interval
        self._times = {}
        self._files = []
        self.running = False
        self._queue = queue.Queue()
        self.lock = threading.Lock()

        self.thread = threading.Thread(target=self._monitor)
        self.thread.setDaemon(True)

    def _restart(self, path):
        self._queue.put(True)
        prefix = f'monitor (pid={os.getpid()}):'
        print(f'{prefix} Change detected to \'{path}\'.', file=sys.stderr)
        print(f'{prefix} Triggering process restart.', file=sys.stderr)
        os.kill(os.getpid(), signal.SIGINT)

    def _modified(self, path):
        try:
            # If path doesn't denote a file and were previously
            # tracking it, then it has been removed or the file type
            # has changed so force a restart. If not previously
            # tracking the file then we can ignore it as probably
            # pseudo reference such as when file extracted from a
            # collection of modules contained in a zip file.

            if not os.path.isfile(path):
                return path in self._times

            # Check for when file last modified.

            mtime = os.stat(path).st_mtime
            if path not in self._times:
                self._times[path] = mtime

            # Force restart when modification time has changed, even
            # if time now older, as that could indicate older file
            # has been restored.

            if mtime != self._times[path]:
                return True
        except:  # noqa: E722 #pylint: disable=bare-except
            # If any exception occured, likely that file has been
            # been removed just before stat(), so force a restart.
            return True

        return False

    def _monitor(self):
        while 1:
            # Check modification times on all files in sys.modules.

            for module in list(sys.modules.values()):
                path = _get_module_file(module)
                if path and self._modified(path):
                    return self._restart(path)

            # Check modification times on files which have
            # specifically been registered for monitoring.

            for path in self._files:
                if self._modified(path):
                    return self._restart(path)

            # Go to sleep for specified interval.

            try:
                return self._queue.get(timeout=self.interval)
            except:  # noqa: E722 #pylint: disable=bare-except
                pass

    def exiting(self):
        try:
            self._queue.put(True)
        except:  # noqa: E722 #pylint: disable=bare-except
            pass
        self.thread.join()

    def track(self, path):
        if path not in self._files:
            self._files.append(path)


_instance = Monitor()
atexit.register(_instance.exiting)


def _get_module_file(module):
    if hasattr(module, '__file__'):
        path = getattr(module, '__file__')
        if os.path.splitext(path)[1] in ['.pyc', '.pyo', '.pyd']:
            path = path[:-1]
        return path
    return None


def start(interval=1.0):
    if interval < _instance.interval:
        _instance.interval = interval

    with _instance.lock:
        if not _instance.running:
            prefix = f'monitor (pid={os.getpid()}):'
            print(f'{prefix} Starting change monitor.', file=sys.stderr)
            _instance.running = True
            _instance.thread.start()
