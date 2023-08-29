import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
from core import Core

class Chart:
    def draw_core_timeline(self, cores: list[Core], second_slice_size, duration):
        no_ptasks = 0
        for core in cores:
            no_ptasks += len(core.ptasks)

        fig, gnt = plt.subplots()
        gnt.set_title('Timeline of Cores')
        gnt.set_xlabel('Time(s)')
        gnt.set_xticks([i * duration / 5 for i in range(0, 6)])
        gnt.set_xticklabels([i * duration / 5 for i in range(0, 6)])
        gnt.set_ylabel('Processor')
        gnt.set_yticks([1.25 + i for i in range(len(cores))])
        gnt.set_yticklabels([core.name for core in cores])

        for i in range(len(cores)):
            for task in cores[i].scheduled_tasks:
                if task.start_time != -1:
                    gnt.broken_barh(xranges=[(task.start_time / second_slice_size, (task.finish_time - task.start_time) / second_slice_size)], 
                                    yrange=(i + 1, 0.5,), facecolor=hsv_to_rgb(((task.ptask_id / no_ptasks), 0.5, 1.0)))
                    #xranges.append((task.start_time / second_slice_size, (task.finish_time - task.start_time) / second_slice_size))

        plt.show()
        