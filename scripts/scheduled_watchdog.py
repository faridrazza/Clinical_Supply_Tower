#!/usr/bin/env python3
"""
Scheduled Supply Watchdog - Autonomous Monitoring with Email Alerts.

This script runs Workflow A on a schedule (default: daily at 8:00 AM)
and sends email alerts via Resend when risks are detected.

Usage:
    # Run once immediately
    python scripts/scheduled_watchdog.py --run-now
    
    # Start scheduler (runs daily)
    python scripts/scheduled_watchdog.py
    
    # Custom schedule (every 6 hours)
    python scripts/scheduled_watchdog.py --interval-hours 6

Environment Variables Required:
    - RESEND_API_KEY: Your Resend API key
    - ALERT_EMAIL_TO: Recipient email address
    - ALERT_EMAIL_FROM: Sender email (default: onboarding@resend.dev)
    - WATCHDOG_SCHEDULE_HOUR: Hour to run (default: 8)
    - WATCHDOG_SCHEDULE_MINUTE: Minute to run (default: 0)
"""
import os
import sys
import argparse
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.workflows.orchestrator import get_orchestrator
from src.services.email_service import send_watchdog_alert

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('watchdog.log')
    ]
)
logger = logging.getLogger("scheduled_watchdog")


def run_watchdog(send_email: bool = True) -> dict:
    """
    Execute Supply Watchdog workflow and optionally send email alert.
    
    Args:
        send_email: Whether to send email alert (default: True)
        
    Returns:
        Dictionary with execution results
    """
    logger.info("=" * 60)
    logger.info("SUPPLY WATCHDOG - Starting Execution")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        # Get orchestrator and run workflow
        orchestrator = get_orchestrator()
        result = orchestrator.run_supply_watchdog(trigger_type="scheduled")
        
        if result.get("success"):
            summary = result.get("summary", {})
            logger.info("Workflow completed successfully")
            logger.info(f"  - Expiring batches: {summary.get('expiring_batches', 0)}")
            logger.info(f"  - Critical batches: {summary.get('critical_batches', 0)}")
            logger.info(f"  - Shortfalls: {summary.get('shortfalls', 0)}")
        else:
            logger.error(f"Workflow failed: {result.get('error')}")
        
        # Send email alert
        if send_email:
            logger.info("Sending email alert...")
            email_result = send_watchdog_alert(result)
            
            if email_result.get("success"):
                logger.info(f"Email sent successfully to {email_result.get('to')}")
            else:
                logger.warning(f"Email failed: {email_result.get('error')}")
            
            result["email_result"] = email_result
        
        return result
    
    except Exception as e:
        logger.error(f"Watchdog execution failed: {str(e)}", exc_info=True)
        
        # Try to send error notification
        if send_email:
            error_result = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time": datetime.now().isoformat()
            }
            send_watchdog_alert(error_result)
        
        return {"success": False, "error": str(e)}


def start_scheduler(
    interval_hours: int = None,
    schedule_hour: int = None,
    schedule_minute: int = None
):
    """
    Start the APScheduler to run watchdog on schedule.
    
    Args:
        interval_hours: Run every N hours (overrides daily schedule)
        schedule_hour: Hour to run daily (default from env: 8)
        schedule_minute: Minute to run daily (default from env: 0)
    """
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    
    scheduler = BlockingScheduler()
    
    if interval_hours:
        # Interval-based scheduling
        trigger = IntervalTrigger(hours=interval_hours)
        logger.info(f"Scheduler configured: Every {interval_hours} hours")
    else:
        # Daily scheduling at specific time
        hour = schedule_hour or int(os.getenv("WATCHDOG_SCHEDULE_HOUR", "8"))
        minute = schedule_minute or int(os.getenv("WATCHDOG_SCHEDULE_MINUTE", "0"))
        trigger = CronTrigger(hour=hour, minute=minute)
        logger.info(f"Scheduler configured: Daily at {hour:02d}:{minute:02d}")
    
    scheduler.add_job(
        run_watchdog,
        trigger=trigger,
        id="supply_watchdog",
        name="Supply Watchdog Daily Alert",
        replace_existing=True
    )
    
    logger.info("=" * 60)
    logger.info("SUPPLY WATCHDOG SCHEDULER STARTED")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Supply Watchdog - Autonomous Monitoring with Email Alerts"
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run watchdog immediately (once) and exit"
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip sending email alert"
    )
    parser.add_argument(
        "--interval-hours",
        type=int,
        help="Run every N hours instead of daily"
    )
    parser.add_argument(
        "--hour",
        type=int,
        help="Hour to run daily (0-23)"
    )
    parser.add_argument(
        "--minute",
        type=int,
        default=0,
        help="Minute to run daily (0-59)"
    )
    
    args = parser.parse_args()
    
    # Check required environment variables
    if not args.no_email:
        if not os.getenv("RESEND_API_KEY"):
            logger.warning("RESEND_API_KEY not set - emails will be disabled")
        if not os.getenv("ALERT_EMAIL_TO"):
            logger.warning("ALERT_EMAIL_TO not set - emails will be disabled")
    
    if args.run_now:
        # Run once and exit
        result = run_watchdog(send_email=not args.no_email)
        
        # Print JSON output
        if result.get("success") and result.get("output"):
            import json
            print("\n" + "=" * 60)
            print("JSON OUTPUT:")
            print("=" * 60)
            print(json.dumps(result["output"], indent=2))
        
        sys.exit(0 if result.get("success") else 1)
    else:
        # Start scheduler
        start_scheduler(
            interval_hours=args.interval_hours,
            schedule_hour=args.hour,
            schedule_minute=args.minute
        )


if __name__ == "__main__":
    main()
