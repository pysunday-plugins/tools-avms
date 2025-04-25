# coding: utf-8
import argparse
import json
import tqdm
import time
from sunday.tools.avms import config
from sunday.core import Logger, getParser, exit, printTable
from sunday.login.avms import Login as AvmsLogin
from sunday.tools.avms.upload import Upload
from pydash import get

logger = Logger('avms').getLogger()

CMDINFO = {
    "version": '0.0.1',
    "description": "发包自动化工具",
    "epilog": """
使用案例:
    %(prog)s info -h
    %(prog)s del -h
    %(prog)s push -h
    %(prog)s info RNB0000062 -e stg3 -a android
    %(prog)s push RNB0000062 -e stg3 -V 20170406 -f RN062 -t 3
    %(prog)s del RNB0000062 -e stg3 -a android
    %(prog)s push RNB0000062 -e stg3 -f RN062 -p /path/to/dist/native/*-car_all.zip
详细ui操作见: https://teststable-avms.stg.1qianbao.com/avms-service/plugin#/plugins
    """,
}

class Main():
    def init(self):
        self.avms = AvmsLogin().login().rs
    
    def pushZip(self):
        zipName = Upload(self.pluginId, self.versionId, isAutoLast=True).run(self.zipPath)
        data = {
            "pluginId": self.pluginId,
            "envName": self.envName,
            "frameVersion": self.frameVersion,
            "zipName": [zipName],
            "betaVersionNum": 10,
            "roolVersion": ""
        }
        logger.debug('上传包' + json.dumps(data))
        ans = self.avms.post(config.insertPluginVersion, data=json.dumps(data), headers={
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json;charset=UTF-8'
        })
        if ans.status_code != 200:
            logger.error('包上传失败, 状态码: %d' % ans.status_code)
        else:
            ansjson = ans.json()
            if ansjson['retCode'] != '000000':
                logger.error('包上传失败, 返回数据: ' + json.dumps(ansjson))
            else:
                print('包上传成功!')
                return zipName
        return False
    
    def getPluginVersionList(self, zipName = ''):
        res = self.avms.get(config.getPluginVersionList % self.pluginId)
        if res.status_code != 200: exit('ERROR: 请求包列表失败, 请检查网络后重试!')
        resdata = res.json()
        if not zipName: return resdata['retData']
        ans = []
        appid = []
        def pluginFilter(item):
            can = get(item, 'zipName.0') == zipName \
                and item['envName'] == self.envName \
                and item['status'] == 0 \
                and item['appId'] not in appid
            if can: appid.append(item['appId'])
            return can
        if 'retData' in resdata and len(resdata['retData']):
            ans = list(filter(pluginFilter, resdata['retData']))
        logger.debug('共存在匹配的包%d个' % len(ans))
        return ans
    
    def approve_1(self, data):
        # 提交到内测后
        step = 0
        pbar = tqdm.tqdm(total=100)
        while step != 100:
            res = self.avms.get(config.approvePluginVersionStep.format(**data))
            if res.status_code != 200: exit('网络异常请检查')
            resdata = res.json()
            status = get(resdata, 'resultData')
            step = int(status) if status else 100
            pbar.update(step)
            if status and step == 100: time.sleep(1 if status else 3)
        pbar.close()

    def approve_2(self, data):
        pass

    def approve_3(self, data):
        pass

    def approve(self, pluginInfo):
        logger.info('{appId}包执行部署, 版本为{versionId}'.format(**pluginInfo))
        status = 0
        while (status < self.target):
            logger.debug('部署到%s' % config.targetMap[status + 1])
            apiurl = config.approvePluginVersionTest if status == 0 else config.approvePluginVersion
            data = pluginInfo.copy()
            data.update({ 'hunxiao': 1, 'status': status })
            res = self.avms.post(apiurl, data=json.dumps(data), headers={
                'Content-Type': 'application/json;charset=UTF-8'
            })
            try:
                resdata = res.json()
                if resdata['retCode'] == '000000':
                    success = getattr(self, 'approve_%d' % (status + 1))(data)
                    if success == False:
                        exit('推送包版本异常请重试!当前失败版本: %s' % data['version'])
                    logger.debug('部署到%s成功' % config.targetMap[status + 1])
                    status += 1
                else:
                    logger.error('部署到%s失败: %s(%s), 即将重试中...' % (config.targetMap[status + 1], resdata['retData'], resdata['retCode']))
                    time.sleep(1)
            except:
                pass

    def push_run(self):
        zipName = self.pushZip()
        # zipName = 'plugin/RNB0000062-20160413-20220221180128-car_all1645778499894.zip'
        if not zipName: exit('ERROR: 包上传失败, 请检查网络后重试!')
        if self.target == 0: exit('包已上传到%s' % config.targetMap[0])
        ans = self.getPluginVersionList(zipName)
        if not len(ans): exit('未找到匹配%s的包版本信息, 请检查' % zipName)
        for plugin in ans: self.approve(plugin)
        logs = ['环境名称: %s' % self.envName, '框架版本: %s' % self.frameVersion, '当前状态: %s' % config.targetMap[self.target]]
        logs.extend(['{appId}版本: {versionId}'.format(**p) for p in ans])
        print(('\n'.join(logs)))

    def filterPluginsList(self):
        allList = self.getPluginVersionList()
        logger.debug('过滤前%d个' % len(allList))
        allListSort = [each for each in sorted(allList, key=lambda item: item['frameVersion'] + item['envName'] + str(item['status']) + item['appId'])]
        allListSort.reverse()
        for name in ['envName', 'frameVersion', 'target', 'versionId', 'appId']:
            if not hasattr(self, name): continue
            value = getattr(self, name)
            if value is not None:
                allListSort = [item for item in allListSort if item['status' if name == 'target' else name] == value]
        logger.debug('过滤后%d个' % len(allListSort))
        return allListSort

    def info_run(self, infos=['info', 'version']):
        # 打印插件号对应的插件信息及部署信息
        if 'info' in infos:
            plugin = [item for item in self.avms.get(config.getPluginList).json()['retData'] if item['pluginId'] == self.pluginId].pop()
            envList = self.avms.get(config.getEnvNameList).json()['retData']
            frameList = [item for item in self.avms.get(config.getFrameVersionList).json()['retData'] if item['type'] == plugin['appId']]
            printTable(['插件', '名称', '描述'])([[plugin['pluginId'], plugin['pluginName'], plugin['pluginDesc']]])
            printTable(['环境(-e)', '描述'])([[item['envName'], item['pluginDesc']] for item in envList])
            printTable(['框架(-f)', '描述'])([[item['frameVersion'], item['pluginDesc']] for item in frameList])
        if 'version' in infos:
            allListSort = self.filterPluginsList()
            pluginTable = printTable(['框架(-f)', '环境(-e)', '状态(-t)', '系统', '版本', '包名', '创建时间'])
            pluginTable([[
                i['frameVersion'],
                i['envName'],
                config.targetMap[i['status']],
                i['appId'],
                i['versionId'],
                ', '.join(i['zipName']),
                i['createTime']
            ] for i in allListSort])

    def del_run(self):
        # 删除或下线未在发布状态的包
        self.info_run(['version'])
        allListSort = [item for item in self.filterPluginsList() if item['status'] < 3]
        statusAll = set()
        total = len(allListSort)
        pbar = tqdm.tqdm(total)
        for item in allListSort:
            status = item['status']
            statusAll.add(status)
            apiurl = config.deletePluginVersion if status == 0 else config.approvePluginVersion
            data = item.copy()
            data.update({ 'hunxiao': 0, 'status': 3 if status else 0 })
            res = self.avms.post(apiurl, data=json.dumps(data), headers={
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json;charset=UTF-8',
                'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
                'sec-ch-ua-mobile': '?0',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            })
            pbar.update(1)
        pbar.close()
        self.info_run(['version'])
    
    def run(self):
        logger.debug('运行子命令: %s' % self.sub_name)
        self.init()
        getattr(self, self.sub_name + '_run')()


def runcmd():
    parser = getParser(**CMDINFO)
    subparsers = parser.add_subparsers(title='子命令', dest='sub_name', description='avms功能细分', help='包信息、上传包到avms、删除avms未发布的包')
    parser_push = subparsers.add_parser('push')
    parser_push.add_argument('pluginId', nargs='?', metavar='PLUGIN_ID', type=str, help='插件ID, 如: RNB0000062')
    parser_push.add_argument("-e", "--env", dest="envName", metavar="ENV_NAME", help="包工具版本, 默认为: teststable", default="teststable")
    parser_push.add_argument("-V", "--vid", dest="versionId", metavar="VERSION_ID", help="版本id, 默认为: 20170406", default="20170406")
    parser_push.add_argument("-f", "--frame", dest="frameVersion", metavar="FRAME_VERSION", help="框架版本: 如: RN062", required=True)
    parser_push.add_argument("-t", "--target", dest="target", metavar="TARGET", help="目标状态, 0表示编辑, 1表示内测, 2表示灰度, 3表示发布", default=3, type=int)
    parser_push.add_argument('-p', '--zpath', dest='zipPath', metavar="FILE", help="指定要上传的包", nargs="?", type=argparse.FileType('r'))
    parser_del = subparsers.add_parser('del')
    parser_del.add_argument('pluginId', nargs='?', metavar='PLUGIN_ID', type=str, help='插件ID, 如: RNB0000062')
    parser_del.add_argument("-e", "--env", dest="envName", metavar="ENV_NAME", help="包工具版本, 如: teststable")
    parser_del.add_argument("-f", "--frame", dest="frameVersion", metavar="FRAME_VERSION", help="框架版本: 如: RN062")
    parser_del.add_argument("-t", "--target", dest="target", metavar="TARGET", help="目标状态, 0表示编辑, 1表示内测, 2表示灰度", type=int)
    parser_del.add_argument("-V", "--vid", dest="versionId", metavar="VERSION_ID", help="包版本id, 如: v2.0.0")
    parser_del.add_argument("-a", "--appid", dest="appId", metavar="APP_ID", help="系统类型, ios或android")
    parser_info = subparsers.add_parser('info')
    parser_info.add_argument('pluginId', nargs='?', metavar='PLUGIN_ID', type=str, help='插件ID, 如: RNB0000062')
    parser_info.add_argument("-e", "--env", dest="envName", metavar="ENV_NAME", help="包工具版本, 默认为: teststable")
    parser_info.add_argument("-f", "--frame", dest="frameVersion", metavar="FRAME_VERSION", help="框架版本: 如: RN062")
    parser_info.add_argument("-t", "--target", dest="target", metavar="TARGET", help="目标状态, 0表示编辑, 1表示内测, 2表示灰度, 3表示发布, 4表示下线", type=int)
    parser_info.add_argument("-a", "--appid", dest="appId", metavar="APP_ID", help="系统类型, ios或android")
    handle = parser.parse_args(namespace=Main())
    handle.run()


if __name__ == "__main__":
    runcmd()
