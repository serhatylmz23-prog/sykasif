from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from syk_core.runtime_kernel import (
    RuntimeEventBus,
    RuntimeScheduler,
    RuntimeSchedulerError,
    ScheduledTaskPriority,
    ScheduledTaskState,
)


class ManualClock:
    def __init__(
        self,
        current: datetime,
    ) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current

    def advance(
        self,
        delta: timedelta,
    ) -> None:
        self.current += delta


def create_scheduler() -> tuple[
    RuntimeScheduler,
    ManualClock,
]:
    clock = ManualClock(
        datetime(
            2026,
            8,
            4,
            12,
            0,
            tzinfo=UTC,
        )
    )

    scheduler = RuntimeScheduler(
        event_bus=RuntimeEventBus(),
        clock=clock.now,
    )

    return scheduler, clock


def test_once_task_runs_when_due() -> None:
    scheduler, clock = create_scheduler()
    results: list[str] = []

    task = scheduler.schedule_once(
        name="kanıt üret",
        handler=lambda: results.append("tamam"),
        delay=timedelta(seconds=5),
    )

    assert scheduler.run_due() == tuple()

    clock.advance(timedelta(seconds=5))
    records = scheduler.run_due()

    assert len(records) == 1
    assert records[0].successful is True
    assert results == ["tamam"]
    assert task.state is ScheduledTaskState.COMPLETED


def test_delayed_task_does_not_run_early() -> None:
    scheduler, clock = create_scheduler()
    run_count = {"value": 0}

    scheduler.schedule_once(
        name="gecikmeli görev",
        handler=lambda: run_count.__setitem__(
            "value",
            run_count["value"] + 1,
        ),
        delay=timedelta(seconds=10),
    )

    clock.advance(timedelta(seconds=9))

    assert scheduler.run_due() == tuple()
    assert run_count["value"] == 0


def test_interval_task_runs_repeatedly() -> None:
    scheduler, clock = create_scheduler()
    run_count = {"value": 0}

    task = scheduler.schedule_interval(
        name="sensör kontrolü",
        handler=lambda: run_count.__setitem__(
            "value",
            run_count["value"] + 1,
        ),
        interval=timedelta(seconds=5),
        start_immediately=True,
    )

    scheduler.run_due()

    clock.advance(timedelta(seconds=5))
    scheduler.run_due()

    clock.advance(timedelta(seconds=5))
    scheduler.run_due()

    assert run_count["value"] == 3
    assert task.run_count == 3
    assert task.state is ScheduledTaskState.SCHEDULED


def test_cancelled_task_does_not_run() -> None:
    scheduler, clock = create_scheduler()
    run_count = {"value": 0}

    task = scheduler.schedule_once(
        name="iptal görevi",
        handler=lambda: run_count.__setitem__(
            "value",
            1,
        ),
        delay=timedelta(seconds=1),
    )

    scheduler.cancel(task.task_id)
    clock.advance(timedelta(seconds=1))

    assert scheduler.run_due() == tuple()
    assert run_count["value"] == 0
    assert task.state is ScheduledTaskState.CANCELLED


def test_duplicate_task_id_is_rejected() -> None:
    scheduler, _ = create_scheduler()

    scheduler.schedule_once(
        task_id="SABİT-GÖREV",
        name="ilk görev",
        handler=lambda: None,
    )

    with pytest.raises(
        RuntimeSchedulerError,
        match="zaten kayıtlı",
    ):
        scheduler.schedule_once(
            task_id="SABİT-GÖREV",
            name="ikinci görev",
            handler=lambda: None,
        )


def test_higher_priority_runs_first() -> None:
    scheduler, _ = create_scheduler()
    order: list[str] = []

    scheduler.schedule_once(
        name="düşük",
        handler=lambda: order.append("düşük"),
        priority=ScheduledTaskPriority.LOW,
    )

    scheduler.schedule_once(
        name="kritik",
        handler=lambda: order.append("kritik"),
        priority=ScheduledTaskPriority.CRITICAL,
    )

    scheduler.schedule_once(
        name="normal",
        handler=lambda: order.append("normal"),
        priority=ScheduledTaskPriority.NORMAL,
    )

    scheduler.run_due()

    assert order == [
        "kritik",
        "normal",
        "düşük",
    ]


def test_failed_task_is_retried() -> None:
    scheduler, clock = create_scheduler()
    attempts = {"value": 0}

    def handler() -> str:
        attempts["value"] += 1

        if attempts["value"] < 2:
            raise RuntimeError("geçici hata")

        return "başarılı"

    task = scheduler.schedule_once(
        name="yeniden deneme",
        handler=handler,
        max_retries=2,
        retry_delay=timedelta(seconds=3),
    )

    first_records = scheduler.run_due()

    assert first_records[0].successful is False
    assert task.state is (
        ScheduledTaskState.RETRY_WAITING
    )
    assert task.retry_count == 1

    clock.advance(timedelta(seconds=3))
    second_records = scheduler.run_due()

    assert second_records[0].successful is True
    assert task.state is ScheduledTaskState.COMPLETED
    assert attempts["value"] == 2


def test_task_fails_after_retry_limit() -> None:
    scheduler, clock = create_scheduler()

    task = scheduler.schedule_once(
        name="sürekli hata",
        handler=lambda: (
            (_ for _ in ()).throw(
                RuntimeError("kalıcı hata")
            )
        ),
        max_retries=1,
        retry_delay=timedelta(seconds=2),
    )

    scheduler.run_due()

    assert task.state is (
        ScheduledTaskState.RETRY_WAITING
    )

    clock.advance(timedelta(seconds=2))
    scheduler.run_due()

    assert task.state is ScheduledTaskState.FAILED
    assert task.failure_count == 2
    assert task.retry_count == 1
    assert "kalıcı hata" in str(task.last_error)


def test_run_due_limit_is_applied() -> None:
    scheduler, _ = create_scheduler()
    results: list[int] = []

    for index in range(3):
        scheduler.schedule_once(
            name=f"görev-{index}",
            handler=lambda index=index: (
                results.append(index)
            ),
        )

    first_records = scheduler.run_due(limit=2)

    assert len(first_records) == 2
    assert len(results) == 2

    second_records = scheduler.run_due()

    assert len(second_records) == 1
    assert len(results) == 3


def test_task_history_is_recorded() -> None:
    scheduler, _ = create_scheduler()

    scheduler.schedule_once(
        name="geçmiş görevi",
        handler=lambda: "sonuç",
    )

    scheduler.run_due()

    history = scheduler.history

    assert len(history) == 1
    assert history[0].task_name == "geçmiş görevi"
    assert history[0].successful is True
    assert history[0].result == "sonuç"


def test_scheduler_events_are_published() -> None:
    scheduler, _ = create_scheduler()

    scheduler.schedule_once(
        name="olay görevi",
        handler=lambda: None,
    )

    scheduler.run_due()

    topics = [
        event.topic
        for event in scheduler.event_bus.history
    ]

    assert (
        "runtime.scheduler.task.scheduled"
        in topics
    )
    assert (
        "runtime.scheduler.task.started"
        in topics
    )
    assert (
        "runtime.scheduler.task.completed"
        in topics
    )


def test_pending_tasks_are_time_ordered() -> None:
    scheduler, clock = create_scheduler()

    later = scheduler.schedule_once(
        name="sonra",
        handler=lambda: None,
        delay=timedelta(seconds=20),
    )

    earlier = scheduler.schedule_once(
        name="önce",
        handler=lambda: None,
        delay=timedelta(seconds=5),
    )

    pending = scheduler.pending_tasks()

    assert pending == (
        earlier,
        later,
    )

    clock.advance(timedelta(seconds=5))
    scheduler.run_due()

    assert scheduler.pending_tasks() == (
        later,
    )


def test_snapshot_preserves_turkish_keys() -> None:
    scheduler, _ = create_scheduler()

    scheduler.schedule_once(
        name="Türkçe görev",
        handler=lambda: "tamam",
        metadata={
            "kaynak": "görüntü",
            "açıklama": "yüzey analizi",
        },
    )

    scheduler.run_due()
    payload = scheduler.snapshot()

    assert payload["toplam_görev_sayısı"] == 1
    assert payload["tamamlanan_görev_sayısı"] == 1
    assert payload["başarısız_görev_sayısı"] == 0
    assert payload["çalışma_geçmişi_sayısı"] == 1
    assert payload["görevler"][0]["ad"] == (
        "Türkçe görev"
    )
    assert payload["görevler"][0]["veri"][
        "açıklama"
    ] == "yüzey analizi"


def test_invalid_interval_is_rejected() -> None:
    scheduler, _ = create_scheduler()

    with pytest.raises(
        RuntimeSchedulerError,
        match="sıfırdan büyük",
    ):
        scheduler.schedule_interval(
            name="geçersiz",
            handler=lambda: None,
            interval=timedelta(),
        )
