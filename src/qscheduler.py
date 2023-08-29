import random
from core import Core
from ptask import PTask
from task import Task
from qstate import QState

class QScheduler:
    def __init__(self, mapping_algorithm, learning_rate, exploration_prob, episodes, soft_schedule_reward, 
                 soft_delay_reward, firm_schedule_reward, second_slice_size):
        self.mapping_algorithm = mapping_algorithm
        self.learning_rate = learning_rate
        self.exploration_prob = exploration_prob
        self.episodes = episodes
        self.soft_schedule_reward = soft_schedule_reward
        self.soft_delay_reward = soft_delay_reward
        self.firm_schedule_reward = firm_schedule_reward
        self.second_slice_size = second_slice_size

    def map_ptasks_to_cores(self, cores: list[Core], ptasks: list[PTask]):
        if self.mapping_algorithm == 'worst-fit':
            for ptask in ptasks:
                candidate_core: Core = None
                for core in cores:
                    if (core.available_resource >= ptask.needed_resource() and 
                        (candidate_core == None or core.available_resource > candidate_core.available_resource)):
                        candidate_core = core
                if candidate_core == None:
                    raise ValueError('Core mapping failed.')
                candidate_core.add_ptask(ptask)

        else:
            raise ValueError('Core mapping algorithm is not supported.')
        
    def schedule(self, core: Core, duration):
        tasks = self.extract_tasks_from_ptasks(core.ptasks, duration)
        qtable = self.learn_qtable(core, tasks)
        self.schedule_with_qtable(core, tasks, qtable)

    def learn_qtable(self, core: Core, tasks: list[Task]):
        qtable = {}
        for episode in range(self.episodes):
            core.reset_core()
            qstate = QState(0, 0, ())
            self.add_qstate_to_qtable(qstate, qtable, tasks, core)
            (qstate, terminated,) = self.learning_step(qstate, qtable, tasks, core)
            while not terminated:
                (qstate, terminated,) = self.learning_step(qstate, qtable, tasks, core)
        return qtable

    def schedule_with_qtable(self, core: Core, tasks: list[Task], qtable: dict[QState, dict]):
        core.reset_core()
        qstate = QState(0, 0, ())
        self.add_qstate_to_qtable(qstate, qtable, tasks, core)
        (qstate, terminated,) = self.solution_step(qstate, qtable, tasks, core)
        while not terminated:
            (qstate, terminated,) = self.solution_step(qstate, qtable, tasks, core)
        
        if not 'finished' in qtable[qstate]:
            raise ValueError('Scheduling failed.')

    def learning_step(self, qstate: QState, qtable: dict[QState, dict], tasks: list[Task], core: Core):
        if 'failure' in qtable[qstate]:
            return qstate, True
        if 'finished' in qtable[qstate]:
            return qstate, True

        action = None
        if random.uniform(0, 1) < self.exploration_prob:
            action = random.choice(list(qtable[qstate].keys()))
        else:
            action = self.max_qvalue_action(qstate, qtable)
        
        next_qstate = self.do_action(qstate, tasks, core, action)
        self.add_qstate_to_qtable(next_qstate, qtable, tasks, core)
        self.update_qtable(qstate, qtable, next_qstate, action)
        return next_qstate, False
    
    def solution_step(self, qstate: QState, qtable: dict[QState, dict], tasks: list[Task], core: Core):
        if 'failure' in qtable[qstate]:
            return qstate, True
        if 'finished' in qtable[qstate]:
            return qstate, True

        action = self.max_qvalue_action(qstate, qtable)
        next_qstate = self.do_action(qstate, tasks, core, action)
        self.add_qstate_to_qtable(next_qstate, qtable, tasks, core)
        return next_qstate, False

    def add_qstate_to_qtable(self, qstate: QState, qtable: dict[QState, dict], tasks: list[Task], core: Core):
        if qstate in qtable:
            return
        
        qtable[qstate] = {}
        if qstate.task_num == len(tasks):
            qtable[qstate] = {'finished': {'qvalue': 0, 'reward': None}}
            return
        
        if core.is_schedulable(tasks[qstate.task_num]):
            if tasks[qstate.task_num].priority == 'soft':
                qtable[qstate]['schedule'] = {'qvalue': 0, 'reward': self.soft_schedule_reward}
            elif tasks[qstate.task_num].priority == 'firm':
                qtable[qstate]['schedule'] = {'qvalue': 0, 'reward': self.firm_schedule_reward}
            else:
                qtable[qstate]['schedule'] = {'qvalue': 0, 'reward': 0}
        else:
            if tasks[qstate.task_num].priority == 'hard':
                qtable[qstate] = {'failure': {'qvalue': float('-inf'), 'reward': None}}
                return
        
        if len(qstate.delayed) > 0:
            if core.is_schedulable(tasks[qstate.delayed[0]]):
                qtable[qstate]['schedule-delayed'] = {'qvalue': 0, 'reward': 0}
            else:
                qtable[qstate] = {'failure': {'qvalue': float('-inf'), 'reward': None}}
                return
        
        if tasks[qstate.task_num].priority != 'hard':
            qtable[qstate]['miss'] = {'qvalue': 0, 'reward': 0}
        
        if tasks[qstate.task_num].priority == 'soft':
            qtable[qstate]['delay'] = {'qvalue': 0, 'reward': self.soft_delay_reward}
    
    def do_action(self, qstate: QState, tasks: list[Task], core: Core, action: str):
        if action == 'schedule':
            task = tasks[qstate.task_num]
            core.schedule(task)
            return QState(task.finish_time, qstate.task_num + 1, qstate.delayed)
        elif action == 'schedule-delayed':
            task = tasks[qstate.delayed[0]]
            core.schedule(task)
            return QState(task.finish_time, qstate.task_num, qstate.delayed[1:])
        elif action == 'miss':
            task = tasks[qstate.task_num]
            core.miss(task)
            return QState(qstate.time, qstate.task_num + 1, qstate.delayed)
        else:
            return QState(qstate.time, qstate.task_num + 1, (*qstate.delayed, qstate.task_num,))
        
    def update_qtable(self, qstate: QState, qtable: dict[QState, dict], next_qstate: QState, action: str):
        qtable[qstate][action]['qvalue'] = ((1 - self.learning_rate) * qtable[qstate][action]['qvalue'] + 
                                            self.learning_rate * (qtable[qstate][action]['reward'] + 
                                                                  qtable[next_qstate][self.max_qvalue_action(next_qstate, qtable)]['qvalue']))
        
    def max_qvalue_action(self, qstate: QState, qtable: dict[QState, dict]):
        candidate_action, candidate_qvalue = None, None
        for action in qtable[qstate]:
            if candidate_action == None or (qtable[qstate][action]['qvalue'] > candidate_qvalue):
                candidate_action = action
                candidate_qvalue = qtable[qstate][action]['qvalue']
        return candidate_action

    def extract_tasks_from_ptasks(self, ptasks: list[PTask], duration) -> list[Task]:
        tasks: list[Task] = []
        for ptask in ptasks:
            t = 0
            while t + ptask.period < duration * self.second_slice_size:
                tasks.append(Task(ptask.id, ptask.ins_count, t, t + ptask.period, ptask.priority))
                t += ptask.period
        tasks = sorted(tasks, key=lambda x: x.deadline)
        return tasks