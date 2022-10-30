#!/usr/bin/env python
# -*- coding:utf-8 -*-


from datetime import datetime, date
import redis
import json
import csv
import pandas as pd
import numpy as np
import akshare as ak


db = redis.StrictRedis(
    host='127.0.0.1',
    port=6379,
    db=0,
    password='',
    decode_responses=True)


def get_dates():
    y_date = db.keys()
    return sorted(y_date, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))


udv_csv = 'data/udv_s20000101.csv'


def get_udv_csv():
    with open(udv_csv, 'w') as f:
        f.write('DATE,UDV,GMS,VOL\n')
        for date_ in get_dates():
            res = db.hgetall(date_)
            udv = round(float(res['gms']) / float(res['vol']) * 100, 3)
            line = '%s,%s,%s,%s\n' % (date_, str(udv), res['gms'], res['vol'])
            f.write(line)


def get_sh1():
    df = ak.stock_zh_index_daily(symbol='sh000001')
    df = df[df['date'] > date(2000, 1, 1)]
    max_, min_ = df['close'].max(), df['close'].min()
    range_ = max_ - min_
    df['nclose'] = df['close'].apply(
        lambda x: (x - min_) / range_ * 240 - 120
    )
    return {
        'close': df['nclose'].values,
        'change': (df['close'] - df['open']).values,
    }


def udv_csv_to_df():
    d = []
    with open(udv_csv) as f:
        f_csv = csv.reader(f)
        next(f_csv)  # headers
        for row in f_csv:
            d.append(row)
    df = pd.DataFrame(d, columns=['date', 'udv', 'gms', 'vol'])
    df['udv'] = df['udv'].astype(float)
    df['udv_5'] = round(df['udv'].rolling(5).mean(), 3)
    df['udv_10'] = round(df['udv'].rolling(10).mean(), 3)
    df['udv_20'] = round(df['udv'].rolling(20).mean(), 3)
    sh1 = get_sh1()
    df['sh1'] = sh1['close']
    df['sh1_chg'] = sh1['change']
    # print(df.tail(50))
    return df


def process_udv():
    df = udv_csv_to_df()

    df['udv_r'] = df['udv'].shift()
    df['udv_5_r'] = df['udv_5'].shift()
    df['udv_10_r'] = df['udv_10'].shift()
    df['udv_20_r'] = df['udv_20'].shift()

    df['dd'] = df['udv_5'] - df['udv_20']
    df['dd_min5'] = df['dd'].rolling(5).min()

    # break out 1
    bo1 = df[(df['udv_5_r'] < df['udv_10_r']) & (df['udv_5_r'] < df['udv_20_r']) &
             (df['udv_5'] > df['udv_10']) & (df['udv_5'] < df['udv_20'])]

    # break out 2
    bo2 = df[(df['udv_5_r'] > df['udv_10_r']) & (df['udv_5_r'] > df['udv_20_r']) &
             (df['udv_5'] < df['udv_10']) & (df['udv_5'] < df['udv_20'])]

    # sig1(27,9,0)
    sig1 = df[(df['dd_min5'] < -30) & (df['udv_20'] < 10) & (df['udv_20'] > -10) &
              (df['sh1_chg'] > 0) & (df['sh1'] < -20) &
              (df['udv_5_r'] < df['udv_20_r']) &
              (df['udv_5'] > df['udv_20']) &
              (df['udv_20'] > df['udv_20_r'])]

    output = {
        'date': list(df['date'].values),
        'udv': list(df['udv'].values),
        'udv_5': ['.' if np.isnan(x) else x for x in df['udv_5'].values],
        'udv_10': ['.' if np.isnan(x) else x for x in df['udv_10'].values],
        'udv_20': ['.' if np.isnan(x) else x for x in df['udv_20'].values],
        'sh1':  ['.' if np.isnan(x) else x for x in df['sh1'].values],
        'bo1': [{'xAxis': x} for x in bo1['date'].values],
        'bo2': [{'xAxis': x} for x in bo2['date'].values],
        'sig1': [{'xAxis': x} for x in sig1['date'].values]
    }

    with open('data/udv.json', 'w') as f:
        json.dump(output, f)


# get_udv_csv()
process_udv()
