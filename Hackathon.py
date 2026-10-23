import pandas as pd
import numpy as np
import random as r

#simulate reality
def generate_environment_data():
    hours = np.arange(24)
    
    # electricity price
    base_price = 200 + 150 * np.sin((hours - 8) * np.pi / 12)
    noise_price = np.random.default_rng(42).normal(0, 10, 24)
    price = np.round(base_price + noise_price, 2)
    
    #carbon emmission
    carbon = np.zeros(24)
    for h in hours:
        if 10 <= h <= 15:
            carbon[h] = 250 + np.random.default_rng(h).normal(0, 15)
        elif 18 <= h <= 21:
            carbon[h] = 650 + np.random.default_rng(h).normal(0, 30)
        else:
            carbon[h] = 450 + np.random.default_rng(h).normal(0, 20)
            
    carbon = np.round(carbon, 2)
    return price, carbon

#simulate workload
def generate_workload():
    rng = np.random.default_rng(42)
    tasks = []
    tid = 0
    
    #simluate tasks
    for h in range(24):
        #High priority
        if h % r.randint(1, 19) == 0:
            tid += 1
            tasks.append({
                'task_id': tid,
                'priority_level': 'High',
                'energy_kwh': round(rng.uniform(20, 40), 1),
                'is_latency_sensitive': True,
                'deadline_hours': 0,
                'arrival_hour': h,
                'executed_hour': h
            })
            
        #low priority
        tid += 1
        tasks.append({
            'task_id': tid,
            'priority_level': 'Low',
            'energy_kwh': round(rng.uniform(50, 120), 1),
            'is_latency_sensitive': False,
            'deadline_hours': int(rng.integers(2, 7)),
            'arrival_hour': h,
            'executed_hour': h
        })
    return tasks

#calculate the best
def compute_metrics(tasks, price_arr, carbon_arr):
    total_cost = 0.0
    total_carbon = 0.0
    for t in tasks:
        h = t['executed_hour']
        total_cost += t['energy_kwh'] * (price_arr[h] / 1000.0)
        total_carbon += t['energy_kwh'] * (carbon_arr[h] / 1000.0)
    return total_cost, total_carbon


#output
print('       数据中心碳价感知调度原型 - 模拟环境测试')

price_series, carbon_series = generate_environment_data()

min_p = str(round(np.min(price_series), 1))
max_p = str(round(np.max(price_series), 1))
min_c = str(int(round(np.min(carbon_series), 0)))
max_c = str(int(round(np.max(carbon_series), 0)))

print('模拟电价范围: ' + min_p + ' - ' + max_p + ' 元/MWh')
print('模拟碳排范围: ' + min_c + ' - ' + max_c + ' kgCO2/MWh')
print('----------------------------------------------------------------')

tasks_baseline = generate_workload()
base_cost, base_carbon = compute_metrics(tasks_baseline, price_series, carbon_series)
tasks_aware = generate_workload()

p_min = np.min(price_series)
p_max = np.max(price_series)
c_min = np.min(carbon_series)
c_max = np.max(carbon_series)

p_norm = (price_series - p_min) / (p_max - p_min + 1e-9)
c_norm = (carbon_series - c_min) / (c_max - c_min + 1e-9)

score = 0.5 * p_norm + 0.5 * c_norm

for t in tasks_aware:
    if t['priority_level'] == 'Low':
        start = t['arrival_hour']
        end = min(t['arrival_hour'] + t['deadline_hours'], 23)
        window = list(range(start, end + 1))
        best_hour = min(window, key=lambda h: score[h])
        t['executed_hour'] = best_hour

aware_cost, aware_carbon = compute_metrics(tasks_aware, price_series, carbon_series)

b_cost_str = str(round(base_cost, 4))
a_cost_str = str(round(aware_cost, 4))
b_carb_str = str(round(base_carbon, 2))
a_carb_str = str(round(aware_carbon, 2))

print('指标'.ljust(20) + '基线 (立即执行)'.rjust(18) + '碳价感知调度'.rjust(18))
print('总电费 (RMB)'.ljust(20) + b_cost_str.rjust(18) + a_cost_str.rjust(18))
print('总碳排放 (kgCO2)'.ljust(20) + b_carb_str.rjust(18) + a_carb_str.rjust(18))

cost_save = (base_cost - aware_cost) / base_cost * 100
carbon_save = (base_carbon - aware_carbon) / base_carbon * 100

cs_str = str(round(cost_save, 2))
cas_str = str(round(carbon_save, 2))

print()
print('成本降低: ' + cs_str + '%')
print('碳排降低: ' + cas_str + '%')