from __future__ import print_function

import grpc

import predict_pb2
import predict_pb2_grpc

def run(user_no, question_no):
    channel = grpc.insecure_channel('localhost:50051')
    stub = predict_pb2_grpc.PredictorStub(channel)
    # response = stub.GetRecommend(recommend_pb2.UserInfo(name='you'))
    # num = (user_no, question_no)
    response = stub.GetPredict(predict_pb2.Numbers(unum=user_no, qnum=question_no))
    # response = stub.GetRecommend(predict_pb2.UserInfo(user_no, question_no)) #처음 .proto에 reque로st를 str 형식의 name으로 설정
    pr = round(response.passrate,1)
    ti = round(response.time,1)
    sc = round(response.score,1)
    print("Predictions: ", str(pr), str(ti), str(sc))

if __name__ == '__main__':
    # run(239)
    run(83,9)