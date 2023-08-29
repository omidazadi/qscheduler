import math
from ptask import PTask
from task import Task

class Core:
    def __init__(self, name, core_id, cpi, one_ghz_power, dvfs_change_lock, dvfs_levels, default_dvfs_level, 
                 allowed_avg_power, second_slice_size):
        self.name = name
        self.core_id = core_id
        self.cpi = cpi
        self.one_ghz_power = one_ghz_power
        self.dvfs_change_lock = dvfs_change_lock * second_slice_size
        self.dvfs_levels = dvfs_levels
        self.default_dvfs_level = default_dvfs_level
        self.dvfs_lock_from = 0
        self.dvfs_level = len(self.dvfs_levels) - 1
        self.allowed_avg_power = allowed_avg_power
        self.second_slice_size = second_slice_size
        self.available_resource = self.default_instruction_per_time_unit()
        self.ptasks: list[PTask] = []
        self.scheduled_tasks: list[Task] = []
        self.missed_tasks: list[Task] = []
        self.freq_history = [(0, self.dvfs_levels[self.dvfs_level])]
        self.energy_history = [(0, 0)]

    def default_instruction_per_time_unit(self):
        return (self.dvfs_levels[self.default_dvfs_level] * (1000_000_000 / self.second_slice_size)) / self.cpi
    
    def instruction_per_time_unit(self):
        return (self.dvfs_levels[self.dvfs_level] * (1000_000_000 / self.second_slice_size)) / self.cpi

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
        energy_consumption = self.energy_consumption(task.finish_time - last_finish_time)
        self.energy_history.append((task.finish_time / self.second_slice_size, self.energy_history[-1][1] + energy_consumption))
        self.freq_history.append((task.finish_time / self.second_slice_size, self.dvfs_levels[self.dvfs_level]))
        return energy_consumption
    
    def stall(self, time_interval):
        energy_consumption = self.energy_consumption(time_interval)
        self.energy_history.append((self.energy_history[-1][0] + time_interval / self.second_slice_size, self.energy_history[-1][1] + energy_consumption))
        self.freq_history.append((self.freq_history[-1][0] + time_interval / self.second_slice_size, self.dvfs_levels[self.dvfs_level]))
        return energy_consumption

    def energy_consumption(self, time_interval):
        return math.floor((time_interval / self.second_slice_size) * (self.dvfs_levels[self.dvfs_level] ** 3) * self.one_ghz_power)

    def miss(self, task: Task):
        self.missed_tasks.append(task)

    def dvfs_up(self, time):
        self.dvfs_lock_from = time
        self.dvfs_level += 1
    
    def dvfs_down(self, time):
        self.dvfs_lock_from = time
        self.dvfs_level -= 1

    def reset(self):
        self.dvfs_level = len(self.dvfs_levels) - 1
        self.scheduled_tasks = []
        self.missed_tasks = []
        self.freq_history = [(0, self.dvfs_levels[self.dvfs_level])]
        self.energy_history = [(0, 0)]

    def get_full_name(self):
        return f'{self.name} / {self.core_id}' 
