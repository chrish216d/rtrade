#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: chrish


import akshare as ak
import redis
import logging
from multiprocessing import Process
from datetime import datetime, date


db = redis.StrictRedis(
    host='127.0.0.1',
    port=6379,
    db=0,
    password='',
    decode_responses=True)


def fetch_stock_gms(code):
    """
    获取从20000101至今(20221028)1D数据
    https://akshare.akfamily.xyz/data/stock/stock.html#id18
    """
    df = ak.stock_zh_a_hist(
        symbol=code,
        period='daily',
        start_date='20000101',
        adjust='qfq',
    )
    # GMS(gain-minus-slip): 上涨成交量减去下跌成交量
    for x in df[['日期', '开盘', '收盘', '成交量']].values:
        key, open_, close_, vol = x
        gms = vol if close_ > open_ else 0 - vol if close_ < open_ else 0
        db.hincrby(key, 'vol', vol)
        db.hincrby(key, 'gms', gms)


def fetch_gms_worker(id):
    logging.basicConfig(
        level=logging.INFO,
        filename='gms_%d.log' % id,
        filemode='w',
        format='%(message)s',
    )
    with open('acodes_%d' % id, 'r') as f:
        count = 0
        for line in f:
            code = line.strip()
            fetch_stock_gms(code)
            count = count + 1
            message = '%d: %s %d' % (id, code, count)
            logging.info(message)
            print(message)


def fetch_gms_proc():
    plist = list()
    pn = 8
    for i in range(0, pn):
        proc = Process(target=fetch_gms_worker, args=(i+1,))
        proc.start()
        plist.append(proc)
    for p in plist:
        p.join()


def get_udv_dates():
    """
    取交易日序列用作x轴数据, 按日期排序
    """
    dates = db.keys()
    return sorted(dates, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))


def output_udv_csv(path):
    with open(path, 'w') as f:
        f.write('DATE,UDV,GMS,VOL\n')  # headers
        for date_ in get_udv_dates():
            res = db.hgetall(date_)
            udv = round(float(res['gms']) / float(res['vol']) * 100, 3)
            line = '%s,%s,%s,%s\n' % (date_, str(udv), res['gms'], res['vol'])
            f.write(line)


def fetch_sh1_index():
    """
    获取从20000101至今上证指数1D数据
    https://akshare.akfamily.xyz/data/stock/stock.html#id41
    """
    df = ak.stock_zh_index_daily(symbol='sh000001')
    df = df[df['date'] > date(2000, 1, 1)]
    # print(df)
    # close 转化成百分比坐标
    max_, min_ = df['close'].max(), df['close'].min()
    range_ = max_ - min_
    # 区间 [-120,120] 用于可视化
    df['nclose'] = df['close'].apply(
        lambda x: round((x - min_) / range_ * 240 - 120, 3))
    return {
        'close': df['nclose'].values,
        # TODO: 输出K线
        'change': (df['close'] - df['open']).values,  # 记录当日涨跌
    }


def update_udv_csv(path):
    """
    收盘后获取A股每日行情数据
    https://akshare.akfamily.xyz/data/stock/stock.html#id9
    """
    df = ak.stock_zh_a_spot_em()
    names = {'今开': 'open', '最新价': 'close', '成交量': 'vol'}
    df.rename(columns=names, inplace=True)
    df = df[['open', 'close', 'vol']].astype(float)
    df['gms'] = df.apply(
        lambda x: x['vol'] if x['close'] > x['open'] else
        0 - x['vol'] if x['close'] < x['open'] else 0,
        axis=1
    )
    vol = int(df['vol'].sum())
    gms = int(df['gms'].sum())
    udv = round(gms / vol * 100, 3)
    date_ = datetime.strftime(datetime.today(), '%Y-%m-%d')
    line = '%s,%s,%s,%s\n' % (date_, str(udv), str(gms), str(vol))
    print(line)
    with open(path, 'a') as f:
        f.write(line)


if __name__ == '__main__':
    fetch_gms_proc()
