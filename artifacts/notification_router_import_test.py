from syk_jarmin.runtime.notification_router import NotificationRouter

router = NotificationRouter()

notification = router.route(
    event_type="analysis_completed",
    message="Test",
)

print("NOTIFICATION_ROUTER_OK")
print(notification.event_type)
print(notification.level)
print(notification.notification_sha256)
