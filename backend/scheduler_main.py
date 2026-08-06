import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.scheduler import generate_daily_sessions
from app.services.email_ingestion import poll_inbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    scheduler = BackgroundScheduler()
    # Run every day at 00:01
    scheduler.add_job(generate_daily_sessions, 'cron', hour=0, minute=1)
    
    # Poll email inbox every 2 minutes
    scheduler.add_job(poll_inbox, 'interval', minutes=2)
    
    scheduler.start()
    logger.info("APScheduler started. Waiting for jobs...")
    
    # Also trigger once on startup just in case we missed it
    logger.info("Triggering initial session generation on startup...")
    generate_daily_sessions()

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully.")

if __name__ == "__main__":
    main()
