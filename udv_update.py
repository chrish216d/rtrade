#!/usr/bin/env python
# -*- coding:utf-8 -*-

from udv_data import fetch_sh1_index, update_udv_csv
from udv_vis import vis_udv_data
import time
import os


def update_test():
    data = fetch_sh1_index()
    # load udv rows
    with open('_udv_rows', 'r') as f:
        rows = f.read().strip()
    _sh1_rows = len(data['close'])
    return _sh1_rows == rows


def update_udv1():
    path = 'data/udv_s20000101.csv'
    update_udv_csv(path)
    rows = vis_udv_data(path, add_sh1=False)
    # TODO: upload
    print('done.')
    # record udv rows
    with open('_udv_rows', 'w') as f:
        f.write(str(rows))


def update_udv2():
    path = 'data/udv_s20000101.csv'
    vis_udv_data(path, add_sh1=True)
    # TODO: upload
    print('done.')


def update_udv_proc():
    # backup data before udpate
    os.system('rm -r data.bk')
    os.system('cp -r data data.bk')
    # TODO
    # update udv before 14:00
    curr_hr = time.localtime().tm_hour
    if curr_hr < 16:
        update_udv1()
    else:  # add sh1 index after 14:00
        if update_test():
            update_udv2()
            print('done.')
            return
        print('wait for sh1...')


if __name__ == '__main__':
    update_udv_proc()
