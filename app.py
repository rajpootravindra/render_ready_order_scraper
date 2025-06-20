
from flask import Flask, render_template, request, flash, redirect
from threading import Thread
from fetch_orders import run_order_scraper
import os

app = Flask(__name__)
app.secret_key = 'some-secret-key'
# Create log.txt if it doesn't exist
if not os.path.exists("log.txt"):
    with open("log.txt", "w") as f:
        f.write("📄 Log file created.\n")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        date = request.form['target_date']
        Thread(target=run_order_scraper, args=(date,)).start()
        flash('Order scraping started!', 'success')
        return redirect('/')
    return render_template('index.html')
@app.route("/logs")
def get_logs():
    try:
        with open("log.txt", "r") as f:
            content = f.read()
    except FileNotFoundError:
        content = "⚠️ No logs available yet. Start a scraping job first."
    return content

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
