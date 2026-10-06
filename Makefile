proto:
	python -m grpc_tools.protoc -I proto --python_out=server --grpc_python_out=server proto/file_storage.proto

server:
	python -m server.server

client:
	python -m client.client
