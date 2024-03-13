import json
import logging
import os
import socket
import paramiko
import yaml
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv(dotenv_path='C:/Users/Roy Avrahami/PycharmProjects/sensorz_qa_roy/config/.env')

# Access variables
sensors_file_path = os.getenv('SENSOR_DETAILS_PATH')
reports_directory = os.getenv('REPORTS_DIRECTORY')
password_sensorz = os.getenv('PASSWORD_SENSORZ')

print(os.getenv('SENSOR_DETAILS_PATH'))
print(os.getenv('REPORTS_DIRECTORY'))
print(os.getenv('PASSWORD_SENSORZ'))

# Assert that essential variables are not None
assert sensors_file_path is not None, "SENSOR_DETAILS_PATH is not set"
assert reports_directory is not None, "REPORTS_DIRECTORY is not set"
assert password_sensorz is not None, "PASSWORD_SENSORZ is not set"

print("Environment variables loaded successfully.")


# Load test definitions from a JSON file
def load_tests(file_path):
    assert os.path.isfile(file_path), f"Test file {file_path} does not exist."
    with open(file_path) as file:
        tests = json.load(file)
        assert isinstance(tests, dict), "Tests file format is incorrect. Expected a dictionary."
        print("Test definitions loaded.")
        return tests


# Load sensor details from a YAML file
def load_sensor_details(file_path):
    assert os.path.isfile(file_path), f"Sensor details file {file_path} does not exist."
    with open(file_path) as file:
        sensor_details = yaml.safe_load(file)
        assert isinstance(sensor_details, list), "Sensor details file format is incorrect. Expected a list."
        print("Sensor details loaded.")
        return sensor_details


# Function to establish SSH connection and execute command
def run_ssh_command(ip_address_sensor, username_sensorz, password_sensorz, command):
    assert isinstance(command, str), "Command must be a string."
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=ip_address_sensor, username=username_sensorz, password=password_sensorz)
        logging.info(f"Connected to {ip_address_sensor}")
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        if error:
            logging.error(f"Error executing {command} on {ip_address_sensor}: {error}")
            return error
        print(f"Command executed successfully on {ip_address_sensor}.")
        return output
    except (paramiko.AuthenticationException, paramiko.SSHException, socket.error) as e:
        logging.error(f"SSH connection to {ip_address_sensor} failed: {e}")
        return str(e)
    finally:
        client.close()


# Function to execute all tests for all sensors
# Function to execute all tests for all sensors
# Function to execute all tests for all sensors
def execute_tests(sensor_details, tests):
    assert isinstance(sensor_details, list), "Sensor details should be a list."
    assert isinstance(tests, dict), "Tests should be a dictionary."
    test_results = []
    for sensor in sensor_details:
        ip_address_sensor = sensor['ip_address_sensor']
        hostname_sensor = sensor['hostname']
        username_sensorz = sensor['username_sensorz']
        sensor_result = {"hostname": hostname_sensor, "ip_address": ip_address_sensor, "results": {}}
        for category, test_commands in tests.items():
            category_results = []
            for test in test_commands:
                logging.info(f"Executing test: {test['name']} on sensor: {hostname_sensor} {ip_address_sensor}")
                formatted_command = test['command']
                output = run_ssh_command(ip_address_sensor, username_sensorz, password_sensorz, formatted_command)
                test_status = "Passed" if output else "Failed"
                category_results.append({"test_name": test['name'], "output": output, "status": test_status})
            sensor_result["results"][category] = category_results
        test_results.append(sensor_result)
        logging.info(f"Tests completed for sensor: {hostname_sensor} {ip_address_sensor}")
        print(f"Tests executed for sensor {hostname_sensor} {ip_address_sensor}.")
    return test_results


# Function to generate an HTML report
def generate_html_report(test_results, title, template_dir='templates', template_file='report_template.html'):
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_file)
    report_data = {
        'title': title,
        'date_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'test_results': test_results
    }
    report_content = template.render(report_data)
    print("HTML report generated.")
    return report_content


def generate_report(report_content, report_filename=None):
    report_directory = 'reports'
    if not os.path.exists(report_directory):
        os.makedirs(report_directory)

    # rest of your code...

    report_filepath = os.path.join(report_directory, report_filename)

    with open(report_filepath, "w") as report_file:
        report_file.write(report_content)

    return report_filepath


def main(tests_file_path=r'C:\Users\Roy Avrahami\PycharmProjects\sensorz_qa_roy\tests\test_definitions.json'):
    print("Starting test execution...")
    sensor_details = load_sensor_details(sensors_file_path)
    tests = load_tests(tests_file_path)
    test_results = execute_tests(sensor_details, tests)

    title = 'Sensor Test Report - ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report = generate_html_report(test_results, title)

    # generate the report and get the file path
    report_filepath = generate_report(report)

    logging.info(f"Report saved to {report_filepath}")


if __name__ == "__main__": main()
