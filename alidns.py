from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkdomain.request.v20180129.QueryDomainGroupListRequest import QueryDomainGroupListRequest
from aliyunsdkdomain.request.v20180129.QueryDomainListRequest import QueryDomainListRequest
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.OperateBatchDomainRequest import OperateBatchDomainRequest
from aliyunsdkalidns.request.v20150109.DescribeBatchResultCountRequest import DescribeBatchResultCountRequest
from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler

import json
import requests
import re
import time
import yaml
import os
import time
import datetime

logger.add('aliyun_ddns.log', format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}',encoding='utf-8')

def get_config():
    url_list = []
    type_keyWord = ''
    rr_keyWord = ''
    domain_group_name = ''
    access_key = ''
    access_key_secret = ''
    region_id = 'cn-hangzhou'
    log_file_name = 'aliyun_ddns.log'
    job_time_minutes = 10
    # 获取当前脚本所在文件夹路径
    current_path = os.path.abspath(".")
    # 获取yaml配置文件路径
    yamlPath = os.path.join(current_path, "config.yaml")
    # open方法打开直接读出来
    file = open(yamlPath, 'r', encoding='utf-8')
    # 读出来是字符串
    cfgStr = file.read() 
    # 用load方法转字典
    cfg = yaml.load(cfgStr, Loader=yaml.FullLoader)  
    aliyunCfg = cfg.get('aliyun')
    if aliyunCfg is not None :
        if aliyunCfg.get('realIpUrl') is not None :
            url_list = aliyunCfg.get('realIpUrl')
        if aliyunCfg.get('type') is not None :
            type_keyWord = aliyunCfg.get('type')
        if aliyunCfg.get('rr') is not None :
            rr_keyWord = aliyunCfg.get('rr')
        if aliyunCfg.get('domainGroup') is not None :
            domain_group_name = aliyunCfg.get('domainGroup')
        if aliyunCfg.get('access_key') is not None :
            access_key = aliyunCfg.get('access_key')
        if aliyunCfg.get('access_key_secret') is not None :
            access_key_secret = aliyunCfg.get('access_key_secret') 
        if aliyunCfg.get('region_id') is not None :
            region_id = aliyunCfg.get('region_id') 
        if aliyunCfg.get('job_time_minutes') is not None :
            job_time_minutes = aliyunCfg.get('job_time_minutes') 
    return url_list,type_keyWord,rr_keyWord,domain_group_name,access_key,access_key_secret,region_id,job_time_minutes


url_list,type_keyWord,rr_keyWord,domain_group_name,access_key,access_key_secret,region_id,job_time_minutes = get_config()

client = AcsClient(access_key, access_key_secret, region_id)

def get_currentIp():
    ip_list = []
    for req in url_list:
        logger.debug("do request url:{}", req)
        http_result = requests.get(req)
        if re.match(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b", http_result.text) :
            ip_list = re.findall(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b", http_result.text)
            break
    logger.debug("ip_list:{}",ip_list)    
    ip = str(ip_list[0])
    logger.debug("ip:{}",ip)    
    return ip


def get_domainGroupIdByGroupName(domain_group_name):
    domainGroupRequest = QueryDomainGroupListRequest()
    domainGroupRequest.set_DomainGroupName(domain_group_name)
    groupResponse = client.do_action_with_exception(domainGroupRequest)
    aliGroupResponse = json.loads(str(groupResponse, encoding='utf-8'))
    data = aliGroupResponse['Data']
    groupId = -1
    for domainGroup in data['DomainGroup'] :
        groupId = domainGroup['DomainGroupId']
        if groupId !=-1 :
            break
    logger.debug('domainGroupId:{}',groupId)
    return groupId

def get_domainRecordsByGroupId(domain_groupId):
    domainListRequest = QueryDomainListRequest()
    domainListRequest.set_DomainGroupId(domain_groupId)
    domainListRequest.set_PageNum(1)
    domainListRequest.set_PageSize(100)
    domapinListResponse = client.do_action_with_exception(domainListRequest)
    aliDomainlList = json.loads(str(domapinListResponse, encoding='utf-8'))
    domainList = aliDomainlList['Data']['Domain']
    # logger.debug('domainList:',domainList)
    return domainList

def get_addAndModifyDomainList(ip,domainList):
    addDomainList = []
    modifyDomainList = []
    for domain in domainList :
        domain_name = domain['DomainName']
        # logger.debug('domain:{}',domain_name)
        describeDomainRecordsRequest = DescribeDomainRecordsRequest()
        describeDomainRecordsRequest.set_TypeKeyWord(type_keyWord)
        describeDomainRecordsRequest.set_RRKeyWord(rr_keyWord)
        describeDomainRecordsRequest.set_PageNumber(1)
        describeDomainRecordsRequest.set_PageSize(10)
        describeDomainRecordsRequest.set_DomainName(domain_name)
        describeDomainRecordsResponse = client.do_action_with_exception(describeDomainRecordsRequest)
        describeDomainRecords = json.loads(str(describeDomainRecordsResponse, encoding='utf-8'))
        # logger.debug('domain:{}',describeDomainRecords)
        if describeDomainRecords['TotalCount'] > 0 :
            record = describeDomainRecords['DomainRecords']['Record'][0]
            # logger.debug('record :{}', record)
            if ip != record['Value'] :
                {
                    'domain_name':domain_name,
                    'old_ip': record['Value']
                }
                modifyDomainList.append({
                    'domain_name':domain_name,
                    'old_ip': record['Value']
                })
        else :
            addDomainList.append(domain_name)
    logger.debug('addDomainList:{}',addDomainList)
    logger.debug('modifyDomainList:{}',modifyDomainList)
    return addDomainList,modifyDomainList

def do_addNewDomainRecordsByCurrentIp(ip,domainList):
    if len(domainList)>0 :
        batchAddDomainRequest =  OperateBatchDomainRequest()
        addDomainListRequest = []
        for add_domain_name in domainList:
            domainRecordInfo = {
                "Domain": add_domain_name,
                "Type": type_keyWord,
                "Rr": rr_keyWord,
                "Value": ip,
                "Ttl": 600,
                "NewRr": rr_keyWord,
                "NewType": type_keyWord,
                "NewValue": ip
            }
            addDomainListRequest.append(domainRecordInfo)
        batchAddDomainRequest.set_Type('RR_ADD')
        # logger.debug('addDomainListRequest : ', addDomainListRequest)
        batchAddDomainRequest.set_DomainRecordInfos(addDomainListRequest)
        batchAddDomainResponse = client.do_action_with_exception(batchAddDomainRequest)
        logger.debug('batchAddDomainResponse :{}',str(batchAddDomainResponse, encoding='utf-8'))
    return

def do_modifyDomainRecordsByCurrentIp(ip,domainList):
    if len(domainList)>0 :
        batchDelDomainRequest =  OperateBatchDomainRequest()
        delDomainListRequest = []
        for del_domain in domainList:
            delDomainRecordInfo = {
                "Domain": del_domain['domain_name'],
                "Type": type_keyWord,
                "Rr": rr_keyWord,
                "Value": del_domain['old_ip'],
                "Ttl": 600,
                "NewRr": rr_keyWord,
                "NewType": type_keyWord,
                "NewValue": ip
            }
            delDomainListRequest.append(delDomainRecordInfo)
        batchDelDomainRequest.set_Type('RR_DEL')
        # logger.debug('modifyDomainListRequest : ', delDomainListRequest)
        batchDelDomainRequest.set_DomainRecordInfos(delDomainListRequest)
        batchDelDomainResponse = client.do_action_with_exception(batchDelDomainRequest)
        # logger.debug('batchDelDomainResponse :',str(batchDelDomainResponse, encoding='utf-8'))
        delResponse = json.loads(str(batchDelDomainResponse, encoding='utf-8'))

        describeBatchResultCountRequest= DescribeBatchResultCountRequest()
        describeBatchResultCountRequest.set_BatchType('RR_DEL')
        describeBatchResultCountRequest.set_TaskId(delResponse['TaskId'])
        status = 0
        while status == 0:
            batchResultResponse=client.do_action_with_exception(describeBatchResultCountRequest)
            logger.debug('batchDelResultResponse :{}',str(batchResultResponse, encoding='utf-8'))
            batchResult = json.loads(str(batchResultResponse, encoding='utf-8'))
            status = batchResult['Status']
            time.sleep(1)

        batchModifyDomainRequest =  OperateBatchDomainRequest()
        modifyDomainListRequest = []
        for modify_domain in domainList:
            modifyDomainRecordInfo = {
                "Domain": modify_domain['domain_name'],
                "Type": type_keyWord,
                "Rr": rr_keyWord,
                "Value": ip,
                "Ttl": 600,
                "NewRr": rr_keyWord,
                "NewType": type_keyWord,
                "NewValue": ip
            }
            modifyDomainListRequest.append(modifyDomainRecordInfo)
        batchModifyDomainRequest.set_DomainRecordInfos(modifyDomainListRequest)
        batchModifyDomainRequest.set_Type('RR_ADD')
        batchModifyDomainResponse = client.do_action_with_exception(batchModifyDomainRequest)
        logger.debug('batchModifyDomainResponse :{}',str(batchModifyDomainResponse, encoding='utf-8'))
    return

def run_main():
    current_ip = get_currentIp()
    groupId = get_domainGroupIdByGroupName(domain_group_name)
    domainList = get_domainRecordsByGroupId(groupId)
    addDomainList,modifyDomainList = get_addAndModifyDomainList(current_ip,domainList)
    do_addNewDomainRecordsByCurrentIp(current_ip,addDomainList)
    do_modifyDomainRecordsByCurrentIp(current_ip,modifyDomainList)

def do_job():
    #创建调度器：BlockingScheduler
    scheduler = BlockingScheduler()
    #添加任务,时间间隔10分钟
    scheduler.add_job(run_main, 'interval', minutes=job_time_minutes,next_run_time=datetime.datetime.now(), id='test_job1')
    scheduler.start()

do_job()