from simulate_parallel_runner.task import Task
from simulate_parallel_runner.schedulers.on_demand_scheduler import simulate_better_on_demand_scheduler
from simulate_parallel_runner.schedulers.partitioned_cluster import simulate_partitioned_cluster_scheduler

import json
import random


def load_tasks(json_file):
    with open(json_file, 'r') as f:
        test_list = json.load(f)
    return [Task(t['run_time_seconds'], t['nodes']) for t in test_list]


def load_tasks_and_shuffle(json_file, seed=None):

    if seed is not None:
        random.seed(seed)
    task_list = load_tasks(json_file)
    random.shuffle(task_list)
    return task_list


def resource_footprint(resource_limit, duration):
    """The resource footprint is resource_limit * time spent using those resources
    """
    # The elapsed time is the timestamp of the very last moment
    return resource_limit * duration


def task_footprint(task_list):
    return sum([t.duration * t.resource for t in task_list])


def efficiency(task_list, duration, resource_limit):
    return task_footprint(task_list) / float(resource_limit * duration)


def simulate(task_list, scheduler_simulator):
    serial_duration = sum(t.duration for t in task_list) / 60.0

    nodes = []
    wallclock = []
    parallelism = []
    resource_efficiency = []

    for n in range(20, 201, 10):
        x = scheduler_simulator(task_list, n)
        x['duration'] = x['duration'] / 60.0
        x['parallelism'] = serial_duration / x['duration']
        nodes.append(n)
        wallclock.append(x['duration'])
        parallelism.append(x['parallelism'])
        resource_efficiency.append(x['efficiency'])

    if scheduler_simulator == simulate_better_on_demand_scheduler:
        scheduler = "on_demand"
    else:
        scheduler = "partitioned_subcluster"

    return {
        "num_tests": len(task_list),
        "serial_duration": serial_duration,
        "scheduler": scheduler,
        "nodes": nodes,
        "wallclock": wallclock,
        "parallelism": parallelism,
        "resource_efficiency": resource_efficiency
    }


def main():
    TASK_LIST_SOURCE = 'simulate_parallel_runner/resources/kafkatest.json'

    results = []
    seed = 12345
    simulators = [simulate_better_on_demand_scheduler, simulate_partitioned_cluster_scheduler]
    for scheduler_simulator in simulators:

        for task_multiplier in [1, 2, 4]:
            task_list = load_tasks_and_shuffle(TASK_LIST_SOURCE, seed=seed) * task_multiplier
            # print len(task_list)
            results.append(simulate(task_list, scheduler_simulator))

    print json.dumps(results, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    main()

"""
questions we can ask for a given scheduling strategy:
- what cluster size gives us the maximum efficiency?
    - what about if we factor in cluster start up time?
- how big does the cluster need to be to get an N-fold speedup?
    - what about if we factor in cluster start up time?
    - keeping in mind the speedup can't be better than max([task.duration]) / sum([task.duration])

"""
