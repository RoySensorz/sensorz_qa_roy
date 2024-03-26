import paramiko

# Define your sensors here
sensors = [
    {"ip": "10.8.0.163", "hostname": "SENS-WA10-398A-0154"},
    {"ip": "10.8.0.76", "hostname": "GLOB-WA10-398A-0067"},
    # Add more sensors as needed
]


def run_ssh_command(ip, username, password, command):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read() + stderr.read()  # Capture both stdout and stderr
        ssh.close()
        return True, output.decode('utf-8').strip()
    except Exception as e:
        return False, str(e).strip()


def connectivity_test(sensor_ip, sensor_hostname):
    ssh_status, ssh_output = run_ssh_command(sensor_ip, 'sensorz', 'sensorz1234', 'echo OK')
    vpn_status, vpn_output = run_ssh_command(sensor_ip, 'sensorz', 'sensorz1234',
                                             f'sudo systemctl status openvpn@{sensor_hostname}.service')
    ip_addr_status, ip_addr_output = run_ssh_command(sensor_ip, 'sensorz', 'sensorz1234', 'ip addr')
    ping_status, ping_output = run_ssh_command(sensor_ip, 'sensorz', 'sensorz1234', 'ping -c 4 google.com')

    return {
        'SSH Access': (ssh_status, ssh_output),
        'VPN Status': (vpn_status, vpn_output),
        'IP Address': (ip_addr_status, ip_addr_output),
        'External Connectivity': (ping_status, ping_output)
    }


def performance_test(sensor_ip):
    # Placeholder for performance test, replace with actual command or sequence
    bandwidth_status, bandwidth_output = run_ssh_command(sensor_ip, 'sensorz', 'sensorz1234',
                                                         "iperf3 -c server_ip -p 5201 -t 10")
    latency_status, latency_output = run_ssh_command(sensor_ip, 'sensorz', 'sensorz1234', "ping -c 4 8.8.8.8")

    return {
        'Bandwidth Test': (bandwidth_status, bandwidth_output),
        'Latency Test': (latency_status, latency_output)
    }


def security_test(sensor_ip, sensor_hostname):
    # Placeholder for security test, adjust commands as necessary
    config_status, config_output = run_ssh_command(sensor_ip, 'sensorz', 'sensorz1234',
                                                   f"cat /etc/openvpn/{sensor_hostname}.conf")
    log_status, log_output = run_ssh_command(sensor_ip, 'sensorz', 'sensorz1234',
                                             "grep 'WARN\\|ERROR' /var/log/openvpn.log")

    return {
        'OpenVPN Configuration': (config_status, config_output),
        'Security Logs': (log_status, log_output)
    }


def compatibility_test(sensor_ip):
    # Placeholder for compatibility test, adjust commands as necessary
    data_transmission_status, data_transmission_output = run_ssh_command(sensor_ip, 'sensorz', 'sensorz1234',
                                                                         "echo 'Data transmission test'")
    db_connectivity_status, db_connectivity_output = run_ssh_command(sensor_ip, 'sensorz', 'sensorz1234',
                                                                     "nc -zv db_host 3306")

    return {
        'Data Transmission': (data_transmission_status, data_transmission_output),
        'Database Connectivity': (db_connectivity_status, db_connectivity_output)
    }


def generate_report(sensor, test_results):
    print(f"\nResults for Sensor {sensor['hostname']} ({sensor['ip']}):")
    for test_category, results in test_results.items():
        print(f"\n{test_category}:")
        for test_name, (status, output) in results.items():
            status_text = 'Success' if status else 'Failure'
            print(f"- {test_name}: {status_text}\n  Output: {output}")


def cleanup():
    pass


if __name__ == "__main__":
    for sensor in sensors:
        test_results = {
            'Connectivity Test': connectivity_test(sensor['ip'], sensor['hostname']),
            'Performance Test': performance_test(sensor['ip']),
            'Security Test': security_test(sensor['ip'], sensor['hostname']),
            'Compatibility Test': compatibility_test(sensor['ip']),
        }
        generate_report(sensor, test_results)

    cleanup()  # Call the cleanup function at the end
