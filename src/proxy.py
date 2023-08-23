from flask import Flask, request, Response
import json
import requests
from flask_cors import CORS
import schedule
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# Load initial configuration
def load_config():
    with open('../config.json', 'r') as file:
        return json.load(file)

config = load_config()

# Maintain a set of defined services to avoid redefining the same route
defined_services = set()

# Maintain a counter for each service to implement round-robin load balancing
service_counters = {}
for service in config['services']:
    service_name = service['name']
    service_counters[service_name] = 0

# Function to send requests to the backend services.
# Include a round robin load balancer so that not all requests are sent to 
# the same service URL. 
# Some URL's in config may not work, so the function 
# must move on to the next one if one doesn't work.
# If the function is able to make a connection to the backend service,
# but the backend service returns an error when checking user input parameters,
# then the error must be passed to the frontend and the function must stop
# checking subsequent service url's in config.
def proxy_request(service_name, service_urls, subpath):
    # Round-robin load balancing
    global service_counters

    method = request.method
    params = request.args
    data = request.data if method != 'GET' else None

    for _ in range(len(service_urls)):
        index = service_counters[service_name] % len(service_urls)
        service_url = service_urls[index] + subpath
        service_counters[service_name] += 1

        try:
            response = requests.request(method, service_url, params=params, data=data)
            if response.status_code >= 200 and response.status_code < 300:
                flask_response = Response(response.content, content_type="application/json")
                flask_response.status_code = response.status_code
                return flask_response
            elif response.status_code == 400:
                # Handle 400 status code by forwarding it to the frontend
                flask_response = Response(response.content, content_type="application/json")
                flask_response.status_code = response.status_code
                return flask_response
            else:
                print(f"Received unexpected status code {response.status_code} from {service_url}")
        except Exception as e:
            print(f"Failed to connect to {service_url}: {e}")

    return f"All {service_name} services are down. Please try again later.", 500



# Function to define routes dynamically based on configuration
def define_routes():
    global defined_services
    for service in config['services']:
        service_name = service['name']
        if service_name in defined_services:
            continue  # Skip if this service route is already defined
        service_urls = service['urls']
        endpoint = f'/{service_name}'

        @app.route(endpoint, defaults={'subpath': ''}, endpoint=f'{service_name}_route')
        @app.route(f'{endpoint}/<path:subpath>', endpoint=f'{service_name}_route_subpath')
        def route(subpath, service_name=service_name, service_urls=service_urls):
            #print(f"Received request for service: {service_name}, subpath: {subpath}") # Debug print
            return proxy_request(service_name, service_urls, subpath)

        defined_services.add(service_name)

# Define routes based on initial configuration
define_routes()

#for rule in app.url_map.iter_rules():   # More debug printing
#    print(rule)

# Function to reload configuration without redefining routes (which was causing errors)
def reload_config():
    global config
    global service_counters

    new_config = load_config()

    # Print the new configuration
    print("Reloading configuration:")
    print(json.dumps(new_config, indent=4))

    config = new_config

    # Update the service_counters based on the new configuration
    service_counters = {service['name']: 0 for service in config['services']}

    define_routes()

# Endpoint to reload configuration
@app.route('/reload-config', methods=['POST'])
def reload_config_endpoint():
    reload_config()
    return "Configuration reloaded successfully", 200

# Schedule the reload configuration job to run every 10 mins on auto
schedule.every(0.1).minutes.do(reload_config)

if __name__ == '__main__':
    import threading

    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)

    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()

    app.run(host='0.0.0.0', port=8007)