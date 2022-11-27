#!/usr/bin/env python
# -*- coding:utf-8 -*-


import akshare as ak
import json
from datetime import datetime


def fetch_udv2():
    df = ak.stock_zh_a_spot_em()
    names = {
        '代码': 'code',
        '名称': 'name',
        '涨跌幅': 'chg',
        '今开': 'open',
        '最新价': 'close',
        '昨收': 'rclose',
        '成交量': 'vol',
        '成交额': 'amt',
        '流通市值': 'cmv',
    }
    df.rename(columns=names, inplace=True)
    df = df[names.values()]
    df['tvr'] = round(df['amt'] / df['cmv'] * 100, 3)  # total vol ratio
    df['uv'] = df.apply(
        lambda x: x['vol'] if x['close'] > x['rclose']
        and x['close'] > x['open'] else 0,
        axis=1
    )
    df['dv'] = df.apply(
        lambda x: x['vol'] if x['close'] < x['rclose']
        and x['close'] < x['open'] else 0,
        axis=1
    )
    df['chg'] = df['chg'].apply(
        lambda x: '%.3f' % x
    )
    # filter
    df['filter'] = df.apply(
        lambda x: 0 if x['code'][:3] == '688'
        or x['name'].find('ST') >= 0 else 1,
        axis=1
    )
    tuv = df['uv'].sum()
    tdv = df['dv'].sum()
    udf = df[(df['uv'] > 0) & df['filter'] == 1].copy()
    ddf = df[(df['dv'] > 0) & df['filter'] == 1].copy()
    udf['tvp'] = udf['uv'].apply(
        lambda x: '%.3f' % round(x / tuv * 100, 3)
    )
    ddf['tvp'] = ddf['dv'].apply(
        lambda x: '%.3f' % round(x / tdv * 100, 3)
    )
    filter = ['code', 'name', 'chg', 'uv', 'dv', 'tvr', 'tvp']
    n_ = 50
    udf1 = udf.sort_values(by='uv', ascending=False)[:n_][filter]
    udf2 = udf.sort_values(by='tvr', ascending=False)[:n_][filter]
    udf2['tvr'] = udf2['tvr'].apply(
        lambda x: '%.3f' % x
    )
    ddf1 = ddf.sort_values(by='dv', ascending=False)[:n_][filter]
    ddf2 = ddf.sort_values(by='tvr', ascending=False)[:n_][filter]
    ddf2['tvr'] = ddf2['tvr'].apply(
        lambda x: '%.3f' % x
    )
    date_ = datetime.strftime(datetime.today(), '%Y%m%d')
    output = {
        'udf1_code': list(udf1['code'].values),
        'udf1_name': list(udf1['name'].values),
        'udf1_chg': list(udf1['chg'].values),
        'udf1_tvp': list(udf1['tvp'].values),
        'udf2_code': list(udf2['code'].values),
        'udf2_name': list(udf2['name'].values),
        'udf2_chg': list(udf2['chg'].values),
        'udf2_tvr': list(udf2['tvr'].values),
        'ddf1_code': list(ddf1['code'].values),
        'ddf1_name': list(ddf1['name'].values),
        'ddf1_chg': list(ddf1['chg'].values),
        'ddf1_tvp': list(ddf1['tvp'].values),
        'ddf2_code': list(ddf2['code'].values),
        'ddf2_name': list(ddf2['name'].values),
        'ddf2_chg': list(ddf2['chg'].values),
        'ddf2_tvr': list(ddf2['tvr'].values),
    }
    with open('data/udv2_%s.json' % date_, 'w') as f:
        json.dump(output, f)
    with open('data/udv2_latest.json', 'w') as f:
        json.dump(output, f)
    print(output)


fetch_udv2()
