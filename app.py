
from flask import Flask, render_template, request, flash, redirect
from threading import Thread
from fetch_orders import run_order_scraper

app = Flask(__name__)
app.secret_key = 'some-secret-key'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        date = request.form['date']
        Thread(target=run_order_scraper, args=(date,)).start()
        flash('Order scraping started!', 'success')
        return redirect('/')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
