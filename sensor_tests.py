import concurrent.futures
import json
import logging
import os
from datetime import datetime

import paramiko
import yaml
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv(dotenv_path=r'C:\Users\Roy Avrahami\PycharmProjects\sensorz_qa_roy\config\.env')

sensors_file_path = os.getenv('SENSOR_DETAILS_PATH')
reports_directory = os.getenv('REPORTS_DIRECTORY')
password_sensorz = os.getenv('PASSWORD_SENSORZ')

assert sensors_file_path is not None, "SENSOR_DETAILS_PATH is not set"
assert reports_directory is not None, "REPORTS_DIRECTORY is not set"
assert password_sensorz is not None, "PASSWORD_SENSORZ is not set"

print("Environment variables loaded successfully.")


def load_tests(file_path):
    assert os.path.isfile(file_path), "Test file {} does not exist.".format(file_path)
    with open(file_path) as file:
        tests = json.load(file)
        assert isinstance(tests, dict), "Tests file format is incorrect. Expected a dictionary."
        print("Test definitions loaded.")
        return tests


def load_sensor_details(file_path):
    assert os.path.isfile(file_path), "Sensor details file {} does not exist.".format(file_path)
    with open(file_path) as file:
        sensor_details = yaml.safe_load(file)
        assert isinstance(sensor_details, list), "Sensor details file format is incorrect. Expected a list."
        print("Sensor details loaded.")
        return sensor_details


def run_ssh_command(ip_address_sensor, username_sensorz, sensorz_password, command):
    assert isinstance(command, str), "Command must be a string."
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=ip_address_sensor, username=username_sensorz, password=sensorz_password)
        logging.info("Connected to {}".format(ip_address_sensor))
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        success = not error  # Test passes if no error message
        if error:
            logging.error("Error executing {} on {}: {}".format(command, ip_address_sensor, error))
        else:
            print("Command executed successfully on {}.".format(ip_address_sensor))
        return success, output
    except Exception as e:
        logging.error("Connection or execution failed for {}: {}".format(ip_address_sensor, str(e)))
        return False, str(e)
    finally:
        client.close()


def run_test_on_sensor(sensor, tests):
    ip_address_sensor = sensor['ip_address_sensor']
    hostname_sensor = sensor['hostname']
    username_sensorz = sensor['username_sensorz']

    sensor_result = {
        "hostname": hostname_sensor,
        "ip_address": ip_address_sensor,
        "results": {}
    }

    for category, test_commands in tests.items():
        category_results = []
        for test in test_commands:
            logging.info("Executing test: {} on sensor: {} {}".format(test['name'], hostname_sensor, ip_address_sensor))

            formatted_command = test['command']
            success, output = run_ssh_command(ip_address_sensor, username_sensorz, password_sensorz, formatted_command)

            log_output = ""
            if "log_check" in test:
                log_command = test['log_check']
                _, log_output = run_ssh_command(ip_address_sensor, username_sensorz, password_sensorz, log_command)

            test_status = "Passed" if success else "Failed"

            category_results.append({
                "test_name": test['name'],
                "output": output,
                "log_output": log_output,
                "status": test_status
            })

        sensor_result["results"][category] = category_results

    logging.info("Tests completed for sensor: {} {}".format(hostname_sensor, ip_address_sensor))
    return sensor_result


def execute_tests(sensor_details, tests):
    assert isinstance(sensor_details, list), "Sensor details should be a list."
    assert isinstance(tests, dict), "Tests should be a dictionary."

    with concurrent.futures.ThreadPoolExecutor() as executor:
        test_results = list(executor.map(lambda sensor: run_test_on_sensor(sensor, tests), sensor_details))

    return test_results


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
    report_directory = os.getenv('REPORTS_DIRECTORY')
    if not os.path.exists(report_directory):
        os.makedirs(report_directory)
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

    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = "report_{}.html".format(timestamp_str)

    report = generate_html_report(test_results, title)
    report_filepath = generate_report(report, report_filename)

    logging.info("Report saved to {}".format(report_filepath))


if __name__ == "__main__":
    main()
