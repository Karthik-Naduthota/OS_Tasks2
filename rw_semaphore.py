"""
Readers-Writers problem - SEMAPHORE based solution.

Shared resource   : SharedCounter (many readers may read together, a writer needs exclusive access)
Critical sections : the read section and the write section in reader()/writer()

Semaphores
  mutex       (init 1) : protects the variable read_count
  room_empty  (init 1) : held by "the group of readers" OR by one writer -> excludes readers from writers
  turnstile   (init 1) : a writer holds it while waiting/writing, so new readers queue behind a
                         waiting writer. This prevents writer starvation.

Run:  python3 rw_semaphore.py --readers 4 --writers 2 --rounds 3 --delay 0.3
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


class SharedCounter:
    value = 0


mutex = threading.Semaphore(1)
room_empty = threading.Semaphore(1)
turnstile = threading.Semaphore(1)
read_count = 0
trace = Trace()


def pause(max_delay):
    time.sleep(random.uniform(0.2, 1.0) * max_delay)


def reader(name, rounds, delay):
    global read_count
    for _ in range(rounds):
        trace.log(name, "state", state="thinking"); pause(delay)
        trace.log(name, "state", state="waiting")

        turnstile.acquire()          # pass through (blocked if a writer is waiting)
        turnstile.release()

        mutex.acquire()              # --- entry protocol
        read_count += 1
        if read_count == 1:          # first reader locks writers out
            room_empty.acquire()
        trace.log(name, "state", state="reading")
        mutex.release()

        # ---- critical section (shared read) ----
        trace.log(name, "access", action="read", value=SharedCounter.value)
        pause(delay)

        mutex.acquire()              # --- exit protocol
        read_count -= 1
        trace.log(name, "state", state="thinking")   # logged BEFORE releasing the room
        if read_count == 0:          # last reader lets writers in
            room_empty.release()
        mutex.release()
    trace.log(name, "state", state="done")


def writer(name, rounds, delay):
    for _ in range(rounds):
        trace.log(name, "state", state="thinking"); pause(delay)
        trace.log(name, "state", state="waiting")

        turnstile.acquire()          # block new readers
        room_empty.acquire()         # wait until room is empty
        trace.log(name, "state", state="writing")

        # ---- critical section (exclusive write) ----
        # read-modify-write with a sleep in the middle: this would lose updates
        # immediately if mutual exclusion were broken.
        tmp = SharedCounter.value
        pause(delay)
        SharedCounter.value = tmp + 1
        trace.log(name, "access", action="write", value=SharedCounter.value)

        trace.log(name, "state", state="thinking")   # logged BEFORE releasing
        room_empty.release()
        turnstile.release()
    trace.log(name, "state", state="done")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--readers", type=int, default=4)
    ap.add_argument("--writers", type=int, default=2)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--delay", type=float, default=0.3, help="max delay scale in seconds")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "..", "generated_html",
                                                 "readers_writers_semaphore.html"))
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
    write_html(a.out, "Readers-Writers (Semaphores)", "rw", names, trace)


if __name__ == "__main__":
    main()
