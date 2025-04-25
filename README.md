# tools-elk

sunday的tools插件，用于avms发包操作, 支持功能:

1. 查看插件配置信息
2. 自动从jenkins找最新包上传
3. 本地包上传
4. 删除或下线未发布的包

依赖sunday，使用前请安装[sunday](https://code.paic.com.cn/#/repo/yqb-travelpluginh5/car_board/sunday/BRANCH/tree), 安装成功后执行`sunday_install ssh://git@code.paic.com.cn:8009/yqb-travelpluginh5/car_board.git#tools-avms`安装本插件

## avms

使用方法：

```console
usage: avms.py [-v] [-h] {push,del,info} ...

发包自动化工具

Optional:
  -v, --version    当前程序版本
  -h, --help       打印帮助说明

子命令:
  avms功能细分

  {push,del,info}  包信息、上传包到avms、删除avms未发布的包

使用案例:
    avms info -h
    avms del -h
    avms push -h
    avms info RNB0000062 -e stg3 -a android
    avms push RNB0000062 -e stg3 -V 20170406 -f RN062 -t 3
    avms del RNB0000062 -e stg3 -a android
    avms push RNB0000062 -e stg3 -f RN062 -p /path/to/dist/native/*-car_all.zip
详细ui操作见: https://teststable-avms.stg.1qianbao.com/avms-service/plugin#/plugins
```

### info 子命令

查看插件信息及包状态

```console
usage: avms.py info [-h] [-e ENV_NAME] [-f FRAME_VERSION] [-t TARGET]
                    [-a APP_ID]
                    [PLUGIN_ID]

positional arguments:
  PLUGIN_ID             插件ID, 如: RNB0000062

optional arguments:
  -h, --help            show this help message and exit
  -e ENV_NAME, --env ENV_NAME
                        包工具版本, 默认为: teststable
  -f FRAME_VERSION, --frame FRAME_VERSION
                        框架版本: 如: RN062
  -t TARGET, --target TARGET
                        目标状态, 0表示编辑, 1表示内测, 2表示灰度, 3表示发布, 4表示下线
  -a APP_ID, --appid APP_ID
                        系统类型, ios或android
```

### del 子命令

用于删除或下线未发布的包

```console
usage: avms.py del [-h] [-e ENV_NAME] [-f FRAME_VERSION] [-t TARGET]
                   [-V VERSION_ID] [-a APP_ID]
                   [PLUGIN_ID]

positional arguments:
  PLUGIN_ID             插件ID, 如: RNB0000062

optional arguments:
  -h, --help            show this help message and exit
  -e ENV_NAME, --env ENV_NAME
                        包工具版本, 如: teststable
  -f FRAME_VERSION, --frame FRAME_VERSION
                        框架版本: 如: RN062
  -t TARGET, --target TARGET
                        目标状态, 0表示编辑, 1表示内测, 2表示灰度
  -V VERSION_ID, --vid VERSION_ID
                        包版本id, 如: v2.0.0
  -a APP_ID, --appid APP_ID
                        系统类型, ios或android
```

### push 子命令

上传包并推送到指定状态, 当未指定本地包则自动到jenkins找最新包, 可推送到编辑状态、内测状态、灰度状态、发布状态

```console
usage: avms.py push [-h] [-e ENV_NAME] [-V VERSION_ID] -f FRAME_VERSION
                    [-t TARGET] [-p [FILE]]
                    [PLUGIN_ID]

positional arguments:
  PLUGIN_ID             插件ID, 如: RNB0000062

optional arguments:
  -h, --help            show this help message and exit
  -e ENV_NAME, --env ENV_NAME
                        包工具版本, 默认为: teststable
  -V VERSION_ID, --vid VERSION_ID
                        版本id, 默认为: 20170406
  -f FRAME_VERSION, --frame FRAME_VERSION
                        框架版本: 如: RN062
  -t TARGET, --target TARGET
                        目标状态, 0表示编辑, 1表示内测, 2表示灰度, 3表示发布
  -p [FILE], --zpath [FILE]
                        指定要上传的包
```
