"""
Dining Philosophers (4 philosophers) - SEMAPHORE based solution.

Resources  : 4 forks, each a binary semaphore (init 1). Fork i lies between P(i-1) and P(i);
             philosopher i uses fork i (left) and fork (i+1)%4 (right).
Deadlock   : prevented by a counting semaphore 'room' (init N-1 = 3). At most 3 philosophers
             may try to pick up forks at once, so at least one can always get both forks
             (circular wait is impossible).
Starvation : room and forks are handed out by the OS/Python scheduler, which gives no strict
             FIFO guarantee, so starvation is unlikely but not formally excluded - discuss in viva.

Run:  python3 dp_semaphore.py --meals 3 --delay 0.3
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
forks = [threading.Semaphore(1) for _ in range(N)]
room = threading.Semaphore(N - 1)
meals_eaten = [0] * N


def pause(max_delay):
    time.sleep(random.uniform(0.2, 1.0) * max_delay)


def philosopher(i, meals, delay):
    name = f"P{i}"
    left, right = i, (i + 1) % N
    for _ in range(meals):
        trace.log(name, "state", state="thinking"); pause(delay)

        trace.log(name, "state", state="hungry")
        room.acquire()                        # deadlock prevention: only N-1 may compete
        trace.log(name, "state", state="acquiring")
        forks[left].acquire()
        trace.log(name, "fork", fork=left, owner=i)
        pause(delay / 3)                      # gap that would cause deadlock without 'room'
        forks[right].acquire()
        trace.log(name, "fork", fork=right, owner=i)

        trace.log(name, "state", state="eating")   # ---- critical section ----
        meals_eaten[i] += 1
        pause(delay)

        trace.log(name, "state", state="releasing")
        trace.log(name, "fork", fork=left, owner=None)    # log BEFORE release
        forks[left].release()
        trace.log(name, "fork", fork=right, owner=None)
        forks[right].release()
        room.release()
    trace.log(name, "state", state="done")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meals", type=int, default=3)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "..", "generated_html",
                                                 "dining_philosophers_semaphore.html"))
    a = ap.parse_args()
    random.seed(a.seed)

    threads = [threading.Thread(target=philosopher, args=(i, a.meals, a.delay)) for i in range(N)]
    for t in threads: t.start()
    for t in threads: t.join()

    print("Meals eaten per philosopher:", meals_eaten, "(no deadlock, all finished)")
    write_html(a.out, "Dining Philosophers x4 (Semaphores)", "dp",
               [f"P{i}" for i in range(N)], trace, forks=N)


if __name__ == "__main__":
    main()
