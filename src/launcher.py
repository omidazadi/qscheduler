import os
import json
from core import Core
from ptask_generator import PTaskGenerator
from ptask_stat import PTaskStat
from qscheduler import QScheduler
from chart import Chart

def launch():
    core_config = json.load(open('configs/core_config.json', 'r'))
    qscheduler_config = json.load(open('configs/qscheduler_config.json', 'r'))
    simulation_config = json.load(open('configs/simulation_config.json', 'r'))

    cores: list[Core] = []
    for core_id in simulation_config['cores']:
        core_name, allowed_avg_power = simulation_config['cores'][core_id]['name'], simulation_config['cores'][core_id]['allowed-average-power-mW']
        cores.append(Core(core_name, core_id, core_config[core_name]['average-cpi'], core_config[core_name]['1-GHz-power-mW'], 
                            core_config[core_name]['dvfs-change-lock'], core_config[core_name]['dfvs-levels'], 
                            simulation_config['cores'][core_id]['default-dvfs-level'], allowed_avg_power, simulation_config['second-slice-size']))
            
    total_cpu_resource = 0
    for core in cores:
        total_cpu_resource += core.available_resource

    ptask_generator = PTaskGenerator()
    ptasks = ptask_generator.generate(simulation_config['task-set-size'], simulation_config['utilization'], total_cpu_resource,
                             simulation_config['task-periods'], simulation_config['real-time-modes'], simulation_config['second-slice-size'])
    
    qscheduler = QScheduler(qscheduler_config['mapping-algorithm'], qscheduler_config['learning-rate'], qscheduler_config['exploration-proboblity'],
                            qscheduler_config['exploration-decay-factor'], qscheduler_config['episodes'], qscheduler_config['soft-schedule-reward'], 
                            qscheduler_config['soft-delay-reward'], qscheduler_config['soft-miss-penalty'], qscheduler_config['firm-schedule-reward'], 
                            qscheduler_config['firm-miss-penalty'], qscheduler_config['dvfs-up-reward'], qscheduler_config['dvfs-down-reward'], 
                            qscheduler_config['finish-reward'], qscheduler_config['retry'], simulation_config['second-slice-size'])

    qscheduler.map_ptasks_to_cores(cores, ptasks)

    for core in cores:
        qscheduler.schedule(core, simulation_config['duration'])

    if not os.path.exists('./simulation-results'):
        os.mkdir('simulation-results')

    simulation_number = len(os.listdir('./simulation-results')) + 1
    simulation_path = f'./simulation-results/{simulation_number}'
    if os.path.exists(simulation_path):
        os.rmdir(simulation_path)
    os.mkdir(simulation_path)

    config = { "core": core_config, "qscheduler": qscheduler_config, "simulation": simulation_config}
    ptask_stats = PTaskStat.extract_ptask_stats(cores, simulation_config['second-slice-size'])
    json.dump(config, open(f'{simulation_path}/config.json', 'w'), indent=4)
    json.dump(list(map(PTaskStat.ptask_stat_to_dict, ptask_stats)), open(f'{simulation_path}/ptasks.json', 'w'), indent=4)
    
    chart = Chart()
    core_timeline_fig = chart.draw_core_timeline(cores, simulation_config['second-slice-size'], simulation_config['duration'])
    core_timeline_fig.savefig(f'{simulation_path}/core_timeline.jpg')
    ptask_schedulability_fig = chart.draw_ptask_schedulability(ptask_stats)
    ptask_schedulability_fig.savefig(f'{simulation_path}/task_schedulability.jpg')
    ptask_timing_fig = chart.draw_ptask_timing(ptask_stats)
    ptask_timing_fig.savefig(f'{simulation_path}/task_timing.jpg')
    core_frequency_fig = chart.draw_core_frequency(cores)
    core_frequency_fig.savefig(f'{simulation_path}/core_frequency.jpg')
    core_energy_fig = chart.draw_core_energy(cores, simulation_config['duration'])
    core_energy_fig.savefig(f'{simulation_path}/core_energy.jpg')

if __name__ == '__main__':
    launch()