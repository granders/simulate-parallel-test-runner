
class Task(object):
    def __init__(self, length_seconds, resource_usage):
        self.duration = length_seconds
        self.resource = resource_usage

    def __repr__(self):
        return '<Task: duration: %s, resource: %s>' % (self.duration, self.resource)


class StartEvent(object):
    def __init__(self, event_time, task):
        self.time = event_time
        self.task = task

    def __repr__(self):
        return '<StartEvent: time: %s, task: %s>' % (str(self.time), str(self.task))


class EndEvent(object):
    def __init__(self, event_time, task):
        self.time = event_time
        self.task = task

    def __repr__(self):
        return '<EndEvent: time: %s, task: %s>' % (str(self.time), str(self.task))


class Resource(object):
    def __init__(self, limit):
        self.max_available = limit
        self.available = limit

    def allocate(self, n):
        assert n <= self.available
        self.available -= n

    def free(self, n):
        assert n <= self.max_available - self.available
        self.available += n


# def load_tasks(json_file):
#     with open(json_file, 'r') as f:
#         test_list = json.load(f)
#     return [Task(t['run_time_seconds'], t['nodes']) for t in test_list]
#
#
# def load_tasks_and_shuffle(json_file):
#     task_list = load_tasks(json_file)
#     random.shuffle(task_list)
#     return task_list
#
#
# def resource_footprint(resource_limit, duration):
#     """The resource footprint is resource_limit * time spent using those resources
#     """
#     # The elapsed time is the timestamp of the very last moment
#     return resource_limit * duration
#
#
# def task_footprint(task_list):
#     return sum([t.duration * t.resource for t in task_list])
#
#
# def efficiency(task_list, duration, resource_limit):
#     return task_footprint(task_list) / float(resource_limit * duration)
#
#
