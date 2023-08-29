from task import Task

class QState:
    def __init__(self, time: int, task_num: int, dvfs_level: int, dvfs_lock_from: int, consumed_energy: int, delayed: tuple[int]):
        self.time = time
        self.task_num = task_num
        self.dvfs_level = dvfs_level
        self.dvfs_lock_from = dvfs_lock_from
        self.consumed_energy = consumed_energy
        self.delayed = delayed

    def __hash__(self):
        return hash((self.time, self.task_num, self.delayed, self.dvfs_level, self.dvfs_lock_from, self.consumed_energy,))

    def __eq__(self, other):
        return ((self.time, self.task_num, self.delayed, self.dvfs_level, self.dvfs_lock_from, self.consumed_energy,) == 
                (other.time, other.task_num, other.delayed, other.dvfs_level, other.dvfs_lock_from, other.consumed_energy,))

    def __ne__(self, other):
        return not self.__eq__(self, other)
    
    def __str__(self):
        return f'QState - time: {self.time}, task number: {self.task_num}, dvfs level: {self.dvfs_level}, dvfs lock from: {self.dvfs_lock_from}, consumed energy: {self.consumed_energy}, delayed queue: {self.delayed}'