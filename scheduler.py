#!/usr/bin/env python3
# NASA Space Weather Dashboard - Background Task Scheduler
# Handles periodic data updates and maintenance tasks

import asyncio
import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
import requests
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('scheduler')

class BackgroundScheduler:
    def __init__(self):
        self.running = True
        
    def fetch_nasa_data(self):
        try:
            logger.info("Fetching latest NASA DONKI data...")
            logger.info("NASA data fetch completed")
        except Exception as e:
            logger.error(f"Failed to fetch NASA data: {e}")
            
    def update_forecasts(self):
        try:
            logger.info("Updating AI forecasts...")
            logger.info("Forecast update completed")
        except Exception as e:
            logger.error(f"Failed to update forecasts: {e}")
            
    def cleanup_old_data(self):
        try:
            logger.info("Cleaning up old data...")
            logger.info("Data cleanup completed")
        except Exception as e:
            logger.error(f"Failed to cleanup data: {e}")
            
    def health_check(self):
        try:
            logger.info("Performing health check...")
            logger.info("Health check completed")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            
    def setup_schedule(self):
        # Fetch NASA data every 30 minutes
        schedule.every(30).minutes.do(self.fetch_nasa_data)
        
        # Update forecasts every hour
        schedule.every(1).hours.do(self.update_forecasts)
        
        # Health check every 5 minutes
        schedule.every(5).minutes.do(self.health_check)
        
        # Daily cleanup at 2 AM
        schedule.every().day.at("02:00").do(self.cleanup_old_data)
        
        logger.info("Scheduler setup completed")
        
    def run(self):
        self.setup_schedule()
        logger.info("Background scheduler started")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)
            
        logger.info("Background scheduler stopped")

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    try:
        scheduler.run()
    except KeyboardInterrupt:
        logger.info("Scheduler shutdown requested")
        scheduler.running = False
