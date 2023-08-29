class Task:
    def __init__(self, ptask_id, ins_count, arrival_time, deadline, priority):
        self.ptask_id = ptask_id
        self.ins_count = ins_count
        self.arrival_time = arrival_time
        self.deadline = deadline
        self.priority = priority
        self.start_time = -1
        self.finish_time = -1
        self.is_delayed = False

    def __str__(self):
        return f'Task - ptask id: {self.ptask_id}, instruction count: {self.ins_count}, arrival time: {self.arrival_time}, deadline: {self.deadline}, priority: {self.priority}, start time: {self.start_time}, finish time: {self.finish_time}'
    
    def delay(self):
        self.is_delayed = True

    @staticmethod
    def reset(tasks):
        for task in tasks:
            task.start_time = -1
            task.finish_time = -1
            task.is_delayed = False