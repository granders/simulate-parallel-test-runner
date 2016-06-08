import json
import random

from simulate_parallel_runner.task import Resource, Task, StartEvent, EndEvent

"""
The idea is to not limit the number of threads (or maybe have a high bound), but instead start up each test in a
separate thread(process?) so long as cluster resources are available to do so.

An on-demand scheduler needs accurate information about cluster usage of each test.
We also have to handle when this is wrong... How would we handle this?
- Some service will raise an exception when it is instantiated (give this a specific exception for easy detection?)
- Strategy 1: fail the test outright
- Strategy 2: re-enqueue the test, but double the number of nodes in the resource hint?

We might want multiple different kinds of resource hints? In that case we can constrain total usage in the same way.
Each additional constraint will potentially further limit parallelism.
- Cluster
- Memory

Keep track of max parallelism?
It would be nice to draw a picture of what the resulting schedule looks like
"""


class Moment(object):
    """A moment is a 'cell' in which one or more events 'simultaneously' occur"""
    def __init__(self, moment_time, start_events=tuple(), end_events=tuple()):
        self.time = moment_time
        self.start_events = [e for e in start_events]
        self.end_events = [e for e in end_events]

    def __repr__(self):
        return "<Moment: time: %s, start_events: %s, end_events: %s>" % (self.time, self.start_events, self.end_events)

    def add_start_event(self, start_event):
        assert start_event.time == self.time
        self.start_events.append(start_event)

    def add_end_event(self, end_event):
        assert end_event.time == self.time
        self.end_events.append(end_event)


def resource_footprint(resource_limit, duration):
    """The resource footprint is resource_limit * time spent using those resources
    """
    # The elapsed time is the timestamp of the very last moment
    return resource_limit * duration


def task_footprint(task_list):
    return sum([t.duration * t.resource for t in task_list])


def efficiency(task_list, duration, resource_limit):
    return task_footprint(task_list) / float(resource_limit * duration)



# def simulate_on_demand_scheduler(task_list, resource_limit):
#     """
#     Logical time
#     start event in the same 'moment' slot as an end event occurs just after the end event
#
#     """
#     resource_state = Resource(resource_limit)
#     moment_list = [Moment(0)]
#     moment_index = 0
#     timestamp = 0
#     task_list_copy = task_list[:]
#     while len(task_list_copy) > 0:
#         task = task_list_copy.pop()
#
#         # advance moment index until we can run the current task
#         while resource_state.available < task.resource:
#             moment_index += 1
#             moment = moment_list[moment_index]
#             timestamp = moment.time
#             resource_state.available += sum([ee.task.resource for ee in moment.end_events])
#
#         # print moment_list
#         # print "INDEX: %d" % moment_index
#         # add task start event at the current moment
#         assert resource_state.available >= task.resource
#         moment = moment_list[moment_index]
#         moment.add_start_event(StartEvent(timestamp, task))
#         resource_state.available -= task.resource
#
#         # insert task end event
#         # search from the end of moment list to find the
#         # latest moment <= end event time
#         j = len(moment_list) - 1
#         assert task.duration > 0  # No instantaneous tasks
#         task_end_time = timestamp + task.duration
#         end_event = EndEvent(task_end_time, task)
#         while moment_list[j].time > task_end_time:
#             j -= 1
#
#         assert j >= moment_index
#         if task_end_time == moment_list[j].time:
#             # add end event to existing moment with matching timestamp
#             moment = moment_list[j]
#             moment.add_end_event(end_event)
#         else:
#             # task end time is greater than moment_list[j] but less than moment_list[j + 1] (if it exists)
#             # so we want to insert a new moment at index j+1
#             moment = Moment(task_end_time, end_events=(end_event,))
#             moment_list = moment_list[: j + 1] + [moment] + moment_list[j + 1:]
#
#     total_duration = moment_list[-1:][0].time
#     total_footprint = resource_limit * total_duration
#     return {
#         'nodes': resource_limit,
#         'duration': total_duration,
#         'resource_footprint': total_footprint,
#         'task_footprint': task_footprint(task_list),
#         'efficiency': efficiency(task_list, total_duration, resource_limit)
#     }


def simulate_better_on_demand_scheduler(task_list, resource_limit):
    """
    Logical time
    start event in the same 'moment' slot as an end event occurs just after the end event

    """
    resource_state = Resource(resource_limit)
    moment_list = [Moment(0)]
    moment_index = 0
    timestamp = 0
    task_list_copy = task_list[:]
    while len(task_list_copy) > 0:

        # find most resource-intensive task that will fit
        best_task = None
        largest_fitting_resource = 0
        for i, t in enumerate(task_list_copy):
            if largest_fitting_resource < t.resource <= resource_state.available:
                best_task = t
                largest_fitting_resource = t.resource

        if best_task is None:
            # If there is no task that will fit in the current moment, just pop
            task = task_list_copy.pop()
        else:
            task = best_task
            task_list_copy.remove(best_task)

        # advance moment index until we can run the current task
        while resource_state.available < task.resource:
            moment_index += 1
            moment = moment_list[moment_index]
            timestamp = moment.time
            resource_state.available += sum([ee.task.resource for ee in moment.end_events])

        # print moment_list
        # print "INDEX: %d" % moment_index
        # add task start event at the current moment
        assert resource_state.available >= task.resource
        moment = moment_list[moment_index]
        moment.add_start_event(StartEvent(timestamp, task))
        resource_state.available -= task.resource

        # insert task end event
        # search from the end of moment list to find the
        # latest moment <= end event time
        j = len(moment_list) - 1
        assert task.duration > 0  # No instantaneous tasks
        task_end_time = timestamp + task.duration
        end_event = EndEvent(task_end_time, task)
        while moment_list[j].time > task_end_time:
            j -= 1

        assert j >= moment_index
        if task_end_time == moment_list[j].time:
            # add end event to existing moment with matching timestamp
            moment = moment_list[j]
            moment.add_end_event(end_event)
        else:
            # task end time is greater than moment_list[j] but less than moment_list[j + 1] (if it exists)
            # so we want to insert a new moment at index j+1
            moment = Moment(task_end_time, end_events=(end_event,))
            moment_list = moment_list[: j + 1] + [moment] + moment_list[j + 1:]

    total_duration = moment_list[-1:][0].time
    total_footprint = resource_limit * total_duration
    return {
        'nodes': resource_limit,
        'duration': total_duration,
        'resource_footprint': total_footprint,
        'task_footprint': task_footprint(task_list),
        'efficiency': efficiency(task_list, total_duration, resource_limit)
    }

