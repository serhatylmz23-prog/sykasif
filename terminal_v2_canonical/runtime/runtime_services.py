from terminal_v2.runtime.scheduler import Scheduler
from terminal_v2.runtime.monitor import RuntimeMonitor

scheduler=Scheduler()

monitor=RuntimeMonitor()

scheduler.every(
    1,
    monitor.heartbeat
)

scheduler.run()
