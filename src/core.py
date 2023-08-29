import math
from ptask import PTask
from task import Task

class Core:
    def __init__(self, name, core_id, cpi, one_ghz_power, dvfs_levels, allowed_avg_power, second_slice_size):
        self.name = name
        self.core_id = core_id
        self.cpi = cpi
        self.one_ghz_power = one_ghz_power
        self.dvfs_levels = dvfs_levels
        self.allowed_avg_power = allowed_avg_power
        self.second_slice_size = second_slice_size
        self.dvfs_level = self.dvfs_levels[-1]
        self.available_resource = self.instruction_per_time_unit()
        self.ptasks: list[PTask] = []
        self.scheduled_tasks: list[Task] = []
        self.missed_tasks: list[Task] = []

    def instruction_per_time_unit(self):
        return (self.dvfs_level * (1000_000_000 / self.second_slice_size)) / self.cpi

    def add_ptask(self, ptask: PTask):
        self.ptasks.append(ptask)
        self.available_resource -= ptask.needed_resource()

    def is_schedulable(self, task: Task):
        final_deadline = (task.deadline if not task.is_delayed else task.deadline + (task.deadline - task.arrival_time))
        last_finish_time = (0 if len(self.scheduled_tasks) == 0 else self.scheduled_tasks[-1].finish_time)
        execution_time = math.floor(task.ins_count / self.instruction_per_time_unit())
        return max(task.arrival_time, last_finish_time) + execution_time <= final_deadline
    
    def schedule(self, task: Task):
        last_finish_time = (0 if len(self.scheduled_tasks) == 0 else self.scheduled_tasks[-1].finish_time)
        execution_time = math.floor(task.ins_count / self.instruction_per_time_unit())
        task.start_time = max(task.arrival_time, last_finish_time)
        task.finish_time = task.start_time + execution_time
        self.scheduled_tasks.append(task)

    def miss(self, task: Task):
        self.missed_tasks.append(task)

    def reset_core(self):
        self.scheduled_tasks = []
        self.missed_tasks = []

    def get_full_name(self):
        return f'{self.name} / {self.core_id}' 
