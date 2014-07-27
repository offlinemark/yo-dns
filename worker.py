#!/usr/bin/env python

import time
import requests
import dns.resolver
import config as CFG
import logging as log
import sqlite3 as sql

log.basicConfig(format='%(asctime)s - %(message)s', level=log.INFO)

def worker():
    while True:
        log.info('[+] Beginning loop')
        conn = sql.connect('yodns.db')
        c = conn.cursor()
        c.execute('select * from yodns')
        for row in c.fetchall():
            pk, username, domain, cname = row
            rc = check_cname(domain, cname)
            if rc:
                if rc == 1:
                    log.info('[+] Sending yo to {}'.format(username))
                    if 'exceeded' in yo(username):
                        log.info('[!] {} is rate limited. Not deleting.'.format(row))
                        continue
                log.info('[+] Deleting {} from db'.format(row))
                delete_row(conn, pk)
        conn.close()
        log.info('[+] Sleeping for {} seconds'.format(CFG.DELAY))
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
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
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
