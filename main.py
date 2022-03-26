from apscheduler.schedulers.background import BackgroundScheduler
from comparator import SupportedComparator
from app import App

infos = [
    SupportedComparator(min_rooms=4, max_total_rent=1300),
    SupportedComparator(min_rooms=3, max_total_rent=1300, is_house=True),
]

if __name__ == "__main__":
    app = App(comparators=infos)
    scheduler = BackgroundScheduler()

    try:
        scheduler.add_job(app.run, "cron", day_of_week="mon-sat", hour='8-18', minute="*", id='saga_hamburg_cron_job')
        scheduler.start()
    except KeyboardInterrupt:
        if app is not None and app.mqtt is not None:
            app.mqtt.loop_stop()
        if scheduler is not None:
            scheduler.remove_job('saga_hamburg_cron_job')
