import requests
from openpyxl import Workbook
from openpyxl.styles import Font
import yaml

# ---------------------------------------
# Configuration
# ---------------------------------------
environments = {
    "singtel": "https://github.com/sensorz/singtel/blob/main/Chart.yaml",
    "poc": "https://github.com/sensorz/poc/blob/main/Chart.yaml",
    "staging": "https://github.com/sensorz/staging/blob/main/Chart.yaml",
    "drc": "https://github.com/sensorz/drc/blob/main/Chart.yaml",
    "qa": "https://github.com/sensorz/qa/blob/main/Chart.yaml",
    "develop": "https://github.com/sensorz/develop/blob/main/Chart.yaml",
    "globe": "https://github.com/sensorz/globe/blob/main/Chart.yaml"
}

output_file = "environment_services.xlsx"  # Output Excel filename


# ---------------------------------------
# Functions
# ---------------------------------------

def fetch_chart_yaml(url):
    """Fetches the raw Chart.yaml content from a GitHub URL."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request fails
    return response.text


def parse_chart_yaml(yaml_content):
    """Parses the Chart.yaml content and extracts service names."""
    data = yaml.safe_load(yaml_content)
    services = [dep['name'] for dep in data.get('dependencies', [])]
    return services


def create_excel_file(data):
    """Creates an Excel file and populates it with the data."""
    workbook = Workbook()
    sheet = workbook.active

    # Header row
    sheet['A1'] = "Environment"
    sheet['B1'] = "Service"
    sheet['C1'] = "GitHub Link"
    sheet['A1'].font = sheet['B1'].font = sheet['C1'].font = Font(bold=True)

    # Data rows
    row_num = 2
    for env, services in data.items():
        for service in services:
            sheet[f'A{row_num}'] = env
            sheet[f'B{row_num}'] = service
            sheet[f'C{row_num}'] = environments[env]
            row_num += 1

    workbook.save(filename=output_file)


# ---------------------------------------
# Main Script Logic
# ---------------------------------------

if __name__ == "__main__":
    data = {}  # Dictionary to store environment and service data

    for env_name, chart_url in environments.items():
        yaml_content = fetch_chart_yaml(chart_url)
        services = parse_chart_yaml(yaml_content)
        data[env_name] = services

    create_excel_file(data)
    print("Excel file created successfully!")
