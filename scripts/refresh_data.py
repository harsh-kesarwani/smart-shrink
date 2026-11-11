import configparser
from datetime import datetime, timedelta
from prometheus_client import (fetch_current_container_count, fetch_metric_data, calc,
                        fetch_average_cpu_utilization_prom_query, fetch_average_memory_utilization_prom_query,
                        fetch_requested_cpu, fetch_requested_ram)
import json

def refresh():
    print("running script")
    config = configparser.ConfigParser()
    # Read the config file
    config.read('../config.ini')
    service_data_list = []
    print(config.sections())
    for section in config.sections():
        print(f"[{section}]")
        service_data = {}
        service_data['application_name'] = config[section]['application_name']
        service_data['container_name'] = config[section]['container_name']
        service_data['namespace'] = config[section]['namespace']
        service_data['prom_host'] = config[section]['prom_host']
        service_data['user'] = config[section]['user']
        service_data['password'] = config[section]['password']
        service_data['regions'] = config[section]['regions'].split(',')
        service_data['environment'] = config[section]['environment']
        service_data_list.append(service_data)

    print(service_data_list)

    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)

    metric_name = "up"
    step = "60s"
    percentile = 0.95
    services_real_data = []

    for service_data in service_data_list:
        print(service_data)
        for region in service_data['regions']:
            # now we know all the data so let's construct the prom query here
            print(region)
            service_real_data = {}
            service_real_data['name'] = service_data['application_name']
            service_real_data['environment'] = service_data['environment']
            service_real_data['region'] = region
            # container_count = get_container_count(service_data['container_name'], service_data['environment'], region,
            #                    service_data['prom_host'], service_data['user'], service_data['password'], percentile)
            container_count = fetch_current_container_count("enm", service_data['container_name'],
                                                            service_data['environment'], region,
                                                            service_data['prom_host'], service_data['user'],
                                                            service_data['password'])

            print(f"Got container count = {container_count} for {region} region and {service_data['environment']} env")
            service_real_data['no_of_containers'] = container_count
            # TODO: Similarly populate other data as well. populating dummy data for now
            service_real_data['allocated_cpu'] = "281m"
            cpu_df = fetch_metric_data(
                fetch_average_cpu_utilization_prom_query("enm", service_data['container_name'],
                                                         service_data['environment'], region),
                start_time, end_time, step, service_data['prom_host'], service_data['user'], service_data['password'])

            cpu_usage = cpu_df['value'].quantile(percentile)
            service_real_data['cpu_usage'] = cpu_usage

            service_real_data['allocated_ram'] = "4GB"
            memory_df = fetch_metric_data(
                fetch_average_memory_utilization_prom_query("enm", service_data['container_name'],
                                                            service_data['environment'], region),
                start_time, end_time, step, service_data['prom_host'], service_data['user'], service_data['password'])

            memory_usage = memory_df['value'].quantile(percentile)

            service_real_data['ram_usage'] = memory_usage
            # TODO: Apply the formula and calculate suggested number of containers
            suggestion = calc(service_real_data['no_of_containers'], cpu_usage, memory_usage, 2)

            service_real_data['suggested_containers'] = suggestion
            service_real_data['percentage_cost_saving'] = round(
                    ((service_real_data['no_of_containers'] - service_real_data['suggested_containers']) /
                     service_real_data['no_of_containers']) * 100)

            # Absolute cost savings
            cpu_cost_per_hour = 0.0319
            ram_cost_per_hour = 0.00531
            requested_vcpu_df = fetch_requested_cpu("enm", service_data['container_name'],
                                                            service_data['environment'], region,
                                                            service_data['prom_host'], service_data['user'],
                                                            service_data['password'])
            requested_vcpu = requested_vcpu_df['value'].quantile(percentile)
            print(requested_vcpu)
            requested_ram_df = fetch_requested_ram("enm", service_data['container_name'],
                                                            service_data['environment'], region,
                                                            service_data['prom_host'], service_data['user'],
                                                            service_data['password'])
            requested_ram = requested_ram_df['value'].quantile(percentile) / (1024**3)
            print(requested_ram)
            total_cost_per_month_today = (requested_vcpu * cpu_cost_per_hour  + requested_ram * ram_cost_per_hour)*container_count*24*30
            total_cost_per_month_after_downscale = (requested_vcpu * cpu_cost_per_hour  + requested_ram * ram_cost_per_hour)*suggestion*24*30
            potential_cost_savings = total_cost_per_month_today - total_cost_per_month_after_downscale
            service_real_data['absolute_cost_saving'] = round(potential_cost_savings)
            services_real_data.append(service_real_data)

    # Write to a file
    sorted_service_data = sorted(services_real_data, key=lambda x: x['absolute_cost_saving'], reverse=True)

    with open("../results.json", "w") as file:
        json.dump(sorted_service_data, file, indent=4)  # Pretty print with indentation


if __name__ == "__main__":
    refresh()