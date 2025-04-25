# coding: utf-8
import os
import re
from sunday.login.jenkins import Login as JenkinsLogin
from sunday.login.avms import Login as AvmsLogin
from sunday.core import Logger, printTable, enver, getParser
from sunday.tools.avms.config import uploadUrl, qubaoUrl
from bs4 import BeautifulSoup

class Upload():
    """将程序包上传到服务器"""
    def __init__(self, pluginId, versionId, buildDate='', fileName='', isAutoLast=False):
        self.logger = Logger('avms:upload').getLogger()
        self.pluginId = pluginId
        self.versionId = versionId
        self.buildDate = buildDate
        self.fileName = fileName
        self.isAutoLast = isAutoLast
        self.avms = AvmsLogin().login().rs
    
    def check(self):
        if not self.pluginId or not self.versionId:
            self.logger.error('pluginId和versionId为必传项')
            exit(1)
        if not self.isAutoLast and (not self.buildDate or not self.fileName):
            self.logger.error('非自动找包buildDate和fileName必传')
            exit(1)
        self.jenkins = JenkinsLogin().login().rs
    
    def getLastUrl(self, url, patstr):
        pattern = re.compile(patstr)
        res = self.jenkins.get(url, verify=False)
        soup = BeautifulSoup(res.content, 'lxml')
        datas = [i.get_text() for i in soup.find(class_='fileList').find_all('a')]
        last = [i for i in datas if pattern.match(i)].pop()
        return os.path.join(url, last), last

    def push(self, url, fileName):
        res = self.jenkins.get(url, verify=False)
        res = self.avms.post(uploadUrl, files={ 'file': (fileName, res.content)})
        return res.json()['retData']

    def run(self, fileStream):
        if fileStream:
            fileName = os.path.basename(fileStream.name)
            res = self.avms.post(uploadUrl, files={ 'file': (fileName, fileStream.buffer.read())})
            return res.json()['retData']
        self.check()
        if self.isAutoLast:
            # 自动上传最新包
            url = os.path.join(qubaoUrl, self.pluginId, self.versionId)
            url, lastDate = self.getLastUrl(url, r'^\d{8}$')
            url, fileName = self.getLastUrl(url, r'.*\.zip$')
            self.logger.debug('auto push last package: lastDate: %s, fileName: %s, url: %s' % (lastDate, fileName, url))
        else:
            url = os.path.join(qubaoUrl, pluginId, versionId, buildDate, fileName)
            self.logger.debug('push package: %s' % url)
        fileName = self.push(url, fileName)
        self.logger.info('附件上传成功: %s' % fileName)
        return fileName


if __name__ == "__main__":
    upload = Upload('RNB0000062', '20170406', isAutoLast=True)
    upload.run()
