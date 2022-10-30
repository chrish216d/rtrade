#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: chrish


import akshare as ak
import redis
import logging
from multiprocessing import Process


db = redis.StrictRedis(
    host='127.0.0.1',
    port=6379,
    db=0,
    password='',
    decode_responses=True)


def get_stock_gms(code):
    df = ak.stock_zh_a_hist(
        symbol=code,
        period='daily',
        start_date='20000101',
        adjust='qfq',
    )
    for x in df[['日期', '开盘', '收盘', '成交量']].values:
        key, open_, close_, vol = x
        gms = vol if close_ > open_ else 0 - vol if close_ < open_ else 0
        db.hincrby(key, 'vol', vol)
        db.hincrby(key, 'gms', gms)  # gain minus slip


def get_gms(index):
    logging.basicConfig(
        level=logging.INFO,
        filename='gms_%d.log' % index,
        filemode='w',
        format='%(message)s',
    )
    with open('acodes_%d' % index, 'r') as f:
        count = 0
        for line in f:
            code = line.strip()
            get_stock_gms(code)
            logging.info(code)
            count = count + 1
            print('%d: %s %d' % (index, code, count))


if __name__ == '__main__':
    plist = list()
    n_ = 8
    for i in range(1, 1 + n_):
        proc = Process(target=get_gms, args=(i,))
        proc.start()
        plist.append(proc)
    for p in plist:
        p.join()
