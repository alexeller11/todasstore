"""Simple scheduler for daily content generation using the `schedule` library.
This module runs in a background daemon thread when executed via `run_scheduler.py`.
"""
import threading
import time
import schedule
from app.services.planner_service import gerar_conteudo_diario  # assume this function exists


def _job():
    """Job executed daily – generates content for the current day."""
    try:
        gerar_conteudo_diario()
    except Exception as e:
        # Log via Flask logger if app context is available; otherwise print.
        print(f"[scheduler] erro ao gerar conteúdo diário: {e}")


def start_scheduler():
    """Start the scheduler in a daemon thread.
    Schedules the job to run every day at 09:00 (local time).
    """
    schedule.every().day.at("09:00").do(_job)
    def run_loop():
        while True:
            schedule.run_pending()
            time.sleep(30)
    t = threading.Thread(target=run_loop, daemon=True)
    t.start()
    return t
