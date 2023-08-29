import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
from core import Core
from ptask_stat import PTaskStat

class Chart:
    def draw_core_timeline(self, cores: list[Core], second_slice_size, duration):
        no_ptasks = 0
        for core in cores:
            no_ptasks += len(core.ptasks)

        fig, ax = plt.subplots()
        fig.set_size_inches((8, 6))
        fig.subplots_adjust(left=0.15, right=0.95, top=0.90, bottom=0.10)
        ax.set_title('Timeline of Cores')
        ax.set_xlabel('Time(s)')
        ax.set_ylabel('Processor')
        ax.set_xticks([i * duration / 5 for i in range(0, 6)], [i * duration / 5 for i in range(0, 6)])
        ax.set_yticks([1.25 + i for i in range(len(cores))], [core.get_full_name() for core in cores], fontsize=7.0)

        for i in range(len(cores)):
            for task in cores[i].scheduled_tasks:
                if task.start_time != -1:
                    ax.broken_barh(xranges=[(task.start_time / second_slice_size, (task.finish_time - task.start_time) / second_slice_size)], 
                                    yrange=(i + 1, 0.5,), facecolor=hsv_to_rgb(((task.ptask_id / no_ptasks), 0.5, 1.0)))

        return fig
    
    def draw_ptask_schedulability(self, ptask_stats: list[PTaskStat]):
        ptask_stats = sorted(ptask_stats, key=lambda x: x.id)

        fig, ax = plt.subplots()
        fig.set_size_inches((8, 6))
        fig.subplots_adjust(left=0.10, right=0.90, top=0.90, bottom=0.10)
        ax.set_title('Schedulability of Priodic Tasks')
        ax.set_xlabel('Priodic Task')
        ax.set_ylabel('Percentage')
        ax.set_xticks([ptask_stat.id for ptask_stat in ptask_stats], 
                      [f'{ptask_stat.id}{PTaskStat.priority_short_form(ptask_stat.priority)}' for ptask_stat in ptask_stats])
        ax.set_yticks([10 * i for i in range(11)], [10 * i for i in range(11)])

        ptask_ids = [ptask_stat.id for ptask_stat in ptask_stats]
        scheduled_percentages = [100 * (ptask_stats[i].no_tasks - ptask_stats[i].missed_tasks - ptask_stats[i].delayed_tasks) / ptask_stats[i].no_tasks 
                                 for i in range(len(ptask_stats))]
        delayed_percentages = [100 * ptask_stats[i].delayed_tasks / ptask_stats[i].no_tasks for i in range(len(ptask_stats))]
        missed_percentages = [100 * ptask_stats[i].missed_tasks / ptask_stats[i].no_tasks for i in range(len(ptask_stats))]
        bottom = [0 for i in range(len(ptask_stats))]

        ax.bar(ptask_ids, scheduled_percentages, label='Scheduled', align='center', bottom=bottom, color=hsv_to_rgb((0.3, 0.5, 1.0)))
        bottom = [bottom[i] + scheduled_percentages[i] for i in range(len(bottom))]
        ax.bar(ptask_ids, delayed_percentages, label='Delayed', align='center', bottom=bottom, color=hsv_to_rgb((0.51, 0.5, 1.0)))
        bottom = [bottom[i] + delayed_percentages[i] for i in range(len(bottom))]
        ax.bar(ptask_ids, missed_percentages, label='Missed', align='center', bottom=bottom, color=hsv_to_rgb((0.0, 0.5, 1.0)))
        bottom = [bottom[i] + missed_percentages[i] for i in range(len(bottom))]
        ax.legend()

        return fig
    
    def draw_ptask_timing(self, ptask_stats: list[PTaskStat]):
        ptask_stats = sorted(ptask_stats, key=lambda x: x.id)

        fig, ax = plt.subplots()
        fig.set_size_inches((8, 6))
        fig.subplots_adjust(left=0.10, right=0.90, top=0.90, bottom=0.10)
        ax.set_title('Timing of Priodic Tasks')
        ax.set_xlabel('Priodic Task')
        ax.set_ylabel('Time(s)')
        width = 0.1
        ax.set_xticks([ptask_stat.id for ptask_stat in ptask_stats], 
                      [f'{ptask_stat.id}{PTaskStat.priority_short_form(ptask_stat.priority)}' for ptask_stat in ptask_stats])

        ax.bar([i - 2 * width + 1 for i in range(len(ptask_stats))], [ptask_stat.avg_waiting_time for ptask_stat in ptask_stats], 
               width=width, label='Avg. Waiting Time', color=hsv_to_rgb((0.0, 0.5, 1.0)))
        ax.bar([i - width + 1 for i in range(len(ptask_stats))], [ptask_stat.avg_response_time for ptask_stat in ptask_stats], 
               width=width, label='Avg. Response Time', color=hsv_to_rgb((0.2, 0.5, 1.0)))
        ax.bar([i + 1 for i in range(len(ptask_stats))], [ptask_stat.avg_slack_time for ptask_stat in ptask_stats], 
               width=width, label='Avg. Slack Time', color=hsv_to_rgb((0.4, 0.5, 1.0)))
        ax.bar([i + width + 1 for i in range(len(ptask_stats))], [ptask_stat.avg_execution_time for ptask_stat in ptask_stats], 
               width=width, label='Avg. Execution Time', color=hsv_to_rgb((0.6, 0.5, 1.0)))
        ax.bar([i + 2 * width + 1 for i in range(len(ptask_stats))], [ptask_stat.period for ptask_stat in ptask_stats], 
               width=width, label='Period', color=hsv_to_rgb((0.8, 0.5, 1.0)))
        ax.legend()

        return fig
