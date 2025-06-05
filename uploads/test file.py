import subprocess
import json
import pandas as pd
from datetime import datetime

# تابعی برای اجرای Pylint
def run_pylint(file_path):
    result = subprocess.run(['pylint', '--output-format=json', file_path], capture_output=True, text=True)
    return json.loads(result.stdout)

# تابعی برای اجرای Bandit
def run_bandit(file_path):
    result = subprocess.run(['bandit', '-f', 'json', '-o', '-', file_path], capture_output=True, text=True)
    
    try:
        # بارگذاری خروجی JSON از Bandit
        bandit_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("خطا در پردازش گزارش Bandit")
        return []

    issues = []
    for issue in bandit_data.get('results', []):  # Bandit خروجی به نام 'results' دارد
        issues.append({
            'test_id': issue.get('test_id', 'N/A'),
            'filename': issue.get('filename', 'N/A'),
            'issue_text': issue.get('issue_text', 'N/A'),
            'line_number': issue.get('line_number', 'N/A'),
            'severity': issue.get('severity', 'N/A'),
            'confidence': issue.get('confidence', 'N/A')
        })
    
    return issues

# تابعی برای ساخت گزارش Excel
def create_excel_report(pylint_report, bandit_report, report_name):
    pylint_df = pd.DataFrame(pylint_report)
    bandit_df = pd.DataFrame(bandit_report)
    
    # ایجاد گزارش Excel و ذخیره دو شیت مختلف
    with pd.ExcelWriter(f"reports/{report_name}.xlsx") as writer:
        pylint_df.to_excel(writer, sheet_name='Pylint Report', index=False)
        bandit_df.to_excel(writer, sheet_name='Bandit Report', index=False)

# تابعی برای ساخت گزارش HTML
def create_html_report(pylint_report, bandit_report, report_name):
    pylint_df = pd.DataFrame(pylint_report)
    bandit_df = pd.DataFrame(bandit_report)
    
    # ایجاد فایل HTML با دو بخش مختلف برای Pylint و Bandit
    with open(f"reports/{report_name}_combined.html", 'w', encoding='utf-8') as f:
        f.write("<html><head><style>table {border-collapse: collapse; width: 100%;} td, th {border: 1px solid black; padding: 8px; text-align: left;} th {background-color: #f2f2f2;}</style></head><body>")
        
        f.write("<h2>Pylint Report</h2>")
        f.write(pylint_df.to_html(index=False, escape=False))

        f.write("<h2>Bandit Report</h2>")
        
        # اضافه کردن شرط برای نمایش اگر گزارش Bandit خالی نباشد
        if not bandit_df.empty:
            f.write(bandit_df.to_html(index=False, escape=False))
        else:
            f.write("<p>No issues found by Bandit.</p>")

        f.write("</body></html>")

# اجرای تحلیل و ایجاد گزارش‌ها
def main():
    file_path = "example.py"  # فایل پایتون خود را اینجا قرار دهید
    pylint_report = run_pylint(file_path)
    bandit_report = run_bandit(file_path)

    # نام گزارش بر اساس تاریخ و زمان
    report_name = f"code_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # ایجاد گزارش‌های Excel و HTML
    create_excel_report(pylint_report, bandit_report, report_name)
    create_html_report(pylint_report, bandit_report, report_name)

    print(f"گزارش‌ها در قالب Excel و HTML ایجاد شد: {report_name}")

if __name__ == "__main__":
    main()
