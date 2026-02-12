"""
Tests for Task Scheduler (Project 7)
Run: pytest test_scheduler.py -k "TestLevel1" -v
"""

import asyncio
import time

import pytest

from scheduler import Task, Scheduler


# ============================================================
# Level 1: Priority Queue Scheduler
# ============================================================

class TestLevel1:
    def test_submit_and_run(self):
        scheduler = Scheduler()
        scheduler.submit(Task(name="task1", priority=1, callback=lambda: "done"))
        task = scheduler.run_next()
        assert task.name == "task1"

    def test_priority_ordering(self):
        scheduler = Scheduler()
        scheduler.submit(Task(name="low", priority=1, callback=lambda: None))
        scheduler.submit(Task(name="high", priority=10, callback=lambda: None))
        scheduler.submit(Task(name="med", priority=5, callback=lambda: None))
        assert scheduler.run_next().name == "high"
        assert scheduler.run_next().name == "med"
        assert scheduler.run_next().name == "low"

    def test_fifo_on_same_priority(self):
        scheduler = Scheduler()
        scheduler.submit(Task(name="first", priority=5, callback=lambda: None))
        scheduler.submit(Task(name="second", priority=5, callback=lambda: None))
        scheduler.submit(Task(name="third", priority=5, callback=lambda: None))
        assert scheduler.run_next().name == "first"
        assert scheduler.run_next().name == "second"
        assert scheduler.run_next().name == "third"

    def test_run_next_empty_returns_none(self):
        scheduler = Scheduler()
        assert scheduler.run_next() is None

    def test_size(self):
        scheduler = Scheduler()
        assert scheduler.size() == 0
        scheduler.submit(Task(name="a", priority=1, callback=lambda: None))
        scheduler.submit(Task(name="b", priority=2, callback=lambda: None))
        assert scheduler.size() == 2
        scheduler.run_next()
        assert scheduler.size() == 1

    def test_peek(self):
        scheduler = Scheduler()
        scheduler.submit(Task(name="a", priority=1, callback=lambda: None))
        scheduler.submit(Task(name="b", priority=10, callback=lambda: None))
        peeked = scheduler.peek()
        assert peeked.name == "b"
        assert scheduler.size() == 2  # peek doesn't remove

    def test_peek_empty_returns_none(self):
        scheduler = Scheduler()
        assert scheduler.peek() is None

    def test_submit_returns_task_id(self):
        scheduler = Scheduler()
        tid = scheduler.submit(Task(name="a", priority=1, callback=lambda: None))
        assert isinstance(tid, str)
        assert len(tid) > 0

    def test_unique_task_ids(self):
        scheduler = Scheduler()
        ids = set()
        for i in range(100):
            tid = scheduler.submit(Task(name=f"t{i}", priority=1, callback=lambda: None))
            ids.add(tid)
        assert len(ids) == 100

    def test_negative_priority(self):
        scheduler = Scheduler()
        scheduler.submit(Task(name="neg", priority=-5, callback=lambda: None))
        scheduler.submit(Task(name="zero", priority=0, callback=lambda: None))
        assert scheduler.run_next().name == "zero"
        assert scheduler.run_next().name == "neg"

    def test_callback_is_executed(self):
        results = []
        scheduler = Scheduler()
        scheduler.submit(Task(name="a", priority=1, callback=lambda: results.append("ran")))
        scheduler.run_next()
        assert results == ["ran"]


# ============================================================
# Level 2: Delayed Execution
# ============================================================

class TestLevel2:
    def test_immediate_task_is_ready(self):
        scheduler = Scheduler()
        scheduler.submit(Task(name="now", priority=1, callback=lambda: None))
        ready = scheduler.run_ready()
        assert len(ready) == 1
        assert ready[0].name == "now"

    def test_delayed_task_not_ready(self):
        scheduler = Scheduler()
        scheduler.submit(
            Task(name="later", priority=1, callback=lambda: None),
            delay=10.0,
        )
        ready = scheduler.run_ready()
        assert len(ready) == 0

    def test_delayed_task_becomes_ready(self):
        scheduler = Scheduler()
        scheduler.submit(
            Task(name="soon", priority=1, callback=lambda: None),
            delay=0.1,
        )
        ready = scheduler.run_ready()
        assert len(ready) == 0
        time.sleep(0.15)
        ready = scheduler.run_ready()
        assert len(ready) == 1
        assert ready[0].name == "soon"

    def test_submit_at_absolute_time(self):
        scheduler = Scheduler()
        scheduler.submit_at(
            Task(name="future", priority=1, callback=lambda: None),
            run_at=time.time() + 0.1,
        )
        ready = scheduler.run_ready()
        assert len(ready) == 0
        time.sleep(0.15)
        ready = scheduler.run_ready()
        assert len(ready) == 1

    def test_ready_tasks_ordered_by_priority(self):
        scheduler = Scheduler()
        scheduler.submit(Task(name="low", priority=1, callback=lambda: None))
        scheduler.submit(Task(name="high", priority=10, callback=lambda: None))
        ready = scheduler.run_ready()
        assert ready[0].name == "high"
        assert ready[1].name == "low"

    def test_cancel_pending_task(self):
        scheduler = Scheduler()
        tid = scheduler.submit(
            Task(name="cancel_me", priority=1, callback=lambda: None),
            delay=10.0,
        )
        assert scheduler.cancel(tid) is True
        assert scheduler.size() == 0

    def test_cancel_nonexistent_returns_false(self):
        scheduler = Scheduler()
        assert scheduler.cancel("no-such-id") is False

    def test_cancel_already_executed_returns_false(self):
        scheduler = Scheduler()
        tid = scheduler.submit(Task(name="done", priority=1, callback=lambda: None))
        scheduler.run_next()
        assert scheduler.cancel(tid) is False

    def test_mix_delayed_and_immediate(self):
        scheduler = Scheduler()
        scheduler.submit(Task(name="now1", priority=1, callback=lambda: None))
        scheduler.submit(Task(name="now2", priority=2, callback=lambda: None))
        scheduler.submit(
            Task(name="later", priority=100, callback=lambda: None),
            delay=10.0,
        )
        ready = scheduler.run_ready()
        assert len(ready) == 2
        assert ready[0].name == "now2"


# ============================================================
# Level 3: Async Worker Pool
# ============================================================

class TestLevel3:
    @pytest.mark.asyncio
    async def test_basic_worker_execution(self):
        scheduler = Scheduler(num_workers=2)
        await scheduler.start()

        results = []

        def work():
            results.append("done")
            return "ok"

        tid = scheduler.submit(Task(name="t1", priority=1, callback=work))
        await asyncio.sleep(0.2)
        assert scheduler.get_status(tid) == "completed"
        assert results == ["done"]
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_async_callback(self):
        scheduler = Scheduler(num_workers=1)
        await scheduler.start()

        async def async_work():
            await asyncio.sleep(0.05)
            return 42

        tid = scheduler.submit(Task(name="async_t", priority=1, callback=async_work))
        await asyncio.sleep(0.3)
        assert scheduler.get_status(tid) == "completed"
        assert scheduler.get_result(tid) == 42
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_concurrent_workers(self):
        scheduler = Scheduler(num_workers=3)
        await scheduler.start()

        start_times = []

        async def slow_work():
            start_times.append(time.time())
            await asyncio.sleep(0.2)
            return "ok"

        for i in range(3):
            scheduler.submit(Task(name=f"t{i}", priority=1, callback=slow_work))

        await asyncio.sleep(0.5)

        # All 3 should have started at roughly the same time
        assert len(start_times) == 3
        span = max(start_times) - min(start_times)
        assert span < 0.1, f"Workers didn't start concurrently: span={span:.3f}s"
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_task_status_lifecycle(self):
        scheduler = Scheduler(num_workers=1)
        await scheduler.start()

        async def slow():
            await asyncio.sleep(0.3)
            return "ok"

        tid = scheduler.submit(Task(name="lifecycle", priority=1, callback=slow))
        assert scheduler.get_status(tid) in ("pending", "running")
        await asyncio.sleep(0.5)
        assert scheduler.get_status(tid) == "completed"
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_failed_task_status(self):
        scheduler = Scheduler(num_workers=1)
        await scheduler.start()

        def fail():
            raise RuntimeError("oops")

        tid = scheduler.submit(Task(name="fail", priority=1, callback=fail))
        await asyncio.sleep(0.2)
        assert scheduler.get_status(tid) == "failed"
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_waits_for_running(self):
        scheduler = Scheduler(num_workers=1)
        await scheduler.start()

        completed = []

        async def slow():
            await asyncio.sleep(0.2)
            completed.append(True)

        scheduler.submit(Task(name="running", priority=1, callback=slow))
        await asyncio.sleep(0.05)  # let it start
        await scheduler.stop()
        assert len(completed) == 1  # should have finished before stop returned

    @pytest.mark.asyncio
    async def test_priority_ordering_in_workers(self):
        scheduler = Scheduler(num_workers=1)
        await scheduler.start()

        order = []

        async def record(name):
            order.append(name)
            await asyncio.sleep(0.05)

        # Submit in wrong order; single worker processes by priority
        scheduler.submit(Task(name="low", priority=1, callback=lambda: record("low")))
        scheduler.submit(Task(name="high", priority=10, callback=lambda: record("high")))
        scheduler.submit(Task(name="med", priority=5, callback=lambda: record("med")))

        await asyncio.sleep(0.5)
        assert order[0] == "high"
        await scheduler.stop()


# ============================================================
# Level 4: Retry + Dead Letter Queue
# ============================================================

class TestLevel4:
    @pytest.mark.asyncio
    async def test_retry_succeeds_eventually(self):
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

    @pytest.mark.asyncio
    async def test_exhausted_retries_goes_to_dlq(self):
        scheduler = Scheduler(num_workers=1, max_retries=2, dlq=True)
        await scheduler.start()

        def always_fail():
            raise RuntimeError("Always fails")

        tid = scheduler.submit(Task(name="doomed", priority=1, callback=always_fail))
        await asyncio.sleep(2)
        assert scheduler.get_status(tid) == "failed"

        dlq = scheduler.get_dlq()
        assert len(dlq) == 1
        assert dlq[0].name == "doomed"
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_retry_dlq_resubmits(self):
        scheduler = Scheduler(num_workers=1, max_retries=0, dlq=True)
        await scheduler.start()

        call_count = 0

        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                raise RuntimeError("First run fails")
            return "ok"

        tid = scheduler.submit(Task(name="retry_me", priority=1, callback=fail_then_succeed))
        await asyncio.sleep(0.5)
        assert scheduler.get_status(tid) == "failed"
        assert len(scheduler.get_dlq()) == 1

        count = scheduler.retry_dlq()
        assert count == 1
        await asyncio.sleep(0.5)
        assert len(scheduler.get_dlq()) == 0
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_no_dlq_when_disabled(self):
        scheduler = Scheduler(num_workers=1, max_retries=0, dlq=False)
        await scheduler.start()

        def fail():
            raise RuntimeError("fail")

        tid = scheduler.submit(Task(name="fail", priority=1, callback=fail))
        await asyncio.sleep(0.3)
        assert scheduler.get_status(tid) == "failed"
        assert scheduler.get_dlq() == []
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        scheduler = Scheduler(num_workers=1, max_retries=2, dlq=False)
        await scheduler.start()

        timestamps = []

        def timed_fail():
            timestamps.append(time.time())
            raise RuntimeError("fail")

        scheduler.submit(Task(name="backoff", priority=1, callback=timed_fail))
        await asyncio.sleep(2)

        # 3 attempts: original + 2 retries
        assert len(timestamps) == 3
        delay1 = timestamps[1] - timestamps[0]  # 0.1 * 2^0 = 0.1s
        delay2 = timestamps[2] - timestamps[1]  # 0.1 * 2^1 = 0.2s
        assert delay1 >= 0.08, f"First retry too fast: {delay1:.3f}s"
        assert delay2 >= 0.15, f"Second retry too fast: {delay2:.3f}s"
        assert delay2 > delay1, "Delays should increase"
        await scheduler.stop()
