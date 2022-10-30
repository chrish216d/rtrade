#!/usr/bin/env python
# -*- coding:utf-8 -*-


from datetime import datetime
import redis
import json
import csv

db = redis.StrictRedis(
    host='127.0.0.1',
    port=6379,
    db=0,
    password='',
    decode_responses=True)


def get_dates():
    y_date = db.keys()
    return sorted(y_date, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))


def get_dkl():
    with open('data/dkl_20000101_20221028.csv', 'w') as f:
        f.write('DATE,DKL\n')
        for date in get_dates():
            res = db.hgetall(date)
            dkl = round(float(res['gms']) / float(res['vol']) * 100, 3)
            line = '%s,%s\n' % (date, str(dkl))
            f.write(line)


def dkl_to_json():
    data = []
    with open('data/dkl_20000101_20221028.csv') as fc:
        f_csv = csv.reader(fc)
        next(f_csv)  # headers
        for row in f_csv:
            data.append(row)
    with open('data/dkl.json', 'w') as fj:
        json.dump(data, fj)


# get_dkl()
dkl_to_json()