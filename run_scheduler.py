"""Entry point to start the background scheduler for Todas Store.
Run with:
    python run_scheduler.py
It will import the Flask app context to ensure DB access.
"""
from app import create_app
from app.services.scheduler_service import start_scheduler

app = create_app()

if __name__ == "__main__":
    # Run scheduler within the app context so DB models are available.
    with app.app_context():
        start_scheduler()
        # Keep the main thread alive – simple infinite loop.
        import time
        while True:
            time.sleep(60)
