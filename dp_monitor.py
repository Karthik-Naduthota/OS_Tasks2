"""
Dining Philosophers (4 philosophers) - MONITOR based solution.

Monitor state : state[i] in {thinking, hungry, eating}, one condition variable per philosopher.
Rule          : a hungry philosopher may start eating only if BOTH neighbours are not eating;
                then both forks are taken together, atomically, inside the monitor.
Deadlock      : impossible, because no philosopher ever holds one fork while waiting for the other
                (no "hold and wait").
Starvation    : possible in theory (two neighbours could keep alternating and starve the one
                between them). Mention this in the viva.

Run:  python3 dp_monitor.py --meals 3 --delay 0.3
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

N = 4
trace = Trace()


class DiningMonitor:
    def __init__(self):
        self._lock = threading.Lock()
        self._state = ["thinking"] * N
        self._can_eat = [threading.Condition(self._lock) for _ in range(N)]

    def _left(self, i):  return (i - 1) % N
    def _right(self, i): return (i + 1) % N

    def _try_to_eat(self, i):
        """Caller must hold the monitor lock."""
        if (self._state[i] == "hungry"
                and self._state[self._left(i)] != "eating"
                and self._state[self._right(i)] != "eating"):
            self._state[i] = "eating"
            trace.log(f"P{i}", "state", state="acquiring")
            trace.log(f"P{i}", "fork", fork=i, owner=i)             # left fork
            trace.log(f"P{i}", "fork", fork=(i + 1) % N, owner=i)   # right fork
            trace.log(f"P{i}", "state", state="eating")
            self._can_eat[i].notify()

    def pickup(self, i):
        with self._lock:
            self._state[i] = "hungry"
            trace.log(f"P{i}", "state", state="hungry")
            self._try_to_eat(i)
            while self._state[i] != "eating":
                self._can_eat[i].wait()

    def putdown(self, i):
        with self._lock:
            trace.log(f"P{i}", "state", state="releasing")
            trace.log(f"P{i}", "fork", fork=i, owner=None)
            trace.log(f"P{i}", "fork", fork=(i + 1) % N, owner=None)
            self._state[i] = "thinking"
            trace.log(f"P{i}", "state", state="thinking")
            self._try_to_eat(self._left(i))     # a neighbour may now be able to eat
            self._try_to_eat(self._right(i))


monitor = DiningMonitor()
meals_eaten = [0] * N


def pause(max_delay):
    time.sleep(random.uniform(0.2, 1.0) * max_delay)


def philosopher(i, meals, delay):
    for _ in range(meals):
        pause(delay)                 # thinking
        monitor.pickup(i)
        meals_eaten[i] += 1          # ---- critical section: eating ----
        pause(delay)
        monitor.putdown(i)
    trace.log(f"P{i}", "state", state="done")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meals", type=int, default=3)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "..", "generated_html",
                                                 "dining_philosophers_monitor.html"))
    a = ap.parse_args()
    random.seed(a.seed)

    threads = [threading.Thread(target=philosopher, args=(i, a.meals, a.delay)) for i in range(N)]
    for t in threads: t.start()
    for t in threads: t.join()

    print("Meals eaten per philosopher:", meals_eaten, "(no deadlock, all finished)")
    write_html(a.out, "Dining Philosophers x4 (Monitor)", "dp",
               [f"P{i}" for i in range(N)], trace, forks=N)


if __name__ == "__main__":
    main()
