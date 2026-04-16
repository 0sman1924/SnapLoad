"""
threading_utils.py — Worker thread and queue bridge for yt-dlp operations.

Provides a generic WorkerThread that runs a callable in a daemon thread
and communicates results/errors back to the UI thread via queue.Queue.
The UI polls the queue using Tkinter's .after() scheduler.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any, Callable

logger = logging.getLogger(__name__)


class WorkerThread(threading.Thread):
    """
    Generic daemon worker thread for running blocking operations.

    Executes a target function in a background thread and places
    the result (or exception) into a result_queue for the main
    thread to consume.

    Usage:
        result_q = queue.Queue()
        worker = WorkerThread(
            target=some_blocking_function,
            args=(arg1, arg2),
            result_queue=result_q,
        )
        worker.start()

        # In UI: poll result_q with .after()
    """

    def __init__(
        self,
        target: Callable[..., Any],
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
        result_queue: queue.Queue | None = None,
        name: str = "WorkerThread",
    ):
        """
        Initialize the worker thread.

        Args:
            target: The callable to execute in the background.
            args: Positional arguments for the target.
            kwargs: Keyword arguments for the target.
            result_queue: Queue to place the result or exception into.
            name: Thread name for logging/debugging.
        """
        super().__init__(name=name, daemon=True)
        self._target_fn = target
        self._args = args
        self._kwargs = kwargs or {}
        self.result_queue = result_queue or queue.Queue()

    def run(self) -> None:
        """Execute the target function and push result to the queue."""
        try:
            result = self._target_fn(*self._args, **self._kwargs)
            self.result_queue.put(("success", result))
        except Exception as exc:
            logger.exception("Worker thread '%s' failed", self.name)
            self.result_queue.put(("error", exc))


class QueuePoller:
    """
    Polls a queue.Queue from the Tkinter main thread using .after().

    Continuously checks the queue at a given interval and invokes
    a callback for each item found. Stops when a sentinel value is
    received or when explicitly stopped.
    """

    # Sentinel value to signal the poller to stop
    STOP_SENTINEL = object()

    def __init__(
        self,
        root,
        data_queue: queue.Queue,
        callback: Callable[[Any], None],
        interval_ms: int = 100,
    ):
        """
        Initialize the queue poller.

        Args:
            root: The Tkinter/CTk root widget (used for .after() scheduling).
            data_queue: The queue to poll for data.
            callback: Called with each item retrieved from the queue.
            interval_ms: Polling interval in milliseconds.
        """
        self._root = root
        self._queue = data_queue
        self._callback = callback
        self._interval = interval_ms
        self._running = False
        self._after_id: str | None = None

    def start(self) -> None:
        """Start polling the queue."""
        self._running = True
        self._poll()

    def stop(self) -> None:
        """Stop polling the queue."""
        self._running = False
        if self._after_id is not None:
            try:
                self._root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _poll(self) -> None:
        """Check the queue for new items and schedule the next poll."""
        if not self._running:
            return

        try:
            while True:
                item = self._queue.get_nowait()
                if item is self.STOP_SENTINEL:
                    self._running = False
                    return
                self._callback(item)
        except queue.Empty:
            pass

        # Schedule next poll
        self._after_id = self._root.after(self._interval, self._poll)
