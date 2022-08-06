# 常用函数库
import json
import pytz
from datetime import datetime
from types import SimpleNamespace
from ktrader_python import *
import pandas as pd
import numpy as np

class HelloWorld(python_strategy):
    # HelloWorld 是KTrader最简模板策略
    def __init__(self):
        # Class自带的初始化函数，每一个新的策略创建时会执行这个函数，
        # 可以在这里设置一些全局变量
        python_strategy.__init__(self)
        kt_info('Strategy Created: {}'.format(self))
        # Initialization

        self.context = '' # 初始化策略名称
        self.param = None # 初始化策略参数
        self.target_open = position_target() # 初始化目标仓位

    def update_config(self, cfg_path):
        # 加载 global_config.json 和 策略参数文件 double_ma.json
        kt_info('Loading strategy global config: {}'.format(cfg_path))
        f = open(cfg_path)
        # 加载策略参数文件 double_ma.json
        params = json.load(f, object_hook=lambda d: SimpleNamespace(**d)) # load json strategy config into object
        self.context = params.context
        self.param = params.params
        kt_info('Global config updated: {}'.format(self.param))
        return ''

    def init(self):
        # init 在每个交易日之前（回测）或策略启动时（实盘）触发, 用于策略初始化
        kt_info('Strategy Init: {}'.format(self.context))
        # 订阅合约
        self.api.subscribe_instrument(self.param.symbol)
        # 订阅K线数据
        self.api.subscribe_bars(self.param.symbol, 3)
        self.api.subscribe_bars(self.param.symbol, 4)
        current_time = format_time(get_time_now(), '')
        current_day = datetime.fromtimestamp(get_time_now() / 1e9, pytz.timezone('Asia/Shanghai')).date().strftime('%Y-%m-%d') # 获得当前日（自然日)
        kt_info('current day is: {}, trading_day is: {}, time is: {}'.format(current_day, get_trading_day(), current_time)) #显示时间信息

        # account summary 显示账户信息示例
        acc = self.api.get_account_summary()
        kt_info('Account Summary: 用户ID: {}, 持仓盈亏:{}, 手续费: {}, 净利润:{}, 最高净利: {}, 最低净利:{}'.format(acc.investor_id, acc.position_profit, acc.total_commission, acc.net_pnl, acc.net_pnl_high, acc.net_pnl_low))
        return

    def shutdown(self):
        # 安全退出策略
        kt_info('Strategy {} shutdown'.format(self.context))
        return

    def on_tick(self, t):
        # 对每一个Tick事件，做出相应交易动作, 策略编写的主要
        tick_time = format_time(int(t.timestamp), '')
        local_time = int(get_time_now())
        cur_date = int(format_time(local_time, "%Y%m%d"))

        # 获取当前tick时的账户净盈利(netpnl)
        acc = self.api.get_account_summary()

        # 获取策略参数的建仓开始时间、结束时间，建仓开始时间、结束时间，并转化成int(纳秒)
        build_start = parse_time(cur_date, self.param.build_start)
        build_end = parse_time(cur_date, self.param.build_end)
        reduce_start = parse_time(cur_date, self.param.reduce_start)
        reduce_end = parse_time(cur_date, self.param.reduce_end)

        # 打印出新来的tick
        kt_info('合约:{},时间:{},净利润:{},手续费:{},最新:{},最高:{},最低:{},买一:{},买一量:{},卖一:{},卖一量:{},成交量:{},增仓:{}'.format(
            t.instrument_id, tick_time, acc.net_pnl, round(acc.total_commission,2), t.last_price, t.highest_price, t.lowest_price, t.bid_price[0], t.bid_volume[0], t.ask_price[0], t.ask_volume[0], t.volume_delta, t.open_interest_delta))

        if self.param.symbol != t.instrument_id: # 检查合约名称是否是当前策略给定的
            return

        # 在给定时间建仓
        if t.timestamp > build_start and t.timestamp < build_end:
            self.target_open.instrument_id = self.param.symbol
            self.target_open.algorithm = target_position_algorithm.basic
            self.target_open.target_pos = self.param.target_pos
            self.target_open.desired_price = t.last_price

        # 在给定时间减仓
        if t.timestamp > reduce_start and t.timestamp < reduce_end:
            self.target_open.instrument_id = self.param.symbol
            self.target_open.algorithm = target_position_algorithm.basic
            self.target_open.target_pos = 0
            self.target_open.desired_price = t.last_price

        # 需要检查self.target_open.instrument_id是否为空，instrument_id有值时，启动调仓函数
        if self.target_open.instrument_id:
            self.api.set_target_position(self.target_open, False) # 启动调仓函数

    def on_bar(self, b):
        kt_info('K线数据: {},{}'.format(b.instrument_id, serialize(b)))
        kt_info('last k bars:')
        bars = self.api.get_last_k_bars(b.instrument_id, 10, 6)
        for idx, bar in enumerate(bars):
            kt_info('{}:\tgot bar {},{}'.format(idx, bar.instrument_id, serialize(bar)))

    def on_order_update(self, update):
        # 对于每一个订单更新或成交事件进行处理
        if update.has_trade:
            kt_info('trade update: {}'.format(serialize(update.trade)))
        else:
            kt_info('order update: {}'.format(serialize(update.order)))
