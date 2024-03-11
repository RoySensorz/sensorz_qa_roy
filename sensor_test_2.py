import logging
import os
import socket
import time
from datetime import datetime

import paramiko
from jinja2 import Environment, FileSystemLoader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths and credentials (placeholders)
sensors_file_path = r"C:\Users\Roy Avrahami\Documents\Sensorz Docs\PoE issue\sensors_details1.txt"
reports_directory = r"C:\Users\Roy Avrahami\Documents\Sensorz Docs\PoE issue\sensors reports runs"
password_sensorz = "sensorz1234"  # Consider secure handling

# Define the structure of tests to be executed
tests = {
    "Functional": [
        # Functional tests removed for brevity
    ],
    "Performance": [
        {"name": "CPU Load Test",
         "command": "stress --cpu 8 --timeout 60s && grep 'CPU Load' /var/log/sensorz/utils_health.log"},
        {"name": "Memory Usage Test",
         "command": "stress --vm 2 --vm-bytes 128M --timeout 60s && grep 'Memory Usage' "
                    "/var/log/sensorz/utils_health.log"},
        {"name": "Disk Write Performance Test",
         "command": "dd if=/dev/zero of=/tmp/test1.img bs=1G count=1 oflag=dsync && tail "
                    "/var/log/sensorz/health_main.log"},
        {"name": "Network Throughput Test",
         "command": "iperf3 -c 10.8.0.1 -p 12321 -t 10; cat /var/log/sensorz/sensorz_mon.log | grep 'Network "
                    "Throughput'"},
        {"name": "Data Processing Rate Test",
         "command": "cat /var/log/sensorz/rf_scanner.log | grep 'Data Processed'"},
    ],
    "Stability": [
        {"name": "Temperature Stability Test",
         "command": "cat /var/log/sensorz/utils_health.log | grep 'Temperature'"},
        # Stability tests removed for brevity
    ],
    "Network": [
        {"name": "Internal Network Latency Test",
         "command": "ping -c 10 10.8.0.1 && cat /var/log/sensorz/network.log | grep 'Latency'"},
        {"name": "External Network Connectivity Test",
         "command": "ssh sensorz@(ip_address_sensor) -C 'ping -c 10 8.8.8.8'"},
        {"name": "DNS Resolution Test",
         "command": "ssh sensorz@(ip_address_sensor) -C 'dig example.com'"},
        {"name": "Network Upload Speed Test",
         "command": "ssh sensorz@(ip_address_sensor) -C 'iperf3 -c 10.8.0.1 -p 12321 -t 10 -R'"},
        {"name": "Network Download Speed Test",
         "command": "ssh sensorz@(ip_address_sensor) -C 'iperf3 -c 10.8.0.1 -p 12321 -t 30'"},
        {"name": "VPN Connectivity Test",
         "command": "ssh sensorz@(ip_address_sensor) -C 'curl -I https://secure.resource.via.vpn'"},
        {"name": "Network Bandwidth Control Test",
         "command": f"scp 'C:\\Users\\Roy Avrahami\\Documents\\Sensorz Docs\\PoE issue\\file size 1GB\\1GB.bin' "
                    f"'sensorz@{{ip_address_sensor}}:/destination/path/on/remote/machine'"},
        {"name": "Network Packet Loss Test",
         "command": "ssh sensorz@(ip_address_sensor) -C 'mtr -rw 8.8.8.8'"},
    ],
    "Hardware": [
        # Hardware tests removed for brevity
    ],
}


def run_ssh_command(ip_address_sensor, username_sensorz, password_sensorz, command):
    """Establish SSH connection and execute a command, with special handling for reboot tests.

    Args:
        ip_address_sensor (str): IP address of the sensor.
        username_sensorz (str): Username for SSH login.
        command (str): Command to be executed.
        password_sensorz (str): Password for SSH login.

    Returns:
        str: Command output or error message.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname=ip_address_sensor, username=username_sensorz, password=password_sensorz)
        logging.info(f"Connected to {ip_address_sensor}")

        adjusted_command = command.replace("(ip_address)", ip_address_sensor)

        if "sudo reboot" in adjusted_command:
            stdin, stdout, stderr = client.exec_command(adjusted_command, get_pty=True)
            time.sleep(10)  # Wait briefly for the command to execute before closing
            client.close()

            attempts, connected = 0, False
            while not connected and attempts < 5:  # Attempt to reconnect up to 5 times
                try:
                    time.sleep(10)  # Wait before each reconnection attempt
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(hostname=ip_address_sensor, username=username_sensorz, password=password_sensorz)
                    connected = True
                    logging.info(f"Reconnected to {ip_address_sensor} after reboot")
                except (paramiko.AuthenticationException, paramiko.SSHException, socket.error) as e:
                    attempts += 1
                    logging.info(f"Attempt {attempts}: Reconnection to {ip_address_sensor} failed, retrying...")
            if not connected:
                return f"Failed to reconnect to {ip_address_sensor} after {attempts} attempts."

            # Execute the command to collect logs after reboot
            stdin, stdout, stderr = client.exec_command("tail -f /var/log/sensorz/HealthMonitoring.log")
        else:
            stdin, stdout, stderr = client.exec_command(adjusted_command)

        output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            logging.error(f"Error executing {command} on {ip_address_sensor}: {error}")
            return error
        return output

    except (paramiko.AuthenticationException, paramiko.SSHException, socket.error) as e:
        logging.error(f"SSH connection to {ip_address_sensor} failed: {e}")
        return str(e)
    finally:
        if client.get_transport() is not None:
            client.close()

            pass


# Adjusted execute_tests function signature to remove the ip_address_sensor parameter
def execute_tests(sensor_details, tests):
    test_results = []
    for sensor_info in sensor_details:
        sensor_info = sensor_info.strip()
        if sensor_info:  # Ensure the line is not empty
            try:
                user_host_pwd = sensor_info.replace("ssh ", "")
                username_sensorz, rest = user_host_pwd.split('@')
                ip_address_sensor, pwd = rest.split(',')

                sensor_result = {"ip_address": ip_address_sensor, "results": {}}
                for category, test_commands in tests.items():
                    category_results = []
                    for test in test_commands:
                        # Replace the placeholder in the command with the actual IP address
                        formatted_command = test["command"].replace("(ip_address_sensor)", ip_address_sensor)
                        output = run_ssh_command(ip_address_sensor, username_sensorz, password_sensorz,
                                                 formatted_command)

                        # Determine test status based on output
                        test_status = "Failed" if any(
                            err in output.lower() for err in ['error', 'errors', 'failed']) else "Passed"

                        # Append both output and status
                        category_results.append({
                            "test_name": test["name"],
                            "output": output,
                            "status": test_status  # Add test status here
                        })
                    sensor_result["results"][category] = category_results
                test_results.append(sensor_result)
            except ValueError as e:
                logging.error(f"Error processing line: '{sensor_info}'. Error: {e}")
    return test_results

    pass


def load_sensor_details(file_path):
    """Load sensor details from a file.

    Args:
        file_path (str): Path to the file containing sensor details.

    Returns:
        list: Sensor details.
    """
    with open(file_path) as file:
        return [line.strip() for line in file if line.strip()]

    pass


def generate_html_report(test_results, title, template_dir='templates', template_file='report_template.html',
                         ip_address_sensor=None):
    # Create Jinja2 environment and load the template
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_file)

    # Construct the report data dictionary
    report_data = {
        'title': title,
        'date_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sensor_id': ip_address_sensor,
        'sensors': test_results  # Assuming test_results is already structured correctly
    }

    # Pass the report data to the template and render the HTML report
    return template.render(report_data)

    pass


def main():
    sensor_details = load_sensor_details(sensors_file_path)
    test_results = execute_tests(sensor_details, tests)
    current_time = datetime.now().strftime('%Y-%m-%d %H_%M_%S')
    title = f'PoE issue investigation {current_time}'
    report = generate_html_report(test_results, title)
    report_file_path = os.path.join(reports_directory, f"sensor_report_{current_time}.html")
    with open(report_file_path, 'w') as file:
        file.write(report)
    logging.info(f"Report saved to {report_file_path}")


if __name__ == "__main__":
    main()
