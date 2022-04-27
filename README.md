# KTrader Python Basic 策略开发环境 (适用于Python用户)

## 介绍
运行环境Ubuntu 20.04  

KTrader Python Basic 是基础版本的KTrader Python Trading API. (仅含策略回测功能，供量化投研使用)
用户可以根据KTrader Python API 开发手册编写量化策略。
src/python_turtle_strategy.py 是海龟示例策略
## 步骤
1. ```git clone git@gitee.com:ktrader-user/ktrader-python-basic.git```
2. ```git submodule update --init --recursive``` 更新子模块
3. 检查strategy_configs folder: global_config.json 是全局策略管理配置，turtle.json 是海龟样例策略参数配置
3. 用Klib工具下载好数据后(推荐将数据存入../data/log/prodticks目录), 运行以下指令进行回测:
    ```
    bin/run_backtest --tick_path=../data/log/prodticks --enabled_strategy=strategy_configs --start_date=20220209 --end_date=20220209 --max_concurrency=1
    ```
