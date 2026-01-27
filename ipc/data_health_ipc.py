# ipc/data_health_ipc.py

from storage.repositories.profiling_repo import ProfilingRepository

profiling_repo = ProfilingRepository()


def get_data_health_ipc(run_id: str):
    results = profiling_repo.get_profiling_results(run_id)

    return {
        "success": True,
        "data": results,  # frontend handles empty state
    }