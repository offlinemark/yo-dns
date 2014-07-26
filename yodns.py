#!/usr/bin/env python

import time
import thread
import requests
import dns.resolver
import sqlite3 as sql
import config as CFG
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

def backend():
    print '[+] Beginning loop'
    conn = sql.connect('yodns.db')
    c = conn.cursor()

    c.execute('select * from yodns')

    for row in c.fetchall():
        pk, username, domain, cname = row
        rc = check_cname(domain, cname)
        if rc:
            if rc == 1:
                print '[+] Sending yo to {}'.format(username)
                if 'exceeded' in yo(username):
                    print '[!] {} is rate limited. Not deleting.'.format(username)
                    continue
            print '[+] Deleting {} from db'.format(username)
            delete_row(conn, pk)

    conn.close()
    print '[+] Sleeping for {} seconds'.format(CFG.DELAY)
    time.sleep(CFG.DELAY)

def yo(username):
    payload = {'username': username, 'api_token': CFG.APIKEY}
    r = requests.post('http://api.justyo.co/yo/', payload)
    return r.text

def check_cname(domain, cname):
    """
        Checks whether the given @cname string is contained in any DNS
        query responses for @domain.

        Returns:
        -1: error, domain did not have a CNAME record
         1: success
         0: failure
    """

    try:
        query = dns.resolver.query(domain, 'CNAME')
    except dns.resolver.NoAnswer:
        return -1
    answers = query.response.answer
    for ans in answers:
        for each in ans.items:
            if cname in each.to_text():
                return 1
    return 0

def delete_row(conn, pk):
    c = conn.cursor()
    c.execute('delete from yodns where id=?', (pk,))
    conn.commit()

if __name__ == '__main__':
    app.run(debug=True)
