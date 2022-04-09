# KTrader Python Demo策略

#### 介绍
python/python_turtle_strategy.py 是示例策略

准备好回测数据后(假设位于prodticks目录), 运行以下指令进行回测:
```
bin/run_backtest --tick_path=prodticks --enabled_strategy=strategy_configs --start_date=20220209 --end_date=20220209 --max_concurrency=1
```
