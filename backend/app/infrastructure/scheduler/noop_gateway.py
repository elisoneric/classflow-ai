class NoOpSchedulerGateway:
    """Placeholder SchedulerGateway used before the scheduler process (PROJECT.md §9,
    task 15) exists. Cancelling a job is then a no-op — the corresponding APScheduler
    job simply doesn't exist yet, so there's nothing to remove.
    """

    async def cancel_job(self, job_id: str) -> None:
        return None
