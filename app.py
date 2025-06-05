import os
import subprocess
import json
from flask import Flask, request, render_template, send_from_directory
from datetime import datetime
import pandas as pd

app = Flask(__name__)


def run_pylint(file_path):
    result = subprocess.run(['pylint', '--output-format=json', file_path], capture_output=True, text=True)
    try:
        return json.loads(result.stdout) if result.stdout else []
    except json.JSONDecodeError:
        return []


def run_bandit(file_path):
    result = subprocess.run(['bandit', '-f', 'json', '-o', '-', file_path], capture_output=True, text=True)
    try:
        bandit_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    
    issues = []
    for issue in bandit_data.get('results', []):
        issues.append({
            'test_id': issue.get('test_id', 'N/A'),
            'filename': issue.get('filename', 'N/A'),
            'issue_text': issue.get('issue_text', 'N/A'),
            'line_number': issue.get('line_number', 'N/A'),
            'severity': issue.get('severity', 'N/A'),
            'confidence': issue.get('confidence', 'N/A')
        })
    return issues


def create_html_report(pylint_report, bandit_report, report_name):
    pylint_df = pd.DataFrame(pylint_report)
    bandit_df = pd.DataFrame(bandit_report)
    
    with open(f"reports/{report_name}_combined.html", 'w', encoding='utf-8') as f:
        f.write("<html><head><style>table {border-collapse: collapse; width: 100%;} td, th {border: 1px solid black; padding: 8px; text-align: left;} th {background-color: #f2f2f2;}</style></head><body>")
        f.write("<h2> کیفیت کد و  استانداردهای کدنویسی</h2>")
        f.write(pylint_df.to_html(index=False, escape=False))
        f.write("<h2> آسیب‌پذیری‌های امنیتی</h2>")
        if not bandit_df.empty:
            f.write(bandit_df.to_html(index=False, escape=False))
        else:
            f.write("<p>No issues found by Bandit.</p>")
        f.write("</body></html>")


def create_excel_report(pylint_report, bandit_report, report_name):
    pylint_df = pd.DataFrame(pylint_report)
    bandit_df = pd.DataFrame(bandit_report)

    excel_path = f"reports/{report_name}.xlsx"
    
    with pd.ExcelWriter(excel_path) as writer:
        pylint_df.to_excel(writer, sheet_name="Pylint Report", index=False)
        bandit_df.to_excel(writer, sheet_name="Bandit Report", index=False)

    return excel_path


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if not file.filename.endswith('.py'):
        return 'Invalid file type. Only Python (.py) files are allowed.', 400

    file_path = os.path.join('uploads', file.filename)
    file.save(file_path)

    pylint_report = run_pylint(file_path)
    bandit_report = run_bandit(file_path)

    report_name = f"code_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    
    create_html_report(pylint_report, bandit_report, report_name)

    
    create_excel_report(pylint_report, bandit_report, report_name)

    return render_template('download.html', report_name=report_name)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('reports', filename, as_attachment=True)


if __name__ == "__main__":
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('reports'):
        os.makedirs('reports')
    app.run(debug=False)
