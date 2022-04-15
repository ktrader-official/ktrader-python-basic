import json
import pytz
from datetime import datetime
from types import SimpleNamespace
from ktrader_python import *

class PythonTurtleStrategy(python_strategy):
    def __init__(self):
        python_strategy.__init__(self)
        kt_info('created PythonStrategy {}'.format(self))

    def name(self):
        return 'python_turtle'

    def update_config(self, cfg_path):
        kt_info('loading {}'.format(cfg_path))
        f = open(cfg_path)
        params = json.load(f, object_hook=lambda d: SimpleNamespace(**d))
        self.context = params.context
        self.param = params.params
        kt_info('updated config {}'.format(self.param))
        return ''

    def init(self):
        kt_info('python strategy {} init'.format(self.context))
        current_time = format_time(get_time_now(), '')
        action_day = datetime.fromtimestamp(get_time_now() / 1e9, pytz.timezone('Asia/Shanghai')).date().strftime('%Y%m%d')
        kt_info('current day is: {}, trading_day is: {}, time is: {}'.format(action_day, get_trading_day(), current_time))
        summary = super().api.get_position_summary()
        kt_info('summary close_profit {} position_profit {}'.format(summary.close_profit, summary.position_profit))
        kt_info('summary total_margin {} total_commission {} total_order_commission {}'.format(summary.total_margin, summary.total_commission, summary.total_order_commission))
        kt_info('summary frozen_margin {} frozen_commission {} frozen_order_commission {}'.format(summary.frozen_margin, summary.frozen_commission, summary.frozen_order_commission))
        # account summary
        summary = super().api.get_account_summary()
        ctp_fees = summary.total_commission
        ctp_pnl = summary.position_profit
        tot_netpnl = summary.net_pnl
        tot_netpnl_high = summary.net_pnl_high
        tot_netpnl_low = summary.net_pnl_low
        kt_info('ctp_account: {}, 持仓盈亏:{}, 手续费: {}, 总利润:{}, 最高: {}, 最低:{}'.format(summary.investor_id, ctp_pnl, ctp_fees, tot_netpnl, tot_netpnl_high, tot_netpnl_low))

        kt_info('parse instrument configs:')
        pos = super().api.get_instrument_position_detail(self.param.symbol)
        total_long = pos.long_position.total
        history_long = pos.long_position.history
        total_short = -pos.short_position.total
        history_short = -pos.short_position.history
        init_net_pos = total_long + total_short
        kt_info('合约{} 多仓{} 昨多{} 空仓{} 昨空{}'.format(self.param.symbol, total_long, history_long, total_short, history_short))
        if init_net_pos > 0:
            for trade in pos.long_position_detail:
                self.last_open_trade = trade
        elif init_net_pos < 0:
            for trade in pos.short_position_detail:
                self.last_open_trade = trade
        # test APIs
        super().api.get_all_position_summary()
        super().api.get_all_position_detail()
        super().api.get_inflight_orders()
        super().api.get_last_k_ticks(self.param.symbol, 60)
        super().api.get_last_k_bars(self.param.symbol, 60, 1)
        super().api.get_instrument_trading_risk(self.param.symbol)
        return

    def shutdown(self):
        kt_info('python strategy {} shutdown'.format(self.context))
        return

    def on_tick(self, t):
        # current tick time
        tick_time = format_time(int(t.timestamp), '')
        kt_info('合约:{},时间:{},最新:{},最高:{},最低:{},买一:{},买一量:{},卖一:{},卖一量:{},成交量:{},增仓:{}'.format(
            t.instrument_id, tick_time, t.last_price, t.highest_price, t.lowest_price, t.bid_price[0], t.bid_volume[0], t.ask_price[0], t.ask_volume[0], t.volume_delta, t.open_interest_delta))

        if self.param.symbol != t.instrument_id:
            return
        cur_last_price = t.last_price
        summary = super().api.get_instrument_summary(self.param.symbol)
        cur_net_pos = summary.net_pos
        if cur_net_pos != 0 and not self.last_open_trade.instrument_id:
            kt_error('{} current net pos {} last open trade not updated'.format(t.instrument_id, cur_net_pos))
            return

        # 开仓条件
        # BUY
        if cur_net_pos == 0:
            if cur_last_price > self.param.HHigh:
                self.target_open.instrument_id = self.param.symbol
                self.target_open.algorithm = target_position_algorithm.basic
                self.target_open.target_pos = 1
                self.target_open.desired_price = cur_last_price
            # SELL
            elif cur_last_price < self.param.LLow:
                self.target_open.instrument_id = self.param.symbol
                self.target_open.algorithm = target_position_algorithm.basic
                self.target_open.target_pos = -1
                self.target_open.desired_price = cur_last_price
        # 止损、止盈条件
        elif cur_net_pos >= 1:
            assert self.last_open_trade.instrument_id
            stoploss = max(self.last_open_trade.price - 0.5*self.param.ATR, self.param.LLow)
            # 平仓止损
            if cur_last_price < stoploss:
                self.target_open.instrument_id = self.param.symbol
                self.target_open.algorithm = target_position_algorithm.basic
                self.target_open.target_pos = cur_net_pos - 1
                self.target_open.desired_price = cur_last_price
            # 动态加仓
            if cur_last_price > self.last_open_trade.price + 0.5*self.param.ATR:
                self.target_open.instrument_id = self.param.symbol
                self.target_open.algorithm = target_position_algorithm.basic
                self.target_open.target_pos = cur_net_pos + 1
                self.target_open.desired_price = cur_last_price
        elif cur_net_pos <= -1:
            assert self.last_open_trade.instrument_id
            stoploss = min(self.last_open_trade.price + 0.5*self.param.ATR, self.param.HHigh)
            # 平仓止损
            if cur_last_price > stoploss:
                self.target_open.instrument_id = self.param.symbol
                self.target_open.algorithm = target_position_algorithm.basic
                self.target_open.target_pos = cur_net_pos + 1
                self.target_open.desired_price = cur_last_price
            # 动态加仓
            if cur_last_price < self.last_open_trade.price - 0.5*self.param.ATR:
                self.target_open.instrument_id = self.param.symbol
                self.target_open.algorithm = target_position_algorithm.basic
                self.target_open.target_pos = cur_net_pos - 1
                self.target_open.desired_price = cur_last_price
        if not self.target_open.instrument_id:
            return
        super().api.set_target_position(self.target_open, False)

    def on_order_update(self, update):
        if update.has_trade:
            kt_info('trade update: {}'.format(serialize(update.trade)))
            if update.trade.offset == offset_flag_enum.open:
                self.last_open_trade = update.trade
        kt_info('order update: {}'.format(serialize(update.order)))


    context = ''
    param = None
    last_open_trade = trade_info()
    target_open = position_target()
