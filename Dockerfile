FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -m grpc_tools.protoc -I./proto --python_out=./server --grpc_python_out=./server ./proto/file_storage.proto \
    && sed -i 's/^import file_storage_pb2 as file__storage__pb2$/from . import file_storage_pb2 as file__storage__pb2/' server/file_storage_pb2_grpc.py

RUN touch server/__init__.py client/__init__.py

CMD ["python", "-m", "server.server"]