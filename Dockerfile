FROM python:3.9.2-slim-buster
RUN python3 -m pip install aliyun-python-sdk-core \
    && python3 -m pip install aliyun-python-sdk-alidns \
    && python3 -m pip install aliyun-python-sdk-domain \
    && python3 -m pip install requests \
    && python3 -m pip install pyyaml \
    && python3 -m pip install loguru \
    && python3 -m pip install apscheduler
WORKDIR /aliyunddns
COPY alidns.py .
ENTRYPOINT [ "python3" ]
CMD [ "/aliyunddns/alidns.py" ] 