- [aliyunddns_python](#aliyunddns_python)
  - [需要安装的包](#需要安装的包)
          - [docker 镜像中已经集成](#docker-镜像中已经集成)
    - [1. 阿里云python sdk核心包](#1-阿里云python-sdk核心包)
    - [2. 阿里云dns sdk包](#2-阿里云dns-sdk包)
    - [3. 阿里云 云解析sdk包](#3-阿里云-云解析sdk包)
    - [4. 网络请求组件](#4-网络请求组件)
    - [5. yaml配置文件读取组件](#5-yaml配置文件读取组件)
    - [6. 日志框架](#6-日志框架)
    - [7. 定时任务框架](#7-定时任务框架)
- [Docker 启动命令](#docker-启动命令)
- [docker-compose 配置](#docker-compose-配置)
- [config.yaml 配置文件详解](#configyaml-配置文件详解)
# aliyunddns_python
基于Python3的阿里云DDNS
## 需要安装的包
###### docker 镜像中已经集成
### 1. 阿里云python sdk核心包
`python3 -m pip install aliyun-python-sdk-core`
### 2. 阿里云dns sdk包
`python3 -m pip install aliyun-python-sdk-alidns`
### 3. 阿里云 云解析sdk包
`python3 -m pip install aliyun-python-sdk-domain`
### 4. 网络请求组件
`python3 -m pip install requests`
### 5. yaml配置文件读取组件
`python3 -m pip install pyyaml`
### 6. 日志框架
`python3 -m pip install loguru`
### 7. 定时任务框架
`python3 -m pip install apscheduler`

# Docker 启动命令
```
docker run -d \
--name aliyunddns \
-v {your_config_path}:/aliyunddns/config.yaml \         #请修改为自己实际的config文件路径
--restart always \
yangjunqiu/aliyunddns:latest
```
# docker-compose 配置
```
version: "3.8"
services:
  aliyunddns:
    image: yangjunqiu/aliyunddns:latest
    container_name: aliyunddns
    volumes:
      - {your_config_path}:/aliyunddns/config.yaml      #请修改为自己实际的config文件路径
    restart: always
```


# config.yaml 配置文件详解
```
aliyun:  
  realIpUrl:                                  #获取真实外网IP的接口地址 列表
    - 'http://members.3322.org/dyndns/getip'
    - 'http://2018.ip138.com/ic.asp'
    - 'http://httpbin.org/ip'
    - 'https://api.ip.sb/ip'
    - 'http://ip.3322.net'
    - 'http://ip.qaros.com'
    - 'http://ip.cip.cc'
    - 'http://ident.me'
    - 'http://icanhazip.com'
    - 'https://api.ipify.org'
    - 'http://ip.42.pl/short'        
  type: 'A'                                   #DDNS type
  rr: ''                                      #自定义 二级域名       
  domainGroup: ''                             #自定义 阿里云上的域名分组
  access_key: ''                              #自定义 阿里云access_key
  access_key_secret: ''                       #自定义 阿里云access_key_secret
  region_id: 'cn-hangzhou'                    #阿里云主机区域
  job_time_minutes: 10                        #定时任务时间配置-分钟
```