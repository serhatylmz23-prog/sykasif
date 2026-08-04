"""Çalışma zamanı görev planlayıcısı."""

from __future__ import annotations

import heapq
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum, IntEnum
from threading import RLock
from typing import Any
from uuid import uuid4

from .event_bus import RuntimeEvent, RuntimeEventBus


class RuntimeSchedulerError(RuntimeError):
    """Görev planlayıcı hatası."""


class ScheduledTaskState(str, Enum):
    SCHEDULED = "planlandı"
    RUNNING = "çalışıyor"
    COMPLETED = "tamamlandı"
    RETRY_WAITING = "yeniden_deneme_bekliyor"
    CANCELLED = "iptal_edildi"
    FAILED = "başarısız"


class ScheduledTaskPriority(IntEnum):
    LOW = 10
    NORMAL = 20
    HIGH = 30
    CRITICAL = 40


ScheduledTaskHandler = Callable[[], Any]


@dataclass(slots=True)
class ScheduledTask:
    task_id: str
    name: str
    handler: ScheduledTaskHandler
    next_run_at: datetime
    priority: ScheduledTaskPriority = (
        ScheduledTaskPriority.NORMAL
    )
    interval: timedelta | None = None
    max_retries: int = 0
    retry_delay: timedelta = timedelta(seconds=1)
    allow_overlap: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    state: ScheduledTaskState = (
        ScheduledTaskState.SCHEDULED
    )
    run_count: int = 0
    failure_count: int = 0
    retry_count: int = 0
    last_started_at: datetime | None = None
    last_finished_at: datetime | None = None
    last_error: str | None = None
    last_result: Any = None

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("Görev kimliği boş olamaz.")

        if not self.name.strip():
            raise ValueError("Görev adı boş olamaz.")

        if self.next_run_at.tzinfo is None:
            raise ValueError(
                "Görev zamanı saat dilimi bilgisi içermelidir."
            )

        if self.interval is not None:
            if self.interval.total_seconds() <= 0:
                raise ValueError(
                    "Görev aralığı sıfırdan büyük olmalıdır."
                )

        if self.max_retries < 0:
            raise ValueError(
                "Yeniden deneme sayısı negatif olamaz."
            )

        if self.retry_delay.total_seconds() < 0:
            raise ValueError(
                "Yeniden deneme gecikmesi negatif olamaz."
            )

    @property
    def is_recurring(self) -> bool:
        return self.interval is not None

    @property
    def is_terminal(self) -> bool:
        return self.state in {
            ScheduledTaskState.COMPLETED,
            ScheduledTaskState.CANCELLED,
            ScheduledTaskState.FAILED,
        }

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "görev_kimliği": self.task_id,
            "ad": self.name,
            "durum": self.state.value,
            "öncelik": self.priority.name.lower(),
            "sonraki_çalışma": self.next_run_at.isoformat(),
            "aralıklı": self.is_recurring,
            "aralık_saniye": (
                self.interval.total_seconds()
                if self.interval is not None
                else None
            ),
            "çalışma_sayısı": self.run_count,
            "hata_sayısı": self.failure_count,
            "yeniden_deneme_sayısı": self.retry_count,
            "azami_yeniden_deneme": self.max_retries,
            "son_hata": self.last_error,
            "çakışmaya_izin_ver": self.allow_overlap,
            "veri": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class ScheduledTaskRunRecord:
    task_id: str
    task_name: str
    successful: bool
    attempt: int
    started_at: datetime
    finished_at: datetime
    result: Any = None
    error: str | None = None

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "görev_kimliği": self.task_id,
            "görev_adı": self.task_name,
            "başarılı": self.successful,
            "deneme": self.attempt,
            "başlangıç": self.started_at.isoformat(),
            "bitiş": self.finished_at.isoformat(),
            "sonuç": self.result,
            "hata": self.error,
        }


class RuntimeScheduler:
    """Öncelikli ve yeniden denemeli görev planlayıcı."""

    def __init__(
        self,
        *,
        event_bus: RuntimeEventBus | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.event_bus = event_bus or RuntimeEventBus()
        self._clock = clock or (
            lambda: datetime.now(UTC)
        )

        self._tasks: dict[str, ScheduledTask] = {}
        self._queue: list[
            tuple[datetime, int, int, str]
        ] = []
        self._history: list[
            ScheduledTaskRunRecord
        ] = []
        self._running_task_ids: set[str] = set()
        self._sequence = 0
        self._lock = RLock()

    def schedule_once(
        self,
        *,
        name: str,
        handler: ScheduledTaskHandler,
        run_at: datetime | None = None,
        delay: timedelta | None = None,
        priority: ScheduledTaskPriority = (
            ScheduledTaskPriority.NORMAL
        ),
        max_retries: int = 0,
        retry_delay: timedelta = timedelta(seconds=1),
        allow_overlap: bool = False,
        metadata: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> ScheduledTask:
        if run_at is not None and delay is not None:
            raise RuntimeSchedulerError(
                "run_at ve delay birlikte kullanılamaz."
            )

        if run_at is None:
            run_at = self._clock() + (
                delay or timedelta()
            )

        return self._create_task(
            name=name,
            handler=handler,
            run_at=run_at,
            interval=None,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            allow_overlap=allow_overlap,
            metadata=metadata,
            task_id=task_id,
        )

    def schedule_interval(
        self,
        *,
        name: str,
        handler: ScheduledTaskHandler,
        interval: timedelta,
        first_run_at: datetime | None = None,
        start_immediately: bool = False,
        priority: ScheduledTaskPriority = (
            ScheduledTaskPriority.NORMAL
        ),
        max_retries: int = 0,
        retry_delay: timedelta = timedelta(seconds=1),
        allow_overlap: bool = False,
        metadata: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> ScheduledTask:
        if interval.total_seconds() <= 0:
            raise RuntimeSchedulerError(
                "Görev aralığı sıfırdan büyük olmalıdır."
            )

        if (
            first_run_at is not None
            and start_immediately
        ):
            raise RuntimeSchedulerError(
                "first_run_at ve start_immediately "
                "birlikte kullanılamaz."
            )

        if first_run_at is None:
            first_run_at = self._clock()

            if not start_immediately:
                first_run_at += interval

        return self._create_task(
            name=name,
            handler=handler,
            run_at=first_run_at,
            interval=interval,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            allow_overlap=allow_overlap,
            metadata=metadata,
            task_id=task_id,
        )

    def cancel(
        self,
        task_id: str,
    ) -> ScheduledTask:
        task = self.get(task_id)

        if task.state is ScheduledTaskState.RUNNING:
            raise RuntimeSchedulerError(
                "Çalışan görev doğrudan iptal edilemez."
            )

        if task.is_terminal:
            return task

        task.state = ScheduledTaskState.CANCELLED

        self.event_bus.publish(
            RuntimeEvent(
                topic="runtime.scheduler.task.cancelled",
                source="runtime_scheduler",
                payload={
                    "task_id": task.task_id,
                    "name": task.name,
                },
            )
        )

        return task

    def get(
        self,
        task_id: str,
    ) -> ScheduledTask:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise RuntimeSchedulerError(
                f"Görev bulunamadı: {task_id}"
            ) from exc

    def run_due(
        self,
        *,
        now: datetime | None = None,
        limit: int | None = None,
    ) -> tuple[ScheduledTaskRunRecord, ...]:
        current_time = now or self._clock()

        if current_time.tzinfo is None:
            raise RuntimeSchedulerError(
                "Çalıştırma zamanı saat dilimi "
                "bilgisi içermelidir."
            )

        if limit is not None and limit <= 0:
            raise RuntimeSchedulerError(
                "Görev sınırı sıfırdan büyük olmalıdır."
            )

        completed_records: list[
            ScheduledTaskRunRecord
        ] = []

        while True:
            with self._lock:
                queue_item = self._peek_due_item(
                    current_time
                )

                if queue_item is None:
                    break

                if (
                    limit is not None
                    and len(completed_records) >= limit
                ):
                    break

                heapq.heappop(self._queue)
                _, _, _, task_id = queue_item
                task = self._tasks.get(task_id)

            if task is None:
                continue

            if task.state in {
                ScheduledTaskState.CANCELLED,
                ScheduledTaskState.COMPLETED,
                ScheduledTaskState.FAILED,
            }:
                continue

            if (
                task_id in self._running_task_ids
                and not task.allow_overlap
            ):
                self._reschedule_overlap(task)
                continue

            record = self._execute_task(
                task,
                current_time=current_time,
            )

            completed_records.append(record)

        return tuple(completed_records)

    def pending_tasks(
        self,
    ) -> tuple[ScheduledTask, ...]:
        return tuple(
            sorted(
                (
                    task
                    for task in self._tasks.values()
                    if not task.is_terminal
                ),
                key=lambda task: (
                    task.next_run_at,
                    -int(task.priority),
                    task.task_id,
                ),
            )
        )

    def snapshot(self) -> dict[str, Any]:
        tasks = sorted(
            self._tasks.values(),
            key=lambda task: task.task_id,
        )

        return {
            "toplam_görev_sayısı": len(tasks),
            "bekleyen_görev_sayısı": sum(
                1
                for task in tasks
                if task.state
                in {
                    ScheduledTaskState.SCHEDULED,
                    ScheduledTaskState.RETRY_WAITING,
                }
            ),
            "çalışan_görev_sayısı": len(
                self._running_task_ids
            ),
            "tamamlanan_görev_sayısı": sum(
                1
                for task in tasks
                if task.state
                is ScheduledTaskState.COMPLETED
            ),
            "başarısız_görev_sayısı": sum(
                1
                for task in tasks
                if task.state
                is ScheduledTaskState.FAILED
            ),
            "iptal_edilen_görev_sayısı": sum(
                1
                for task in tasks
                if task.state
                is ScheduledTaskState.CANCELLED
            ),
            "çalışma_geçmişi_sayısı": len(
                self._history
            ),
            "görevler": [
                task.to_runtime_dict()
                for task in tasks
            ],
            "çalışma_geçmişi": [
                record.to_runtime_dict()
                for record in self._history
            ],
        }

    @property
    def history(
        self,
    ) -> tuple[ScheduledTaskRunRecord, ...]:
        with self._lock:
            return tuple(self._history)

    def _create_task(
        self,
        *,
        name: str,
        handler: ScheduledTaskHandler,
        run_at: datetime,
        interval: timedelta | None,
        priority: ScheduledTaskPriority,
        max_retries: int,
        retry_delay: timedelta,
        allow_overlap: bool,
        metadata: dict[str, Any] | None,
        task_id: str | None,
    ) -> ScheduledTask:
        generated_task_id = (
            task_id
            or "SYK-TASK-" + uuid4().hex.upper()
        )

        with self._lock:
            if generated_task_id in self._tasks:
                raise RuntimeSchedulerError(
                    "Görev kimliği zaten kayıtlı: "
                    f"{generated_task_id}"
                )

            task = ScheduledTask(
                task_id=generated_task_id,
                name=name,
                handler=handler,
                next_run_at=run_at,
                priority=priority,
                interval=interval,
                max_retries=max_retries,
                retry_delay=retry_delay,
                allow_overlap=allow_overlap,
                metadata=dict(metadata or {}),
            )

            self._tasks[task.task_id] = task
            self._push_task(task)

        self.event_bus.publish(
            RuntimeEvent(
                topic="runtime.scheduler.task.scheduled",
                source="runtime_scheduler",
                payload={
                    "task_id": task.task_id,
                    "name": task.name,
                    "run_at": task.next_run_at.isoformat(),
                    "recurring": task.is_recurring,
                    "priority": int(task.priority),
                },
            )
        )

        return task

    def _push_task(
        self,
        task: ScheduledTask,
    ) -> None:
        self._sequence += 1

        heapq.heappush(
            self._queue,
            (
                task.next_run_at,
                -int(task.priority),
                self._sequence,
                task.task_id,
            ),
        )

    def _peek_due_item(
        self,
        current_time: datetime,
    ) -> tuple[datetime, int, int, str] | None:
        while self._queue:
            item = self._queue[0]
            run_at, _, _, task_id = item
            task = self._tasks.get(task_id)

            if task is None:
                heapq.heappop(self._queue)
                continue

            if run_at != task.next_run_at:
                heapq.heappop(self._queue)
                continue

            if task.is_terminal:
                heapq.heappop(self._queue)
                continue

            if run_at > current_time:
                return None

            return item

        return None

    def _execute_task(
        self,
        task: ScheduledTask,
        *,
        current_time: datetime,
    ) -> ScheduledTaskRunRecord:
        task.state = ScheduledTaskState.RUNNING
        task.last_started_at = current_time

        with self._lock:
            self._running_task_ids.add(task.task_id)

        self.event_bus.publish(
            RuntimeEvent(
                topic="runtime.scheduler.task.started",
                source="runtime_scheduler",
                payload={
                    "task_id": task.task_id,
                    "name": task.name,
                    "attempt": task.retry_count + 1,
                },
            )
        )

        result: Any = None
        error_text: str | None = None
        successful = False

        try:
            result = task.handler()
            successful = True
        except Exception as exc:
            error_text = (
                f"{type(exc).__name__}: {exc}"
            )
        finally:
            finished_at = self._clock()

            with self._lock:
                self._running_task_ids.discard(
                    task.task_id
                )

        task.run_count += 1
        task.last_finished_at = finished_at

        if successful:
            task.last_result = result
            task.last_error = None
            task.retry_count = 0

            if task.interval is None:
                task.state = (
                    ScheduledTaskState.COMPLETED
                )
            else:
                task.state = (
                    ScheduledTaskState.SCHEDULED
                )
                task.next_run_at = (
                    current_time + task.interval
                )

                with self._lock:
                    self._push_task(task)

            self.event_bus.publish(
                RuntimeEvent(
                    topic=(
                        "runtime.scheduler.task.completed"
                    ),
                    source="runtime_scheduler",
                    payload={
                        "task_id": task.task_id,
                        "name": task.name,
                        "recurring": task.is_recurring,
                    },
                )
            )

        else:
            task.failure_count += 1
            task.last_error = error_text

            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.state = (
                    ScheduledTaskState.RETRY_WAITING
                )
                task.next_run_at = (
                    current_time + task.retry_delay
                )

                with self._lock:
                    self._push_task(task)

                self.event_bus.publish(
                    RuntimeEvent(
                        topic=(
                            "runtime.scheduler.task."
                            "retry_scheduled"
                        ),
                        source="runtime_scheduler",
                        payload={
                            "task_id": task.task_id,
                            "name": task.name,
                            "retry_count": task.retry_count,
                            "error": error_text,
                        },
                    )
                )
            else:
                task.state = ScheduledTaskState.FAILED

                self.event_bus.publish(
                    RuntimeEvent(
                        topic=(
                            "runtime.scheduler.task.failed"
                        ),
                        source="runtime_scheduler",
                        payload={
                            "task_id": task.task_id,
                            "name": task.name,
                            "error": error_text,
                        },
                    )
                )

        record = ScheduledTaskRunRecord(
            task_id=task.task_id,
            task_name=task.name,
            successful=successful,
            attempt=task.run_count,
            started_at=current_time,
            finished_at=finished_at,
            result=result,
            error=error_text,
        )

        with self._lock:
            self._history.append(record)

        return record

    def _reschedule_overlap(
        self,
        task: ScheduledTask,
    ) -> None:
        task.next_run_at = (
            self._clock() + timedelta(milliseconds=1)
        )

        with self._lock:
            self._push_task(task)

        self.event_bus.publish(
            RuntimeEvent(
                topic=(
                    "runtime.scheduler.task."
                    "overlap_prevented"
                ),
                source="runtime_scheduler",
                payload={
                    "task_id": task.task_id,
                    "name": task.name,
                },
            )
        )
