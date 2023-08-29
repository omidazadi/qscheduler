from core import Core
from ptask import PTask

class PTaskStat:
    def __init__(self, id, ins_count, period, priority, no_tasks, missed_tasks, delayed_tasks, avg_execution_time, 
                 avg_waiting_time, avg_slack_time, avg_response_time, processing_core):
        self.id = id
        self.ins_count = ins_count
        self.period = period
        self.priority = priority
        self.no_tasks = no_tasks
        self.missed_tasks = missed_tasks
        self.delayed_tasks = delayed_tasks
        self.avg_execution_time = avg_execution_time
        self.avg_waiting_time = avg_waiting_time
        self.avg_slack_time = avg_slack_time
        self.avg_response_time = avg_response_time
        self.processing_core = processing_core
    
    @staticmethod
    def extract_ptask_stats(cores: list[Core], second_slice_size):
        ptasks: list[PTask] = []
        for core in cores:
            for ptask in core.ptasks:
                ptasks.append(ptask)
        temp_stats = [{ 'number-of-tasks': 0, 
                        'missed-tasks': 0,
                        'delayed-tasks': 0,
                        'total-execution-time': 0,
                        'total-waiting-time': 0,
                        'total-slack-time': 0,
                        'total-response-time': 0,
                        'processing-core': ''} for i in range(len(ptasks))]
        for core in cores:
            for ptask in core.ptasks:
                temp_stats[ptask.id - 1]['processing-core'] = core.get_full_name()
        
        for core in cores:
            for task in core.scheduled_tasks:
                temp_stats[task.ptask_id - 1]['number-of-tasks'] += 1
                temp_stats[task.ptask_id - 1]['delayed-tasks'] += (task.is_delayed)
                temp_stats[task.ptask_id - 1]['total-execution-time'] += (task.finish_time - task.start_time) / second_slice_size
                temp_stats[task.ptask_id - 1]['total-waiting-time'] += (task.start_time - task.arrival_time) / second_slice_size
                temp_stats[task.ptask_id - 1]['total-slack-time'] += (task.deadline - task.finish_time) / second_slice_size
                temp_stats[task.ptask_id - 1]['total-response-time'] += (task.finish_time - task.arrival_time) / second_slice_size
            for task in core.missed_tasks:
                temp_stats[task.ptask_id - 1]['number-of-tasks'] += 1
                temp_stats[task.ptask_id - 1]['missed-tasks'] += 1
        
        ptask_stats: list[PTaskStat] = []
        for ptask in ptasks:
            no_scheduled_tasks = temp_stats[ptask.id - 1]['number-of-tasks'] - temp_stats[ptask.id - 1]['missed-tasks']
            if no_scheduled_tasks > 0:
                ptask_stat = PTaskStat(ptask.id, ptask.ins_count, ptask.period / second_slice_size, ptask.priority, temp_stats[ptask.id - 1]['number-of-tasks'],
                                       temp_stats[ptask.id - 1]['missed-tasks'], temp_stats[ptask.id - 1]['delayed-tasks'], 
                                       temp_stats[ptask.id - 1]['total-execution-time'] / no_scheduled_tasks,
                                       temp_stats[ptask.id - 1]['total-waiting-time'] / no_scheduled_tasks,
                                       temp_stats[ptask.id - 1]['total-slack-time'] / no_scheduled_tasks,
                                       temp_stats[ptask.id - 1]['total-response-time'] / no_scheduled_tasks,
                                       temp_stats[ptask.id - 1]['processing-core'])
                ptask_stats.append(ptask_stat)
            else:
                ptask_stat = PTaskStat(ptask.id, ptask.ins_count, ptask.period / second_slice_size, ptask.priority, temp_stats[ptask.id - 1]['number-of-tasks'],
                                       temp_stats[ptask.id - 1]['missed-tasks'], temp_stats[ptask.id - 1]['delayed-tasks'], None, None, None, None,
                                       temp_stats[ptask.id - 1]['processing-core'])
                ptask_stats.append(ptask_stat)
                
        return ptask_stats
    
    @staticmethod
    def ptask_stat_to_dict(ptask_stat):
        return {
            'id': ptask_stat.id,
            'instruction-count': ptask_stat.ins_count,
            'period': ptask_stat.period,
            'priority': ptask_stat.priority,
            'number-of-tasks': ptask_stat.no_tasks,
            'missed-tasks': ptask_stat.missed_tasks,
            'delayed-tasks': ptask_stat.delayed_tasks,
            'average-execution-time': ptask_stat.avg_execution_time,
            'average-waiting-time': ptask_stat.avg_waiting_time,
            'average-slack-time': ptask_stat.avg_slack_time,
            'average-response-time': ptask_stat.avg_response_time,
            'processing-core': ptask_stat.processing_core
        }
    
    @staticmethod
    def priority_short_form(priority):
        if priority == 'hard':
            return 'H'
        elif priority == 'soft':
            return 'S'
        else:
            return 'F'