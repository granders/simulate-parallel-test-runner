

"""
Tools for measuring how well schedulers do their thing
"""


def resource_footprint(resource_limit, duration):
    """The resource footprint is resource_limit * time spent using those resources
    """
    # The elapsed time is the timestamp of the very last moment
    return resource_limit * duration


def task_footprint(task_list):
    return sum([t.duration * t.resource for t in task_list])


def efficiency(task_list, duration, resource_limit):
    return task_footprint(task_list) / float(resource_limit * duration)
