import json
import pytz
from datetime import datetime
from types import SimpleNamespace
from ktrader_python import *
import pandas as pd
import numpy as np

class DoubleMA(python_strategy):
    # DoubleMA 是最简模板策略，即是经常见到的双均线策略。
    def __init__(self):
        # 每一个新的策略instance需要继承 python_strategy object
        python_strategy.__init__(self)
        kt_info('Strategy Created: {}'.format(self))
        # Initialization
        self.context = ''
        self.param = None
        self.target_open = position_target() # 初始化调仓object

    def update_config(self, cfg_path):
        # 加载global_config.json
        kt_info('Loading strategy global config: {}'.format(cfg_path))
        f = open(cfg_path)
        params = json.load(f, object_hook=lambda d: SimpleNamespace(**d)) # load json strategy config into object
        self.context = params.context
        self.param = params.params
        kt_info('Global config updated: {}'.format(self.param))
        return ''

    def init(self):
        # init 在每次交易刚开始时会触发, 用于策略初始化
        kt_info('Strategy Init: {}'.format(self.context))
        current_time = format_time(get_time_now(), '')
        action_day = datetime.fromtimestamp(get_time_now() / 1e9, pytz.timezone('Asia/Shanghai')).date().strftime('%Y-%m-%d') # action day 自然日
        kt_info('current day is: {}, trading_day is: {}, time is: {}'.format(action_day, get_trading_day(), current_time)) #显示时间信息

        # account summary 显示账户信息
        summary = self.api.get_account_summary()
        acc_fees = summary.total_commission
        acc_profit = summary.position_profit
        acc_netpnl = summary.net_pnl
        acc_netpnl_high = summary.net_pnl_high
        acc_netpnl_low = summary.net_pnl_low
        kt_info('Account Summary: 用户ID: {}, 持仓盈亏:{}, 手续费: {}, 净利润:{}, 最高净利: {}, 最低净利:{}'.format(summary.investor_id, acc_profit, acc_fees, acc_netpnl, acc_netpnl_high, acc_netpnl_low))

        # position summary 显示本策略所有仓位信息
        summary = self.api.get_position_summary()
        kt_info('Position Summary: 平仓盈亏:{}, 持仓盈亏:{}, 总保证金:{}, 总手续费:{}, '.format(summary.close_profit, summary.position_profit, summary.total_margin, summary.total_commission))

        # contract summary 显示单个合约持仓信息
        kt_info('Contract Summary:')
        pos = self.api.get_instrument_position_detail(self.param.symbol)
        total_long = pos.long_position.total # 多仓(总)
        history_long = pos.long_position.history # 昨多仓
        total_short = -pos.short_position.total # 空仓(总)
        history_short = -pos.short_position.history # 昨空仓
        init_net_pos = total_long + total_short # 净多仓
        kt_info('合约:{}, 多仓:{}, 昨多:{}, 空仓:{}, 昨空:{}, 净多仓:{}'.format(self.param.symbol, total_long, history_long, total_short, history_short, init_net_pos))

        return

    def shutdown(self):
        # 安全退出策略
        kt_info('Strategy {} shutdown'.format(self.context))
        return

    def on_tick(self, t):
        # 对每一个Tick事件，做出相应交易动作
        tick_time = format_time(int(t.timestamp), '')
        # get current netpnl
        summary = self.api.get_account_summary()
        netpnl = summary.net_pnl
        kt_info('合约:{},时间:{},净利润:{},最新:{},最高:{},最低:{},买一:{},买一量:{},卖一:{},卖一量:{},成交量:{},增仓:{}'.format(
            t.instrument_id, tick_time, netpnl, t.last_price, t.highest_price, t.lowest_price, t.bid_price[0], t.bid_volume[0], t.ask_price[0], t.ask_volume[0], t.volume_delta, t.open_interest_delta))

        if self.param.symbol != t.instrument_id: # 检查symbol
            return
        cur_price = t.last_price
        summary = self.api.get_instrument_summary(self.param.symbol)
        cur_net_pos = summary.net_pos

        # get moving averages
        bars = self.api.get_last_k_bars(self.param.symbol, 25, 5) # bars[0]: 离当前最近的bar
        close_prices = [bar.close for bar in bars]
        slow_ma = np.mean(close_prices)
        fast_ma = np.mean(close_prices[-5:])
        kt_info('fast_ma: {}, slow_ma:{}'.format(fast_ma, slow_ma))

        # 开仓条件
        if cur_net_pos == 0:
            # 买入开仓条件
            if cur_price > fast_ma and fast_ma > slow_ma:
                # 设定position_target object: symbol, algo type, target_pos, desired price
                self.target_open.instrument_id = self.param.symbol
                self.target_open.algorithm = target_position_algorithm.basic
                self.target_open.target_pos = 1
                self.target_open.desired_price = cur_price
            # 卖出开仓条件
            elif cur_price < fast_ma and  fast_ma < slow_ma:
                self.target_open.instrument_id = self.param.symbol
                self.target_open.algorithm = target_position_algorithm.basic
                self.target_open.target_pos = -1
                self.target_open.desired_price = cur_price

        if not self.target_open.instrument_id:
            return
        self.api.set_target_position(self.target_open, False) # set target position 进行调仓

    def on_order_update(self, update):
        # 对于每一个订单更新或成交事件进行处理
        if update.has_trade:
            kt_info('trade update: {}'.format(serialize(update.trade)))
        else:
            kt_info('order update: {}'.format(serialize(update.order)))
