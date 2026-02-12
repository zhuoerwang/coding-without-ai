# Project 7: Task Scheduler

## Level 1: Priority Queue Scheduler

**Implement classes:**

```
class Task:
    # Represents a schedulable task

class Scheduler:
    __init__() -> None
    submit(task: Task) -> str                  # submit task, returns task_id
    run_next() -> Task | None                  # execute highest-priority task
    peek() -> Task | None                      # view next task without executing
    size() -> int                              # number of pending tasks
```

**Requirements:**
- Each task has: `name` (str), `priority` (int, higher = more important), `callback` (callable)
- `submit()` adds task to the queue, returns a unique task_id
- `run_next()` executes the highest-priority task's callback and removes it from the queue
- Ties in priority: use FIFO order (first submitted runs first)
- `run_next()` on empty queue returns `None`
- Tasks can have any integer priority (including negative)

**Test Cases:**
```python
scheduler = Scheduler()
scheduler.submit(Task(name="low", priority=1, callback=lambda: "low"))
scheduler.submit(Task(name="high", priority=10, callback=lambda: "high"))
scheduler.submit(Task(name="med", priority=5, callback=lambda: "med"))

task = scheduler.run_next()
assert task.name == "high"
assert scheduler.size() == 2
```

---

## Level 2: Delayed Execution

**Extend `Scheduler`:**

```
submit(task: Task, delay: float = 0) -> str      # delay in seconds
submit_at(task: Task, run_at: float) -> str       # absolute timestamp
run_ready() -> list[Task]                         # execute all tasks whose time has come
cancel(task_id: str) -> bool                      # cancel a pending task
```

**Requirements:**
- `delay` parameter schedules task to run after N seconds from submission
- `submit_at` schedules task for an absolute time (epoch timestamp)
- `run_ready()` executes all tasks whose scheduled time has passed, in priority order
- Tasks with `delay=0` are immediately ready
- `cancel()` removes a pending task by ID, returns True if found
- Cancelling an already-executed or non-existent task returns False

**Test Cases:**
```python
scheduler = Scheduler()
scheduler.submit(Task(name="now", priority=1, callback=lambda: None))
scheduler.submit(Task(name="later", priority=10, callback=lambda: None), delay=5.0)

ready = scheduler.run_ready()
assert len(ready) == 1
assert ready[0].name == "now"  # "later" not ready yet
```

---

## Level 3: Async Worker Pool

**Extend `Scheduler`:**

```
__init__(num_workers: int = 1) -> None
start() -> None                      # start worker pool
stop() -> None                       # graceful shutdown
submit(task: Task) -> str            # now supports async callbacks
get_result(task_id: str) -> any      # get task result (blocks until done)
get_status(task_id: str) -> str      # "pending", "running", "completed", "failed"
```

**Requirements:**
- Worker pool with `num_workers` concurrent workers
- Workers pull tasks from the priority queue and execute them
- Support both sync and async callbacks
- `get_result()` returns the callback's return value
- `get_status()` tracks task lifecycle: pending -> running -> completed/failed
- `stop()` waits for currently running tasks to finish, then stops
- `stop()` should not execute pending tasks that haven't started

**Test Cases:**
```python
scheduler = Scheduler(num_workers=3)
await scheduler.start()

results = []
async def work(n):
    await asyncio.sleep(0.1)
    return n * 2

ids = [scheduler.submit(Task(name=f"t{i}", priority=1, callback=lambda: work(i))) for i in range(5)]
# Workers process tasks concurrently
await asyncio.sleep(0.5)
for tid in ids:
    assert scheduler.get_status(tid) == "completed"
await scheduler.stop()
```

---

## Level 4: Retry + Dead Letter Queue

**Extend `Scheduler`:**

```
__init__(num_workers: int = 1, max_retries: int = 0, dlq: bool = False)
get_dlq() -> list[Task]              # get all dead-lettered tasks
retry_dlq() -> int                    # retry all DLQ tasks, returns count
```

**Requirements:**
- When a task callback raises an exception, retry up to `max_retries` times
- Exponential backoff between retries: `0.1 * 2^attempt` seconds
- After all retries exhausted, task status becomes "failed"
- If `dlq=True`, failed tasks are moved to a dead letter queue
- `get_dlq()` returns list of tasks that exhausted all retries
- `retry_dlq()` re-submits all DLQ tasks back to the main queue
- Task retry count should be tracked (accessible via task object)

**Test Cases:**
```python
scheduler = Scheduler(num_workers=1, max_retries=3, dlq=True)
await scheduler.start()

attempt_count = 0
def flaky():
    nonlocal attempt_count
    attempt_count += 1
    if attempt_count < 3:
        raise RuntimeError("Temporary failure")
    return "success"

tid = scheduler.submit(Task(name="flaky", priority=1, callback=flaky))
await asyncio.sleep(2)
assert scheduler.get_status(tid) == "completed"
assert attempt_count == 3
await scheduler.stop()
```
