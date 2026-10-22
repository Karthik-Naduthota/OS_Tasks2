# OS_Tasks2
# AI-Assisted Synchronization Algorithms with HTML Simulation

## Operating Systems Programming Assignment

This project implements two classical Operating Systems synchronization problems using **Semaphores and Monitors in Python**. It also generates interactive HTML simulations to visualize the execution of threads and synchronization events.

## Problems Implemented

### 1. Readers-Writers Problem

The Readers-Writers problem manages concurrent access to a shared resource.

- **Semaphore implementation:** Uses `mutex`, `room_empty`, and `turnstile` to coordinate readers and writers.
- **Monitor implementation:** Uses a lock and condition variables to control access.
- Multiple readers can read simultaneously.
- Writers get exclusive access to the shared resource.
- The implementation checks the shared counter to detect incorrect updates.

### 2. Dining Philosophers Problem

The Dining Philosophers problem demonstrates resource sharing and deadlock prevention using four philosophers and four forks.

- **Semaphore implementation:** Uses binary semaphores for forks and a counting semaphore to allow at most three philosophers to compete for forks simultaneously.
- **Monitor implementation:** Uses philosopher states and condition variables to allow a philosopher to eat only when both neighbours are not eating.
- Prevents deadlock using the respective synchronization strategies.
- Discusses the possibility of starvation and fairness limitations.

## Technologies Used

- Python 3
- Python `threading` module
- Semaphores, locks, and condition variables
- HTML, CSS, and JavaScript for visualization
- JSON for storing execution events
- Python `webbrowser` module

**Dependencies:** Python standard library only. No additional packages are required.

## Project Structure

```text
.
├── readers_writers/
│   ├── semaphore/
│   │   └── rw_semaphore.py
│   └── monitor/
│       └── rw_monitor.py
├── dining_philosophers/
│   ├── semaphore/
│   │   └── dp_semaphore.py
│   └── monitor/
│       └── dp_monitor.py
├── common/
│   └── tracelog.py
├── generated_html/
└── README.md
```

## How to Run

### Prerequisites

1. Install Python 3.
2. Clone or download this repository.
3. Open a terminal in the repository's root directory.

### 1. Readers-Writers Using Semaphores

```bash
python readers_writers/semaphore/rw_semaphore.py --readers 4 --writers 2 --rounds 3 --delay 0.3
```

### 2. Readers-Writers Using Monitors

```bash
python readers_writers/monitor/rw_monitor.py --readers 4 --writers 2 --rounds 3 --delay 0.3
```

### 3. Dining Philosophers Using Semaphores

```bash
python dining_philosophers/semaphore/dp_semaphore.py --meals 3 --delay 0.3
```

### 4. Dining Philosophers Using Monitors

```bash
python dining_philosophers/monitor/dp_monitor.py --meals 3 --delay 0.3
```

**Note:** Run the commands from the repository's root directory. If you are using Windows, `python` can usually be used in place of `python3`.

## HTML Simulation and Visualization

Each program records execution events and generates a self-contained HTML simulation in the `generated_html/` directory.

The simulation includes:

- Play and Pause controls
- Step-by-step execution
- Reset functionality
- Adjustable playback speed
- Timeline slider
- Visualization of thread and philosopher states
- Visualization of shared resource access and fork ownership
- Violation indicators for synchronization errors

The generated HTML file opens in the default web browser when the program finishes, provided the environment supports opening a browser.

## Synchronization Concepts Demonstrated

- Race conditions
- Mutual exclusion
- Critical sections
- Semaphores
- Monitors
- Locks and condition variables
- Deadlock prevention
- Starvation and fairness
- Concurrent execution and event logging

## Testing

The programs can be tested using different numbers of readers, writers, rounds, meals, and delays.

Expected checks include:

- The final shared counter matches the expected number of successful writes.
- Readers and writers do not access the critical section simultaneously.
- No two neighbouring philosophers eat at the same time.
- All philosophers complete their meals in the tested executions.
- The generated HTML simulations correctly display the recorded events.

Thread scheduling is nondeterministic, so the execution order may vary between runs. Successful test runs do not prove that starvation is impossible.

## Learning Outcomes

This project provides practical experience with:

- Implementing classical synchronization algorithms.
- Comparing semaphore-based and monitor-based solutions.
- Understanding race conditions, deadlock, and starvation.
- Recording concurrent events for debugging.
- Visualizing program execution through HTML simulations.

## References

1. A. B. Downey, *The Little Book of Semaphores*.
2. Abraham Silberschatz, Peter B. Galvin, and Greg Gagne, *Operating System Concepts*.
3. Andrew S. Tanenbaum and Herbert Bos, *Modern Operating Systems*.
4. [Python Threading Documentation](https://docs.python.org/3/library/threading.html)
5. [Python Webbrowser Documentation](https://docs.python.org/3/library/webbrowser.html)

## AI Usage Disclosure

AI assistance was used to support code development, debugging, explanation of synchronization concepts, HTML visualization, and documentation. The code should be reviewed, tested, and understood before submission.

---

**Course:** Operating Systems  
**Programming Language:** Python 3
