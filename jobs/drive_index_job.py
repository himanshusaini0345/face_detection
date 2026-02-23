from apscheduler.schedulers.background import BackgroundScheduler


def start_index_job(photo_service, interval_hours: int = 24):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        photo_service.index_last_24_hours,
        "interval",
        hours=interval_hours,
        id="drive_index_job",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler          # keep reference so it isn't GC'd