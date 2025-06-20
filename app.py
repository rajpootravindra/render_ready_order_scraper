from flask import Flask, render_template, request
from fetch_orders import scrape_orders_for_date
import os
import logging

app = Flask(__name__)

# Setup logging to a file and console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    logs = []
    if request.method == 'POST':
        target_date = request.form.get('target_date')
        try:
            logs.append("Starting order scraping for date: " + target_date)
            result_logs = scrape_orders_for_date(target_date)
            logs.extend(result_logs)
            message = "✅ Process completed. Check logs for details."
        except Exception as e:
            message = f"❌ Error occurred: {e}"
            logs.append(str(e))
    return render_template('index.html', message=message, logs=logs)

if __name__ == '__main__':
    app.run(debug=True)
