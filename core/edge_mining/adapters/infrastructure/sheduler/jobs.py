"""Job scheduler for running optimization tasks at regular intervals."""

from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from edge_mining.application.interfaces import HomeLoadHistoryServiceInterface, OptimizationServiceInterface
from edge_mining.application.services.load_forecast_training_service import LoadForecastModelTrainingService
from edge_mining.shared.logging.port import LoggerPort
from edge_mining.shared.scheduler.port import SchedulerPort
from edge_mining.shared.settings.settings import AppSettings


class AutomationScheduler(SchedulerPort):
    """Scheduler for running optimization jobs at regular intervals."""

    def __init__(
        self,
        optimization_service: OptimizationServiceInterface,
        logger: LoggerPort,
        settings: AppSettings,
        home_load_history_service: Optional[HomeLoadHistoryServiceInterface] = None,
        load_forecast_training_service: Optional[LoadForecastModelTrainingService] = None,
    ):
        self.optimization_service = optimization_service
        self.home_load_history_service = home_load_history_service
        self.load_forecast_training_service = load_forecast_training_service
        self.logger = logger
        self.settings = settings
        self.scheduler = AsyncIOScheduler(timezone=self.settings.timezone)

        self._job_id = "evaluate_mining"
        self._history_collect_job_id = "collect_load_history"
        self._history_purge_job_id = "purge_load_history"
        self._model_training_job_id = "train_load_forecast_models"

    async def _run_evaluation_job(self):
        """Wrapper to call the optimization service's run method."""
        self.logger.debug(f"Scheduler triggered. Running job: {self._job_id}.")
        try:
            await self.optimization_service.run_all_enabled_units()
        except Exception as e:
            self.logger.error(f"Error during scheduled job: {self._job_id}. {e}")

    async def _run_history_collect_job(self):
        """Collect power points from all history providers."""
        self.logger.debug(f"Scheduler triggered. Running job: {self._history_collect_job_id}.")
        if not self.home_load_history_service:
            return
        try:
            await self.home_load_history_service.collect_all()
        except Exception as e:
            self.logger.error(f"Error during scheduled job: {self._history_collect_job_id}. {e}")

    async def _run_history_purge_job(self):
        """Purge old power points beyond retention window."""
        self.logger.debug(f"Scheduler triggered. Running job: {self._history_purge_job_id}.")
        if not self.home_load_history_service:
            return
        try:
            await self.home_load_history_service.purge_all(
                retention_days=self.settings.history_retention_days,
            )
        except Exception as e:
            self.logger.error(f"Error during scheduled job: {self._history_purge_job_id}. {e}")

    async def _run_model_training_job(self):
        """Train ML forecast models on collected history."""
        self.logger.debug(f"Scheduler triggered. Running job: {self._model_training_job_id}.")
        if not self.load_forecast_training_service:
            return
        try:
            await self.load_forecast_training_service.train_all()
        except Exception as e:
            self.logger.error(f"Error during scheduled job: {self._model_training_job_id}. {e}")

    async def start(self):
        """Adds the job and starts the scheduler."""
        interval = self.settings.scheduler_interval_seconds
        self.logger.debug(f"Starting scheduler. job |{self._job_id}| will run every {interval} seconds.")

        self.scheduler.add_job(
            self._run_evaluation_job,
            "interval",
            seconds=interval,
            id=self._job_id,
            replace_existing=True,
            max_instances=1,
        )

        if self.home_load_history_service:
            ingestion_interval = self.settings.history_ingestion_interval_seconds
            self.logger.debug(
                f"Scheduling history ingestion every {ingestion_interval}s "
                f"and purge daily (retention={self.settings.history_retention_days}d)."
            )
            self.scheduler.add_job(
                self._run_history_collect_job,
                "interval",
                seconds=ingestion_interval,
                id=self._history_collect_job_id,
                replace_existing=True,
            )
            self.scheduler.add_job(
                self._run_history_purge_job,
                "cron",
                hour=3,
                minute=0,
                id=self._history_purge_job_id,
                replace_existing=True,
            )

        if self.load_forecast_training_service:
            self.logger.debug("Scheduling nightly ML model training at 04:00.")
            self.scheduler.add_job(
                self._run_model_training_job,
                "cron",
                hour=4,
                minute=0,
                id=self._model_training_job_id,
                replace_existing=True,
            )

        self.logger.debug("Scheduler started.")
        self.scheduler.start()

    def stop(self):
        self.logger.debug(f"Scheduler stopped. Job: {self._job_id}")
        self.scheduler.shutdown()
