#!/usr/bin/env python
# -*- coding:utf-8 -*-


import json
import pandas as pd
import numpy as np
from udv_data import fetch_sh1_index


def load_udv_csv(path) -> pd.DataFrame:
    data = list()
    with open(path, 'r') as f:
        data = [x.split(',') for x in f.readlines()[1:]]
    df = pd.DataFrame(data, columns=['date', 'udv', 'gms', 'vol'])
    df['udv'] = df['udv'].astype(float)
    # 均线
    df['udv5'] = round(df['udv'].rolling(5).mean(), 3)
    df['udv10'] = round(df['udv'].rolling(10).mean(), 3)
    df['udv20'] = round(df['udv'].rolling(20).mean(), 3)
    # print(df.tail(50))
    return df


def add_sh1_index(df) -> pd.DataFrame:
    sh1 = fetch_sh1_index()
    df['sh1'] = sh1['close']
    df['sh1_chg'] = sh1['change']
    # print(df.tail(50))
    return df


def vis_udv_data(path, add_sh1=False):
    df = load_udv_csv(path)

    # REF
    df['udv_r'] = df['udv'].shift()
    df['udv5_r'] = df['udv5'].shift()
    df['udv10_r'] = df['udv10'].shift()
    df['udv20_r'] = df['udv20'].shift()

    # DF5_20 = 5日均线-20日均线
    df['df5_20'] = df['udv5'] - df['udv20']
    df['df5_20_min5'] = df['df5_20'].rolling(5).min()

    # break-out-1: 5日金叉10日和20日
    '''
    bo1 = df[
        (df['udv5_r'] < df['udv10_r']) & (df['udv5_r'] < df['udv20_r']) &
        (df['udv5'] > df['udv10']) & (df['udv5'] > df['udv20'])
    ]
    # break-out-2: 5日死叉10日和20日
    bo2 = df[
        (df['udv5_r'] > df['udv10_r']) & (df['udv5_r'] > df['udv20_r']) &
        (df['udv5'] < df['udv10']) & (df['udv5'] < df['udv20'])
    ]
    '''

    # 连续10天量柱>-10/
    df['du_0'] = df['udv'].apply(lambda x: 1 if x > 0 else 0)
    df['du_n10'] = df['udv'].apply(lambda x: 1 if x > -10 else 0)
    df['tu_0'] = df['du_0'].rolling(10).sum()
    df['tu_n10'] = df['du_n10'].rolling(10).sum()
    tu1d = df[
        (df['tu_0'] >= 9)
    ]
    tu2d = df[
        (df['tu_n10'] >= 9)
    ]

    # hit-1: 20日撞击-10

    output = {
        'date': list(df['date'].values),
        'udv': list(df['udv'].values),
        'udv5': to_no_nan_list(df['udv5'].values),
        'udv10': to_no_nan_list(df['udv10'].values),
        'udv20': to_no_nan_list(df['udv20'].values),
        # 'bo1': to_markline_data(bo1['date'].values),
        # 'bo2': to_markline_data(bo2['date'].values),
        'tu_0': to_no_nan_list(df['tu_0'].values),
        'tu_n10': to_no_nan_list(df['tu_n10'].values),
        'tu1d': to_markline_data(tu1d['date'].values),
        'tu2d': to_markline_data(tu2d['date'].values),
    }

    if add_sh1:
        # 叠加上证指数
        add_sh1_index(df)
        # 测试信号1: 底部反转买入
        """
        1. 最近5日内 ma5 和 ma20 差值的最小值小于 vars[0].
        2. ma5 上穿 ma20.
        3. ma20 跟上一个交易日相比上涨.
        4. ma20 绝对值小于 vars[1].
        5. 上证指数当日上涨.
        6. 上证指数百分比收盘价小于 vars[2].
        (1是撞击条件, 235构成反转信号, 46过滤高位)
        """
        vars = [-30, 10, -20]
        sig1 = df[
            (df['df5_20_min5'] < vars[0]) &  # cond1
            (df['udv5_r'] < df['udv20_r']) & (df['udv5'] > df['udv20']) &  # cond2
            (df['udv20'] > df['udv20_r']) &  # cond3
            (df['udv20'] < vars[1]) & (df['udv20'] > 0-vars[1]) &  # cond4
            (df['sh1_chg'] > 0) &  # cond5
            (df['sh1'] < vars[2])  # cond6
        ]
        # 添加输出
        output['sh1'] = list(df['sh1'].values)
        output['sig1'] = to_markline_data(sig1['date'].values)

    with open('data/vis_udv.json', 'w') as f:
        json.dump(output, f)

    # return rows
    return df.shape[0]


def to_no_nan_list(data):
    return ['.' if np.isnan(x) else x for x in data]


def to_markline_data(data):
    return [{'xAxis': x} for x in data]


if __name__ == '__main__':
    path = 'data/udv_s20000101.csv'
    vis_udv_data(path, add_sh1=False)
