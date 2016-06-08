from simulate_parallel_runner.task import StartEvent, EndEvent, Resource
from simulate_parallel_runner.schedulers.metrics import efficiency, task_footprint

"""
With this strategy, we partition the cluster into N equal subclusters

Assume that we have good intel on resource usage, but know how to handle situations where this isn't true.
- Strategy 1: suppose subcluster is not big enough for a task. Then fail the task
- Strategy 2: Enqueue the task to be run by the sequential test runner

cluster size R, max cluster usage over all tasks M => split into N = R/M sub-clusters
(assume R is divisible by M)

Feed new task into a subcluster whenever the previous task has finished
"""


class SubclusterEventQueue(object):
    # an event list looks like this:
    #    [Start(t=0, task=t0), End(t=356, task=t0), Start(t=356, task=t4), End(400, task=t4)...]
    def __init__(self, resource):
        self.resource = resource
        self.events = []
        self.end_time = 0

    def add_task(self, task):
        task_start_time = self.end_time
        self.end_time += task.duration
        self.events.append(StartEvent(task_start_time, task))
        self.events.append(EndEvent(self.end_time, task))


def get_min_endtime_queue(event_queues):

    target_queue = None
    minimum_end = float('inf')
    for eq in event_queues:
        if eq.end_time < minimum_end:
            target_queue = eq
            minimum_end = eq.end_time

    return target_queue


def simulate_partitioned_cluster_scheduler(task_list, resource_limit):
    """
    R = resource_limit  # aka total cluster size
    M = max([task.resource for task in task_list])
    assert R >= M and R % M == 0
    N = R / M

    create N event lists
    an event list looks like this:
        [Start(t=0, task=t0), End(t=356, task=t0), Start(t=356, task=t4), End(400, task=t4)...]


    while len(task_list) > 0:
        task = task_list.pop()

        q = get_min_endtime_queue(subcluster_event_queues)  # return queue from collection with smallest end time
        q.add_task(task)
    """
    R = resource_limit  # aka total cluster size
    M = max([task.resource for task in task_list])
    assert R >= M and R % M == 0
    N = R / M

    # create N subcluster event queues
    subcluster_event_queues = [SubclusterEventQueue(Resource(M)) for _ in range(N)]

    task_list_copy = task_list[:]
    while len(task_list_copy) > 0:
        task = task_list_copy.pop()

        q = get_min_endtime_queue(subcluster_event_queues)  # return queue from collection with smallest end time
        q.add_task(task)

    total_duration = max([q.end_time for q in subcluster_event_queues])
    total_footprint = resource_limit * total_duration
    return {
        'nodes': resource_limit,
        'duration': total_duration,
        'resource_footprint': total_footprint,
        'task_footprint': task_footprint(task_list),
        'efficiency': efficiency(task_list, total_duration, resource_limit)
    }