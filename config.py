# coding: utf8

qubaoUrl = 'https://yqbjenkins.stg.pinganfu.net/job/qubao/ws/plugin-h5/'

avmsBaseUrl = 'https://teststable-avms.stg.1qianbao.com/avms-service'

uploadUrl = avmsBaseUrl + '/uploadFiles?filePath=plugin'

insertPluginVersion = avmsBaseUrl + '/insertPluginVersion'

getPluginVersionList = avmsBaseUrl + '/getPluginVersionList?pluginId=%s'

targetMap = ['编辑', '内测', '灰度', '发布', '下线']

# 状态变更为编辑使用
approvePluginVersionTest = avmsBaseUrl + '/approvePluginVersionTest'

# 状态变更为非编辑使用
approvePluginVersion = avmsBaseUrl + '/approvePluginVersion'

# 编辑为编辑状态的进度
approvePluginVersionStep = avmsBaseUrl + '/getPluginVersionIncreaseList?pluginId={pluginId}&envName={envName}&frameVersion={frameVersion}&version={versionId}&appId={appId}&status={status}'

# 获取所有插件列表
getPluginList = avmsBaseUrl + '/getPluginList'

# 获取env列表
getEnvNameList = avmsBaseUrl + '/getEnvNameList'

# 获取框架版本列表
getFrameVersionList = avmsBaseUrl + '/getFrameVersionList'

# 删除编辑状态包
deletePluginVersion = avmsBaseUrl + '/deletePluginVersion'