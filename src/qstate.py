from task import Task

class QState:
    def __init__(self, time: int, task_num: int, delayed: tuple[int]):
        self.time = time
        self.task_num = task_num
        self.delayed = delayed

    def __hash__(self):
        return hash((self.time, self.task_num, self.delayed,))

    def __eq__(self, other):
        return (self.time, self.task_num, self.delayed,) == (other.time, other.task_num, other.delayed,)
    
    def __ne__(self, other):
        return not self.__eq__(self, other)
    
    def __str__(self):
        return f'QState - time: {self.time}, task number: {self.task_num}, delayed queue: {self.delayed}'