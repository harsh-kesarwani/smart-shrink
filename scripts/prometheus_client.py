from datetime import datetime, timedelta

import pandas as pd
from prometheus_api_client import PrometheusConnect
from requests.auth import HTTPBasicAuth
import sys

prome_url = "https://nacho.aws1217.adobeitc.com/api/prom"  # Replace with your Prometheus server URL
user = "724"  # Replace with your Prometheus username
passw = ""  # Replace with your Prometheus password


def test_prometheus_connection(prometheus_url, username, password):
    try:
        # Set up authentication
        auth = HTTPBasicAuth(username, password)
        # Connect to Prometheus
        prom = PrometheusConnect(url=prometheus_url, auth=auth,
                                 disable_ssl=True)  # Set disable_ssl=False if using HTTPS
        # Perform a simple query to test the connection
        metric_name = 'up'  # 'up' metric is commonly used to check if a target is up
        response = prom.get_current_metric_value(metric_name)
        # If we get a valid response (non-empty), the connection is working
        if response:
            print("Connection successful! Prometheus is reachable.")
            return True
        else:
            print(f"Connection failed. No data returned for metric '{metric_name}'.")
            return False
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


def calc(current_containers, average_cpu_utilization, average_memory_utilization, floor_val):
    suggested_max = max((current_containers*average_cpu_utilization)/100, (current_containers*average_memory_utilization)/100, floor_val)
    return min(current_containers, suggested_max)

def fetch_average_cpu_utilization_prom_query(cluster, container, enm_env, enm_region):
    prom_query = f'''
        sum(rate(container_cpu_usage_seconds_total{{
            cluster="{cluster}",
            enm_region=~"{enm_region}",
            namespace=~".*",
            container=~"{container}",
            enm_env=~"{enm_env}"
        }}[5m])) by (container, enm_region, enm_env) /
        sum(kube_pod_container_resource_requests{{
            resource="cpu",
            unit="core",
            cluster="{cluster}",
            container=~"{container}",
            enm_region=~"{enm_region}",
            enm_env=~"{enm_env}",
            namespace=~".*"
        }}) by (container, enm_region, enm_env)
    '''
    return prom_query

def fetch_average_memory_utilization_prom_query(cluster, container, enm_env, enm_region):
    prom_query = f'''
        sum(container_memory_usage_bytes{{
            cluster="{cluster}",
            enm_region=~"{enm_region}",
            container=~"{container}",
            enm_env=~"{enm_env}"
        }}) by (container, enm_region, enm_env) /
        sum(kube_pod_container_resource_requests{{
            resource="memory", 
            unit="byte", 
            cluster="{cluster}", 
            container=~"{container}",
            enm_region=~"{enm_region}",
            enm_env=~"{enm_env}",
            namespace=~".*"
        }}) by (container, enm_region, enm_env)
    '''
    return prom_query


def fetch_min_memory_utilization_prom_query(cluster, container, enm_env, enm_region):
    prom_query = f'''
        sum(container_memory_usage_bytes{{
            cluster="{cluster}",
            enm_region=~"{enm_region}",
            container=~"{container}",
            enm_env=~"{enm_env}"
        }}) by (container, enm_region, enm_env)
    '''
    return prom_query


def fetch_current_container_count(cluster, container, enm_env, enm_region, prometheus_url, username,
                                  password, namespace=".*"):
    try:
        # Set up authentication
        auth = HTTPBasicAuth(username, password)

        # Connect to Prometheus
        prom = PrometheusConnect(url=prometheus_url, auth=auth,
                                 disable_ssl=True)  # Set disable_ssl=False if using HTTPS

        # Define the PromQL query to count the current number of containers
        prom_query = f'''
            count(kube_pod_container_info{{
                cluster="{cluster}",
                namespace=~"{namespace}",
                container=~"{container}",
                enm_env=~"{enm_env}",
                enm_region=~"{enm_region}"
            }}) by (container, namespace)
        '''

        # Fire the query
        data = prom.custom_query(query=prom_query)

        # If data is returned, extract the count
        if data:
            metric_data = data[0]
            container_count = int(metric_data['value'][1])
            return container_count
        else:
            print(f"No data returned for the query: {prom_query}")
            return None

    except Exception as e:
        print(f"Failed to fetch data from Prometheus: {e}")
        return None

def fetch_requested_cpu(cluster, container, enm_env, enm_region, prometheus_url, username, password, namespace=".*"):
    try:
        # Set up authentication
        auth = HTTPBasicAuth(username, password)

        # Connect to Prometheus
        prom = PrometheusConnect(url=prometheus_url, auth=auth, disable_ssl=True)  # Set disable_ssl=False if using HTTPS


        #Define the PromQL query to count the current number of containers
        prom_query = f'''
            sum(kube_pod_container_resource_requests{{
                resource="cpu",
                unit="core",
                cluster="{cluster}",
                namespace=~"{namespace}",
                container=~"{container}",
                enm_env=~"{enm_env}",
                enm_region=~"{enm_region}"
            }}) by (container, pod, enm_env, enm_region)
        '''

        # Fire the query
        data = prom.custom_query(query=prom_query)
        print(data)
        # If data is returned, extract the count
        if data:
            df = pd.DataFrame(data)
            df['value'] = df['value'].apply(lambda x: float(x[1]))
            # Drop rows with NaN values in 'value' column
            return df
        else:
            print(f"No data returned for the query: {prom_query}")
            return None

    except Exception as e:
        print(f"Failed to fetch data from Prometheus: {e}")
        return None

def fetch_requested_ram(cluster, container, enm_env, enm_region, prometheus_url, username, password, namespace=".*"):
    try:
        # Set up authentication
        auth = HTTPBasicAuth(username, password)

        # Connect to Prometheus
        prom = PrometheusConnect(url=prometheus_url, auth=auth, disable_ssl=True)  # Set disable_ssl=False if using HTTPS


        #Define the PromQL query to count the current number of containers
        prom_query = f'''
            sum(kube_pod_container_resource_requests{{
                cluster="{cluster}",
                container=~"{container}",
                enm_env=~"{enm_env}",
                enm_region=~"{enm_region}"
            }}) by (container, pod, enm_env, enm_region)
        '''

        # Fire the query
        data = prom.custom_query(query=prom_query)
        print(data)
        # If data is returned, extract the count
        if data:
            df = pd.DataFrame(data)
            df['value'] = df['value'].apply(lambda x: float(x[1]))
            # Drop rows with NaN values in 'value' column
            return df
        else:
            print(f"No data returned for the query: {prom_query}")
            return None

    except Exception as e:
        print(f"Failed to fetch data from Prometheus: {e}")
        return None


def fetch_metric_data(prom_query, start_time, end_time, step, prometheus_url, username, password):
    try:
        # Set up authentication
        auth = HTTPBasicAuth(username, password)

        # Connect to Prometheus
        prom = PrometheusConnect(url=prometheus_url, auth=auth, disable_ssl=True)  # Set disable_ssl=False if using HTTPS

        # Fetch the metric data using the PromQL query
        data = prom.custom_query_range(
            query=prom_query,
            start_time=start_time,
            end_time=end_time,
            step=step
        )

        if data:
            # Convert the fetched data to a pandas DataFrame for easier manipulation
            df = pd.DataFrame(data[0]['values'], columns=['timestamp', 'value'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df['value'] = pd.to_numeric(df['value'], errors='coerce')

            # Drop rows with NaN values in 'value' column
            df = df.dropna(subset=['value'])
            return df
        else:
            print(f"No data returned for the query '{prom_query}' in the specified time range.")
            return None
    except Exception as e:
        print(f"Failed to fetch metric data: {e}")
        return None


if __name__ == "__main__":
    # Hardcoded Prometheus connection details
    cluster = "enm"
    container = "operationmanager"
    enm_env = "stage"
    enm_region = "jpn3"
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)

    metric_name = "up"
    step = "5m"

    # Check if credentials are provided
    if not user or not passw:
        print("Error: PROMETHEUS_USERNAME and PROMETHEUS_PASSWORD must be set.")
        sys.exit(1)

    # Test the connection
    if not test_prometheus_connection(prome_url, user, passw):
        sys.exit(1)  # Exit with an error code if the connection fails

    df_mem_util_30_days = fetch_metric_data(
        fetch_min_memory_utilization_prom_query(cluster, container, enm_env, enm_region),
        end_time - timedelta(days=30), end_time, "10m", prome_url, user, passw)
    min_value = df_mem_util_30_days['value'].min()

    container_count = fetch_current_container_count(cluster, container, enm_env, enm_region,
                                                    prome_url, user, passw)

    cpu_df = fetch_metric_data(
        fetch_average_cpu_utilization_prom_query(cluster, container, enm_env, enm_region),
        start_time, end_time, step, prome_url, user, passw)

    cpu_p95 = cpu_df['value'].quantile(0.95)

    overhead = container_count * min_value

    memory_df = fetch_metric_data(
        fetch_average_memory_utilization_prom_query(cluster, container, enm_env, enm_region),
        start_time, end_time, step, prome_url, user, passw)

    memory_p95 = memory_df['value'].quantile(0.95)

    suggestion = calc(container_count, cpu_p95, memory_p95, 2)
    print(suggestion)
