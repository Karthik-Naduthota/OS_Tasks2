"""
Readers-Writers problem - MONITOR based solution.

Python has no 'monitor' keyword, so the monitor is a class whose every public method
takes the same lock (threading.Lock) and uses condition variables, which is the
textbook equivalent.

Monitor state : active_readers, writing, waiting_writers   (all guarded by self._lock)
Conditions    : can_read, can_write
Policy        : writer preference (a reader waits if a writer is waiting). Writers cannot starve;
                a continuous stream of writers could starve readers - discuss this in the viva.

Run:  python3 rw_monitor.py --readers 4 --writers 2 --rounds 3 --delay 0.3
"""
import argparse
import os
import random
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "common"))
from tracelog import Trace, write_html  # noqa: E402

trace = Trace()


class SharedCounter:
    value = 0


class ReadersWritersMonitor:
    def __init__(self):
        self._lock = threading.Lock()
        self._can_read = threading.Condition(self._lock)
        self._can_write = threading.Condition(self._lock)
        self._active_readers = 0
        self._writing = False
        self._waiting_writers = 0

    def start_read(self, who):
        with self._lock:
            trace.log(who, "state", state="waiting")
            while self._writing or self._waiting_writers > 0:
                self._can_read.wait()
            self._active_readers += 1
            trace.log(who, "state", state="reading")

    def end_read(self, who):
        with self._lock:
            self._active_readers -= 1
            trace.log(who, "state", state="thinking")
            if self._active_readers == 0:
                self._can_write.notify()

    def start_write(self, who):
        with self._lock:
            self._waiting_writers += 1
            trace.log(who, "state", state="waiting")
            while self._writing or self._active_readers > 0:
                self._can_write.wait()
            self._waiting_writers -= 1
            self._writing = True
            trace.log(who, "state", state="writing")

    def end_write(self, who):
        with self._lock:
            self._writing = False
            trace.log(who, "state", state="thinking")
            if self._waiting_writers > 0:
                self._can_write.notify()
            else:
                self._can_read.notify_all()


monitor = ReadersWritersMonitor()


def pause(max_delay):
    time.sleep(random.uniform(0.2, 1.0) * max_delay)


def reader(name, rounds, delay):
    for _ in range(rounds):
        trace.log(name, "state", state="thinking"); pause(delay)
        monitor.start_read(name)
        # ---- critical section (shared read) ----
        trace.log(name, "access", action="read", value=SharedCounter.value)
        pause(delay)
        monitor.end_read(name)
    trace.log(name, "state", state="done")


def writer(name, rounds, delay):
    for _ in range(rounds):
        trace.log(name, "state", state="thinking"); pause(delay)
        monitor.start_write(name)
        # ---- critical section (exclusive write) ----
        tmp = SharedCounter.value
        pause(delay)                       # widens the race window if exclusion were broken
        SharedCounter.value = tmp + 1
        trace.log(name, "access", action="write", value=SharedCounter.value)
        monitor.end_write(name)
    trace.log(name, "state", state="done")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--readers", type=int, default=4)
    ap.add_argument("--writers", type=int, default=2)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "..", "generated_html",
                                                 "readers_writers_monitor.html"))
    a = ap.parse_args()
    random.seed(a.seed)

    threads = [threading.Thread(target=reader, args=(f"R{i+1}", a.rounds, a.delay)) for i in range(a.readers)]
    threads += [threading.Thread(target=writer, args=(f"W{i+1}", a.rounds, a.delay)) for i in range(a.writers)]
    for t in threads: t.start()
    for t in threads: t.join()

    expected = a.writers * a.rounds
    print(f"Final counter = {SharedCounter.value} (expected {expected}) ->",
          "OK, no lost updates" if SharedCounter.value == expected else "RACE CONDITION!")
    names = [f"R{i+1}" for i in range(a.readers)] + [f"W{i+1}" for i in range(a.writers)]
    write_html(a.out, "Readers-Writers (Monitor)", "rw", names, trace)


if __name__ == "__main__":
    main()
