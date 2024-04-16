import subprocess
import sys

print(f"Using Python interpreter: {sys.executable}")


def run_script(script_path):
    python_executable = sys.executable  # Gets the Python interpreter path currently running the script
    result = subprocess.run([python_executable, script_path], capture_output=True, text=True)
    print('STDOUT:', result.stdout)
    print('STDERR:', result.stderr)


def main():
    scripts = [
        r'C:\Users\Roy Avrahami\PycharmProjects\sensorz_qa_roy\check_ping_sensors.py',
        r'C:\Users\Roy Avrahami\PycharmProjects\sensorz_qa_roy\detect_package_manager_and_install.py',
        r'C:\Users\Roy Avrahami\PycharmProjects\sensorz_qa_roy\ssh_commands_test_sensors_tests.py'
    ]

    for script in scripts:
        print(f"Running script: {script}")
        run_script(script)


if __name__ == '__main__':
    main()
