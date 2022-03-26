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
    scheduler.add_job(app.run, "saga-hamburg-cronjob", day_of_week="mon-sat", hour='8-18', minute="*")
    scheduler.start()
