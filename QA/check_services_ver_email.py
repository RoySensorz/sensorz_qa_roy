import requests
import yaml
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

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


def fetch_chart_yaml(repo_path):
    """Fetches the Chart.yaml content and processes it into a dictionary of services and versions."""
    chart_url = f"https://raw.githubusercontent.com/{repo_path}/main/Chart.yaml"
    response = requests.get(chart_url, headers=headers)
    if response.status_code == 200:
        chart_yaml = yaml.safe_load(response.text)
        services_versions = {dep['name']: dep['version'] for dep in chart_yaml.get('dependencies', [])}
        return services_versions
    else:
        print(f"Failed to fetch Chart.yaml from {repo_path} with status code {response.status_code}")
        return {}


def compare_versions(environment_versions):
    """Compares versions across environments and identifies differences."""
    all_services = set()
    for versions in environment_versions.values():
        all_services.update(versions.keys())

    differences = {}
    for service in all_services:
        seen_versions = {env: versions.get(service, "Missing") for env, versions in environment_versions.items()}
        if len(set(seen_versions.values())) > 1:
            differences[service] = seen_versions
    return differences


def write_html_report(environments_versions, differences):
    """Generates an HTML report of version differences across environments."""
    date_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"services_versions_{date_time_str}.html"
    file_path = os.path.join("/mnt/data", file_name)

    with open(file_path, 'w') as file:
        file.write(
            "<html><head><style>td, th {border: 1px solid #ddd; padding: 8px;} .diff {color: red;} .same {color: "
            "green;} th {padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #04AA6D; color: "
            "white;}</style></head><body>")
        file.write(f"<h2>Services Versions Across Environments - {date_time_str}</h2>")
        for env, services in environments_versions.items():
            file.write(f"<h3>{env} Environment</h3><table><tr><th>Service</th><th>Version</th></tr>")
            for service, version in services.items():
                color_class = "diff" if service in differences else "same"
                file.write(f"<tr class='{color_class}'><td>{service}</td><td>{version}</td></tr>")
            file.write("</table><br>")
        file.write("</body></html>")
    return file_path


def send_email(subject, body, to_addresses, attachment_path):
    """Sends an email with the report attached."""
    from_address = "roy.avrahami@sensorz.io"
    email_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = "smtp-mail.outlook.com"
    smtp_port = 587

    message = MIMEMultipart()
    message['From'] = from_address
    message['To'] = ", ".join(to_addresses)
    message['Subject'] = subject
    message.attach(MIMEText(body))

    with open(attachment_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
        message.attach(part)

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(from_address, email_password)
    server.sendmail(from_address, to_addresses, message.as_string())
    server.quit()


def main():
    """Main function to orchestrate the version comparison and email sending."""
    environment_versions = {}
    for env, repo_path in environments_info.items():
        services_versions = fetch_chart_yaml(repo_path)
        environment_versions[env] = services_versions

    differences = compare_versions(environment_versions)
    report_path = write_html_report(environment_versions, differences)
    send_email(
        subject="Daily Service Versions Report",
        body="Attached is the daily service versions report.",
        to_addresses=["person1@example.com", "person2@example.com"],
        attachment_path=report_path
    )


if __name__ == "__main__":
    main()
