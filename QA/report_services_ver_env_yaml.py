import requests
import os
import yaml
from datetime import datetime

# Define GitHub API URL and personal access token
GITHUB_API_URL = "https://api.github.com"
YOUR_PERSONAL_ACCESS_TOKEN = os.getenv('GITHUB_PAT')

# Headers for GitHub API requests, including authorization token
headers = {
    "Authorization": f"token {YOUR_PERSONAL_ACCESS_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Manually specified environments and their GitHub repository paths
environments_info = {
    "staging": "sensorz/staging",
    "singtel": "sensorz/singtel",
    "drc": "sensorz/drc",
    "qa": "sensorz/qa",
    "develop": "sensorz/develop",
    "poc": "sensorz/poc",
    "globe": "sensorz/globe"
}

# GitHub repository base URL for easy access links
GITHUB_REPO_BASE_URL = "https://github.com"


def fetch_chart_yaml(repo_path):
    """Fetches the Chart.yaml content from the specified repository."""
    chart_url = f"https://raw.githubusercontent.com/{repo_path}/main/Chart.yaml"
    response = requests.get(chart_url, headers=headers)
    return yaml.safe_load(response.text) if response.status_code == 200 else None


def compare_versions(environment_versions):
    """Compares versions across environments and marks differences."""
    all_services = set()
    for versions in environment_versions.values():
        all_services.update(versions.keys())

    differences = {}
    for service in all_services:
        seen_versions = {env: versions.get(service, {}).get("version", "Missing") for env, versions in
                         environment_versions.items()}
        if len(set(seen_versions.values())) > 1:  # If there's more than one unique version
            differences[service] = seen_versions

    return differences


def write_html_report(environments_versions, differences):
    """Writes the collected version information to an HTML file, including differences."""
    date_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    directory_path = os.path.join(os.getenv('USERPROFILE'), "Documents", "Services in each environment automation")

    # Ensure the directory exists
    if not os.path.exists(directory_path):
        print(f"Creating directory: {directory_path}")
        os.makedirs(directory_path)

    file_path = os.path.join(directory_path, f"services_versions_{date_time_str}.html")

    with open(file_path, 'w') as file:
        file.write(
            "<html><head><style>td, th {border: 1px solid #ddd; padding: 8px;} .diff {color: red;} .same {color: "
            "green;} th {padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #04AA6D; color: "
            "white;}</style></head><body>")
        file.write(f"<h2>Services Versions Across Environments - {date_time_str}</h2>")

        for env, services in environments_versions.items():
            # Repository URL for the environment
            repo_url = f"https://github.com/sensorz/{env}"
            file.write(f"<h3><a href='{repo_url}' target='_blank'>{env} Environment</a></h3>")
            file.write("<table><tr><th>Service</th><th>Version</th><th>Repository</th></tr>")

            for service, info in services.items():
                if service in differences:
                    color_class = "diff"
                else:
                    color_class = "same"
                version = info.get('version', 'Missing')
                repository = info.get('repository', 'Missing')
                file.write(f"<tr class='{color_class}'><td>{service}</td><td>{version}</td><td>{repository}</td></tr>")

            file.write("</table><br>")

        # Include a summary of differences and similarities
        file.write("</body></html>")

    print(f"Services versions report written to {file_path}")


def main():
    """Main function to process each environment and generate a comparison report."""
    environment_versions = {}
    for env, repo_path in environments_info.items():
        chart_info = fetch_chart_yaml(repo_path)
        environment_versions[env] = {
            dep['name']: {"version": dep.get('version', 'Missing'), "repository": dep.get('repository', 'Missing')} for
            dep in chart_info.get('dependencies', [])} if chart_info else {}

    differences = compare_versions(environment_versions)
    write_html_report(environment_versions, differences)


if __name__ == "__main__":
    main()
