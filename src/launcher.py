import json
from core import Core
from ptask_generator import PTaskGenerator
from qscheduler import QScheduler
from chart import Chart

def print_core_mapping(cores: list[Core]):
    for core in cores:
        print(f'core: {core.name}')
        sum_ptask_resources = 0
        for ptask in core.ptasks:
            print(ptask)
            sum_ptask_resources += ptask.needed_resource()
        print('\n')

def launch():
    core_config = json.load(open('configs/core_config.json', 'r'))
    qscheduler_config = json.load(open('configs/qscheduler_config.json', 'r'))
    simulation_config = json.load(open('configs/simulation_config.json', 'r'))

    cores: list[Core] = []
    for core_name in simulation_config['cores']:
        for i in range(simulation_config['cores'][core_name]):
            cores.append(Core(core_name, core_config[core_name]['average-cpi'], core_config[core_name]['1-GHz-power-mW'], 
                              core_config[core_name]['dfvs-levels'], simulation_config['second-slice-size']))
            
    total_cpu_resource = 0
    for core in cores:
        total_cpu_resource += core.available_resource

    ptask_generator = PTaskGenerator()
    ptasks = ptask_generator.generate(simulation_config['task-set-size'], simulation_config['utilization'], total_cpu_resource,
                             simulation_config['task-periods'], simulation_config['second-slice-size'])
    
    qscheduler = QScheduler(qscheduler_config['mapping-algorithm'], qscheduler_config['learning-rate'], qscheduler_config['exploration-proboblity'],
                            qscheduler_config['episodes'], qscheduler_config['soft-schedule-reward'], qscheduler_config['soft-delay-reward'], 
                            qscheduler_config['firm-schedule-reward'], simulation_config['second-slice-size'])

    qscheduler.map_ptasks_to_cores(cores, ptasks)
    print_core_mapping(cores)

    for core in cores:
        qscheduler.schedule(core, simulation_config['duration'])
    
    chart = Chart()
    chart.draw_core_timeline(cores, simulation_config['second-slice-size'], simulation_config['duration'])

if __name__ == '__main__':
    launch()