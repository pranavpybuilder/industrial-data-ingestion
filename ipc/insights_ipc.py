from storage.repositories.insight_repo import InsightRepository

insight_repo = InsightRepository()


def get_insights_ipc(run_id: str):
    insights = insight_repo.get_insights(run_id)

    return {
        "success": True,
        "data": insights,
    }