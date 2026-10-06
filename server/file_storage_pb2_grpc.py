import grpc
from . import file_storage_pb2 as file__storage__pb2

class FileStorageStub:
    def __init__(self, channel):
        self.Login = channel.unary_unary('/securefilestorage.FileStorage/Login', request_serializer=file__storage__pb2.LoginRequest.SerializeToString, response_deserializer=file__storage__pb2.LoginResponse.FromString)
        self.Upload = channel.unary_unary('/securefilestorage.FileStorage/Upload', request_serializer=file__storage__pb2.UploadRequest.SerializeToString, response_deserializer=file__storage__pb2.FileResponse.FromString)
        self.Download = channel.unary_unary('/securefilestorage.FileStorage/Download', request_serializer=file__storage__pb2.DownloadRequest.SerializeToString, response_deserializer=file__storage__pb2.FileResponse.FromString)
        self.List = channel.unary_unary('/securefilestorage.FileStorage/List', request_serializer=file__storage__pb2.ListRequest.SerializeToString, response_deserializer=file__storage__pb2.ListResponse.FromString)
        self.Delete = channel.unary_unary('/securefilestorage.FileStorage/Delete', request_serializer=file__storage__pb2.DeleteRequest.SerializeToString, response_deserializer=file__storage__pb2.FileResponse.FromString)

class FileStorageServicer:
    def Login(self, request, context): context.set_code(grpc.StatusCode.UNIMPLEMENTED); context.set_details('Method not implemented!'); raise NotImplementedError()
    def Upload(self, request, context): context.set_code(grpc.StatusCode.UNIMPLEMENTED); context.set_details('Method not implemented!'); raise NotImplementedError()
    def Download(self, request, context): context.set_code(grpc.StatusCode.UNIMPLEMENTED); context.set_details('Method not implemented!'); raise NotImplementedError()
    def List(self, request, context): context.set_code(grpc.StatusCode.UNIMPLEMENTED); context.set_details('Method not implemented!'); raise NotImplementedError()
    def Delete(self, request, context): context.set_code(grpc.StatusCode.UNIMPLEMENTED); context.set_details('Method not implemented!'); raise NotImplementedError()

def add_FileStorageServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'Login': grpc.unary_unary_rpc_method_handler(servicer.Login, request_deserializer=file__storage__pb2.LoginRequest.FromString, response_serializer=file__storage__pb2.LoginResponse.SerializeToString),
        'Upload': grpc.unary_unary_rpc_method_handler(servicer.Upload, request_deserializer=file__storage__pb2.UploadRequest.FromString, response_serializer=file__storage__pb2.FileResponse.SerializeToString),
        'Download': grpc.unary_unary_rpc_method_handler(servicer.Download, request_deserializer=file__storage__pb2.DownloadRequest.FromString, response_serializer=file__storage__pb2.FileResponse.SerializeToString),
        'List': grpc.unary_unary_rpc_method_handler(servicer.List, request_deserializer=file__storage__pb2.ListRequest.FromString, response_serializer=file__storage__pb2.ListResponse.SerializeToString),
        'Delete': grpc.unary_unary_rpc_method_handler(servicer.Delete, request_deserializer=file__storage__pb2.DeleteRequest.FromString, response_serializer=file__storage__pb2.FileResponse.SerializeToString),
    }
    generic_handler = grpc.method_handlers_generic_handler('securefilestorage.FileStorage', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
