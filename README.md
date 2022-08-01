# KTrader Python策略开发指南

## 介绍

KTrader Python Basic是基础版本的KTrader Python Trading API. (仅含策略回测功能，供量化投研使用)
用户可以根据KTrader Python API 开发手册编写量化策略。

**注意**: 最新文档请登录[易量科技KTrader官网](https://ktrader-official.com)查询。

## 配置项目

1. 下载KTrader Python示例策略`git clone git@gitee.com:ktrader-user/ktrader-python-basic.git`
1. 运行`git submodule update --init --recursive`更新子模块
1. 检查`strategy_configs`路径： `global_config.json`是全局策略管理配置，`turtle.json`是海龟样例策略参数配置

    > **global_config.json**
    > ```json
    > {
    >     "python": {
    >         "identifier": 101,
    >         "python_path": "python/python_turtle_strategy.py",
    >         "python_strategy": "PythonTurtleStrategy",
    >         "config": "strategy_configs/turtle.json"
    >     }
    > }
    > ```
    > **turtle.json**
    > ```json
    > {
    >     "context":"turtle",
    >     "params": {
    >                   "symbol":"sc2204",
    >                   "start_time": "21:01:00",
    >                   "end_time" : "15:00:00",
    >                   "unit":1,
    >                   "HHigh": 550.6,
    >                   "LLow": 504.2,
    >                   "ATR":15.6447
    >                 }
    > }
    > ```

**在浏览器中打开`third_party/ktrader-python-backtest/docs/index.html`查看全部API文档**

## 配置Python环境

KTrader Python使用Python 3.8版本，可使用pip或conda配置python环境

> **注意：** 不要混用pip和conda

### 使用pip配置Python
运行以下命令安装Python3.8和pip
```bash
> sudo apt install -y python3.8 python3.8-dev python3-pip
```

使用pip安装pandas和numpy

```bash
> pip3 install pandas numpy
```

### 使用conda配置Python
安装conda
```bash
> wget https://repo.anaconda.com/miniconda/Miniconda3-py38_4.11.0-Linux-x86_64.sh -O ~/miniconda.sh
> bash miniconda.sh -b -p ~/miniconda
```

弹出是否运行`conda init`选择`yes`, 之后打开一个新的终端进入conda环境并安装pandas和numpy

```bash
> conda create -n py38 python=3.8
> conda activate py38
> conda install pandas numpy
```

## KTrader回测框架配置及使用
KTrader运行环境为Ubuntu 20.04LTS, 暂不支持直接在Windows或MacOS上运行。
推荐在Docker下运行回测。在Windows或MacOS上运行需要在虚拟机中安装Linux。

**Windows 10安装Ubuntu 20.04虚拟机**
 * 启用Windows 10自带[Hyper-V虚拟机](https://docs.microsoft.com/zh-cn/virtualization/hyper-v-on-windows/quick-start/enable-hyper-v)
 * 下载并安装Ubuntu 20.04（[官方](https://releases.ubuntu.com/20.04/ubuntu-20.04.4-desktop-amd64.iso)或[镜像](https://mirrors.tuna.tsinghua.edu.cn/ubuntu-releases/20.04/ubuntu-20.04.4-desktop-amd64.iso)），可参考[此教程](https://blog.csdn.net/ZChen1996/article/details/106042635)

**MacOS安装Ubuntu 20.04虚拟机**
* MacOS下可以使用免费的[VirtualBox虚拟机](https://download.virtualbox.org/virtualbox/6.1.34/VirtualBox-6.1.34-150636-OSX.dmg)
* 下载并安装Ubuntu 20.04（[官方](https://releases.ubuntu.com/20.04/ubuntu-20.04.4-desktop-amd64.iso)或[镜像](https://mirrors.tuna.tsinghua.edu.cn/ubuntu-releases/20.04/ubuntu-20.04.4-desktop-amd64.iso)），可参考[此教程](https://www.jianshu.com/p/fedcf6c98ba0)

**本地运行回测**
 * 使用klib下载行情数据到本地，例如`/prodticks`目录：
	```bash
	> python download_data.py --user=$username --passwd=$password --start_date=20220101 \
    --end_date=20220228 --data_type=raw_data --dir_path=/prodticks
	```
 * 在Ubuntu 20.04环境下，在策略开发所在路径运行回测：
	```bash
	> bin/run_backtest --tick_path=/prodticks/raw_data --enabled_strategy=strategy_configs \
	--start_date=20220106 --end_date=20220228 --log_root=log --test_name=mytest
    ```
    回测参数`start_date`和`end_date`是回测开始与截止日期，`tick_path`为行情数据所在路径，需包含从开始到截至每一天的数据，`enabled_strategy`为`global_config.json`所在目录，`log_root`为运行日志所在路径。
 * 在`ktrader-python-basic`所在路径下`ktrader_config.json`文件配置KTrader账户信息

    > **ktrader_config.json**
    > ```json
    > {
    >     "license":"BASIC",
    >     "email": "user-email@test.com",
    >     "password": "user-password"
    > }
    > ```

    `license`填写用户使用的KTrader版本，如`BASIC`, `SOLO`, `PRO`等。`email`和`password`填写用户在`https://ktrader-official.com`注册的邮箱和密码即可。
 * 回测结果存储在格式如`log/run_backtest/mytest-20220209-20220209-123456`的目录，其中最后一级格式为`$test_name-$start_date-$end_date-$process_id`，例如
	```
    log/run_backtest/mytest-20220106-20220228-738719/
    ├── backtest 
    ├── logs
    ├── orders
    ├── positions
    ├── summary
    └── trades
	```
	其中logs目录下为系统日志，orders目录下为每个交易日订单、成交日志，summary目录下为每天各策略盈亏总结，backtest/account_settlement-20220106-20220228.csv为每天账户综合盈亏总结。

