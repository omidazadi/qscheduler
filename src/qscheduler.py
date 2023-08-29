import random
from core import Core
from ptask import PTask
from task import Task
from qstate import QState

class QScheduler:
    def __init__(self, mapping_algorithm, learning_rate, exploration_prob, exploration_decay, episodes, soft_schedule_reward, 
                 soft_delay_reward, soft_miss_penalty, firm_schedule_reward, firm_miss_penalty, dvfs_up_reward, dvfs_down_reward, 
                 finish_reward, retry, second_slice_size):
        self.mapping_algorithm = mapping_algorithm
        self.learning_rate = learning_rate
        self.exploration_prob = exploration_prob
        self.exploration_decay = exploration_decay
        self.episodes = episodes
        self.soft_schedule_reward = soft_schedule_reward
        self.soft_delay_reward = soft_delay_reward
        self.soft_miss_penalty = soft_miss_penalty
        self.firm_schedule_reward = firm_schedule_reward
        self.firm_miss_penalty = firm_miss_penalty
        self.dvfs_up_reward = dvfs_up_reward
        self.dvfs_down_reward = dvfs_down_reward
        self.finish_reward = finish_reward
        self.retry = retry
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
        retries, tasks = 0, self.extract_tasks_from_ptasks(core.ptasks, duration)
        while True:
            try:
                qtable = self.learn_qtable(core, tasks, duration)
                self.schedule_with_qtable(core, tasks, qtable, duration)
                return
            except ValueError as e:
                retries += 1
                if retries == self.retry:
                    raise e

    def learn_qtable(self, core: Core, tasks: list[Task], duration: int):
        qtable, exploration_prob = {}, self.exploration_prob
        for episode in range(self.episodes):
            Task.reset(tasks)
            core.reset()
            qstate, terminated = QState(0, 0, core.dvfs_level, 0, 0, ()), False
            self.add_qstate_to_qtable(qstate, qtable, tasks, core, duration)
            while not terminated:
                (qstate, terminated,) = self.learning_step(qstate, qtable, tasks, core, duration, exploration_prob)
            exploration_prob *= self.exploration_decay
        return qtable

    def schedule_with_qtable(self, core: Core, tasks: list[Task], qtable: dict[QState, dict], duration: int):
        Task.reset(tasks)
        core.reset()
        qstate, terminated = QState(0, 0, core.dvfs_level, 0, 0, ()), False
        self.add_qstate_to_qtable(qstate, qtable, tasks, core, duration)
        while not terminated:
            (qstate, terminated,) = self.solution_step(qstate, qtable, tasks, core, duration)
        
        if not 'finished' in qtable[qstate]:
            raise ValueError('Scheduling failed.')

    def learning_step(self, qstate: QState, qtable: dict[QState, dict], tasks: list[Task], core: Core, duration: int, exploration_prob: float):
        if 'failure' in qtable[qstate]:
            return qstate, True
        if 'finished' in qtable[qstate]:
            return qstate, True

        action = None
        if random.uniform(0, 1) < exploration_prob:
            action = random.choice(list(qtable[qstate].keys()))
        else:
            action = self.max_qvalue_action(qstate, qtable)
        
        next_qstate = self.do_action(qstate, tasks, core, action, duration)
        self.add_qstate_to_qtable(next_qstate, qtable, tasks, core, duration)
        self.update_qtable(qstate, qtable, next_qstate, action)
        return next_qstate, False
    
    def solution_step(self, qstate: QState, qtable: dict[QState, dict], tasks: list[Task], core: Core, duration: int):
        if 'failure' in qtable[qstate]:
            return qstate, True
        if 'finished' in qtable[qstate]:
            return qstate, True

        action = self.max_qvalue_action(qstate, qtable)
        next_qstate = self.do_action(qstate, tasks, core, action, duration)
        self.add_qstate_to_qtable(next_qstate, qtable, tasks, core, duration)
        return next_qstate, False

    def add_qstate_to_qtable(self, qstate: QState, qtable: dict[QState, dict], tasks: list[Task], core: Core, duration: int):
        if qstate in qtable:
            return
        
        qtable[qstate] = {}
        if core.allowed_avg_power * duration < qstate.consumed_energy:
            qtable[qstate] = {'failure': {'qvalue': float('-inf'), 'reward': None}}
            return

        if len(qstate.delayed) == 0 and qstate.task_num == len(tasks):
            if qstate.time == duration * self.second_slice_size:
                qtable[qstate] = {'finished': {'qvalue': self.finish_reward, 'reward': None}}
                return
            else:
                qtable[qstate]['stall-to-finish'] = {'qvalue': 0, 'reward': 0}

                time_interval = core.dvfs_change_lock - (qstate.time - qstate.dvfs_lock_from)
                if time_interval > 0 and qstate.time + time_interval <= duration * self.second_slice_size:
                    qtable[qstate]['stall-to-dvfs-lock'] = {'qvalue': 0, 'reward': 0}
        
        if qstate.task_num < len(tasks):
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
                
            if tasks[qstate.task_num].priority == 'soft':
                qtable[qstate]['miss'] = {'qvalue': 0, 'reward': self.soft_miss_penalty}
            elif tasks[qstate.task_num].priority == 'firm':
                qtable[qstate]['miss'] = {'qvalue': 0, 'reward': self.firm_miss_penalty}
            
            if tasks[qstate.task_num].priority == 'soft':
                qtable[qstate]['delay'] = {'qvalue': 0, 'reward': self.soft_delay_reward}
        
        if len(qstate.delayed) > 0:
            if core.is_schedulable(tasks[qstate.delayed[0]]):
                qtable[qstate]['schedule-delayed'] = {'qvalue': 0, 'reward': 0}
            else:
                qtable[qstate] = {'failure': {'qvalue': float('-inf'), 'reward': None}}
                return

        if qstate.dvfs_level < len(core.dvfs_levels) - 1 and core.dvfs_change_lock + qstate.dvfs_lock_from <= qstate.time:
            qtable[qstate]['dvfs-up'] = {'qvalue': 0, 'reward': self.dvfs_up_reward}

        if qstate.dvfs_level > 0 and core.dvfs_change_lock + qstate.dvfs_lock_from <= qstate.time:
            qtable[qstate]['dvfs-down'] = {'qvalue': 0, 'reward': self.dvfs_down_reward}
    
    def do_action(self, qstate: QState, tasks: list[Task], core: Core, action: str, duration: int):
        if action == 'schedule':
            task = tasks[qstate.task_num]
            energy_consumption = core.schedule(task)
            return QState(task.finish_time, qstate.task_num + 1, qstate.dvfs_level, qstate.dvfs_lock_from, qstate.consumed_energy + energy_consumption, qstate.delayed)
        elif action == 'schedule-delayed':
            task = tasks[qstate.delayed[0]]
            energy_consumption = core.schedule(task)
            return QState(task.finish_time, qstate.task_num, qstate.dvfs_level, qstate.dvfs_lock_from, qstate.consumed_energy + energy_consumption, qstate.delayed[1:])
        elif action == 'miss':
            task = tasks[qstate.task_num]
            core.miss(task)
            return QState(qstate.time, qstate.task_num + 1, qstate.dvfs_level, qstate.dvfs_lock_from, qstate.consumed_energy, qstate.delayed)
        elif action == 'delay':
            return QState(qstate.time, qstate.task_num + 1, qstate.dvfs_level, qstate.dvfs_lock_from, qstate.consumed_energy, (*qstate.delayed, qstate.task_num,))
        elif action == 'dvfs-up':
            core.dvfs_up(qstate.time)
            return QState(qstate.time, qstate.task_num, qstate.dvfs_level + 1, qstate.time, qstate.consumed_energy, qstate.delayed)
        elif action == 'dvfs-down':
            core.dvfs_down(qstate.time)
            return QState(qstate.time, qstate.task_num, qstate.dvfs_level - 1, qstate.time, qstate.consumed_energy, qstate.delayed)
        elif action == 'stall-to-finish':
            energy_consumption = core.stall(duration * self.second_slice_size - qstate.time)
            return QState(duration * self.second_slice_size, qstate.task_num, qstate.dvfs_level, qstate.dvfs_lock_from, 
                          qstate.consumed_energy + energy_consumption, qstate.delayed)
        else:
            time_interval = core.dvfs_change_lock - (qstate.time - qstate.dvfs_lock_from)
            energy_consumption = core.stall(time_interval)
            return QState(qstate.time + time_interval, qstate.task_num, qstate.dvfs_level, qstate.dvfs_lock_from, 
                          qstate.consumed_energy + energy_consumption, qstate.delayed)
        
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