# qscheduler
Real-time, multi-core scheduler with QLearning.

Configuration files for the simulator can be found at `configs` directory, and they are fairly straight-forward to understand. When one starts the simulation with the given configurations, the result of the simulation (if it was successful) can be found at `simulation-results` directory. Sub-directories of `simulation-results` are named with ordinal numbers, with higher numbers pointing to later simulations.

First install the requirements (perferably in a venv) with the below command:
```bash
pip3 install -r requirements.txt
```

Then start the simulation with:
```bash
python3 src/launcher.py
```

Enjoy!