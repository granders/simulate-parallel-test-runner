from simulate_parallel_runner.schedulers.metrics import task_footprint, efficiency


def simulate_linear_scheduler(task_list):

    resource_limit = max([t.resource for t in task_list])
    total_duration = sum([t.duration for t in task_list])
    total_footprint = resource_limit * total_duration

    x = {
        'nodes': resource_limit,
        'duration': total_duration,
        'resource_footprint': total_footprint,
        'task_footprint': task_footprint(task_list),
        'efficiency': efficiency(task_list, total_duration, resource_limit)
    }

    print x
