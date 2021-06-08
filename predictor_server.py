from concurrent import futures
import time
import grpc

import predict_pb2
import predict_pb2_grpc
from predict import predicts

# class ContentsRecommender(recommend_pb2_grpc.RecommenderServicer): # 자체 클래스 선언
#     def GetRecommend(self, request, context): # RPC
#         result = recom(int(request.name)) # 받아온 후에 다시 int형으로 변환하여 인자로 넣음
#         return recommend_pb2.Contents(message=str(result))
#         # return recommend_pb2.Contents(message='Hello, %s!' % request.name)

class ScorePredictor(predict_pb2_grpc.PredictorServicer):
    def GetPredict(self, request, context):
        result = predicts(request.unum, request.qnum)
        return predict_pb2.Predictions(passrate=result[0], time=result[1], score = result[2])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    predict_pb2_grpc.add_PredictorServicer_to_server(ScorePredictor(), server)
    server.add_insecure_port('localhost:50051')
    server.start()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        server.stop(0)

# def serve():
#     server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
#     predict_pb2_grpc.add_PredictorServicer_to_server()
#     recommend_pb2_grpc.add_RecommenderServicer_to_server(ContentsRecommender(), server)
#     server.add_insecure_port('localhost:50051')
#     server.start()
#     try:
#         while True:
#             time.sleep(60)
#     except KeyboardInterrupt:
#         server.stop(0)


if __name__ == '__main__':
    serve()