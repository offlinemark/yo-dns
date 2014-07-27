#!/usr/bin/env python

import worker
import sqlite3 as sql
import multiprocessing
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        domain = request.form['domain']
        cname = request.form['cname']

        conn = sql.connect('yodns.db')
        c = conn.cursor()
        c.execute('insert into yodns (username, domain, cname) values (?,?,?)',
                  (username, domain, cname))
        conn.commit()
        conn.close()

        return render_template('index.html', submitted=True)

    return render_template('index.html')

if __name__ == '__main__':
    p = multiprocessing.Process(target=worker.worker)
    p.start()
    app.run()
