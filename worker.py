#!/usr/bin/env python

import time
import logging
import requests
import dns.resolver
import config as CFG
import sqlite3 as sql

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.FileHandler('logs/app.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

def worker():
    while True:
        conn = sql.connect(CFG.DB)
        c = conn.cursor()
        c.execute('select * from yodns')
        for row in c.fetchall():
            pk, username, domain, cname = row
            if check_cname(domain, cname):
                log.debug('[+] Sending yo to: {}'.format(username))
                if 'exceeded' in yo(username):
                    log.debug('[!] {} is rate limited. Not deleting.'.format(row))
                else:
                    log.debug('[+] Deleting {} from db'.format(row))
                    delete_row(conn, pk)
        conn.close()
        time.sleep(CFG.DELAY)

def yo(username):
    payload = {'username': username, 'api_token': CFG.APIKEY}
    r = requests.post('http://api.justyo.co/yo/', payload)
    return r.text

def check_cname(domain, cname):
    """
        Checks whether the given @cname string is contained in any DNS
        query responses for @domain.

        Returns 1 on success, 0 on failure.
    """

    try:
        query = dns.resolver.query(domain, 'CNAME')
    except:
        return 0
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
