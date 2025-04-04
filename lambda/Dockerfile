FROM public.ecr.aws/lambda/python:3.9

RUN yum -y install gcc-c++

WORKDIR ${LAMBDA_TASK_ROOT}

COPY lambda_handler.py .
COPY env.txt .
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

RUN python lambda_handler.py

CMD [ "lambda_handler.handler"]