import math
import random
from uunifast import generate_uunifastdiscard
from ptask import PTask

class PTaskGenerator:
    def generate(self, task_set_size, utilization, total_cpu_resource, periods, 
                 second_slice_size) -> list[PTask]:
        task_set, ptasks, next_id = generate_uunifastdiscard(1, utilization, task_set_size)[0], [], 1
        for u in task_set:
            period_segment = random.choice(list(periods.values()))
            period = math.floor(random.uniform(*period_segment) * second_slice_size)
            priority = random.choice(['hard', 'firm', 'soft'])
            ptasks.append(PTask(next_id, math.floor(u * total_cpu_resource * period), period, priority))
            next_id += 1
        return ptasks