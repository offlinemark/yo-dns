#!/usr/bin/env python

import re
import worker
import logging
import config as CFG
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

        for i, each in enumerate((username, domain, cname)):
            if i == 0:
                if not is_valid(each, 1):
                    return render_template('index.html', submit=True,
                                           error=True)
            else:
                if not is_valid(each):
                    return render_template('index.html', submit=True,
                                           error=True)
                
        conn = sql.connect(CFG.DB)
        c = conn.cursor()
        c.execute('insert into yodns (username, domain, cname) values (?,?,?)',
                  (username, domain, cname))
        conn.commit()
        conn.close()

        return render_template('index.html', submit=True, error=False)

    return render_template('index.html')

def is_valid(str, usr_flag=None):
    regex = '^\w+$' if usr_flag else '^(\w+\.)?\w+\.\w+\.?$'

    if len(str) > 50:
        return False

    return re.search(regex, str)

if __name__ == '__main__':
    p = multiprocessing.Process(target=worker.worker)
    p.start()
    logging.basicConfig(filename='logs/server.log',
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)
    app.run(debug=True, port=CFG.PORT, use_reloader=False)
