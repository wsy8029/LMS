import pandas as pd
import boto3

raw_data = pd.DataFrame(columns = ["no", "title", "types", "level_type", "limit_time"])
raw_data = raw_data.append(pd.Series([1,"두 수의 합",["MATHEMATICS"],"LEVEL1","40"], index=raw_data.columns),ignore_index=True)
raw_data = raw_data.append(pd.Series([2,"가장 큰 수",["SORT"],"LEVEL2","50"], index=raw_data.columns),ignore_index=True)
raw_data = raw_data.append(pd.Series([3,"H-Index",["SORT"],"LEVEL3","40"], index=raw_data.columns),ignore_index=True)
raw_data = raw_data.append(pd.Series([4,"369게임",["STRING"],"LEVEL1","30"], index=raw_data.columns),ignore_index=True)
raw_data = raw_data.append(pd.Series([5,"피타고라스의 수",["GRAPH"],"LEVEL1","40"], index=raw_data.columns),ignore_index=True)
raw_data = raw_data.append(pd.Series([6,"전화번호 유형",["STRING"],"LEVEL1","30"], index=raw_data.columns),ignore_index=True)
raw_data = raw_data.append(pd.Series([7,"다음 숫자",["SORT", "STRING"],"LEVEL1","30"], index=raw_data.columns),ignore_index=True)
raw_data = raw_data.append(pd.Series([8,"시간 표시 바꾸기",["SORT", "ARRAY"],"LEVEL2","40"], index=raw_data.columns),ignore_index=True)
raw_data = raw_data.append(pd.Series([26,"a 와 z",["STACK","STRING"],"LEVEL4","50"], index=raw_data.columns),ignore_index=True)
raw_data = raw_data.append(pd.Series([31,"예산(budget)",["MATHEMATICS","STRING"],"LEVEL5","50"], index=raw_data.columns),ignore_index=True)

data_question = raw_data.to_numpy()



def compare_types(idx1, idx2):
    '''
    문제 유형의 유사도를 구하는 함수
    유형 항목은 discrete하기 때문에 비교 시 일치하는 유형이 있는지에 대한 확인을 한다.
    idx1 : 이미 푼 문제 index
    idx2 : 아직 안 푼 문제 index
    return : 동일한 유형의 포함 비율 (0~1)
    '''
    q1 = set(data_question[idx1][2]) # 비교 연산을 위해 set 형태로 변환
    q2 = set(data_question[idx2][2])
    return len(set.intersection(q1,q2)) / len(q2)

def compare_level_type(idx1, idx2):
    '''
    q1에 대한 q2의 레벨 차를 반환
    레벨은 유형(types)과 ordinal 데이터기 때문에, 두 레벨 차를 그대로 반환
    idx1 : 이미 푼 문제 index
    idx2 : 아직 안 푼 문제 index
    return : 레벨 차이(-4 ~ +4) ;
    '''
    q1 = int([q for q in data_question[idx1][3] if str.isdigit(q)][0]) # string에서 숫자만 추출
    q2 = int([q for q in data_question[idx2][3] if str.isdigit(q)][0])
    diff = q1-q2
    return diff

def compare_limit_time(idx1, idx2):
    '''
    q1에 대한 q2의 제한 시간 차를 하는 함수
    return : 제한시간 차를 반환
    '''
    q1 = data_question[idx1][4]
    q2 = data_question[idx2][4]
    diff = int(q1)-int(q2)
    return diff


def predict_passrate(qid1, passrate, qid2):
    '''
    TC통과율 예측 함수
    이미 푼 문제1의 ID와 TC 통과율을 입력하면, 문제2에 대한 TC통과율을 반환한다.
    return : q2 passrate
    반환되는 passrate가 q1에 비해 높아지려면
    1. 유형 유사도 up / 2. level difficulty up / 3. 제한시간 down 이어야 한다.
    - (유형 유사도(0~1) 값 - 0.5) * 10
    - 레벨 차이(-4 ~ +4)*5
    - 제한시간 차이(-20 ~ +20)*0.5
    '''
    #     passrate = 73
    types = compare_types(qid1, qid2)
    level_type = compare_level_type(qid1, qid2)
    limit_time = compare_limit_time(qid1, qid2)
    predicted_passrate = passrate + ((types - 0.5) * 10 + level_type * 5 + limit_time * 0.5)
    predicted_passrate = 100 if predicted_passrate > 100 else predicted_passrate

    return predicted_passrate


def predict_time(qid1, time, qid2):
    '''
    q2의 제한시간을 기준으로 산출된 조정시간을 더함
    '''
    #     time = 50
    types = compare_types(qid1, qid2)
    level_type = compare_level_type(qid1, qid2)
    limit_time = compare_limit_time(qid1, qid2)
    q2_limit_time = int(data_question[qid2][4])
    predicted_time = q2_limit_time + ((types - 0.5) * 10 + level_type * 5 + limit_time * 0.5)

    return int(predicted_time)


def predict_score(qid1, passrate, time, qid2):
    pr = predict_passrate(qid1, passrate, qid2) # 예측된 통과율
    pt = predict_time(qid1, time, qid2) # 예측된 소요시간 - 백분위 변경 필요 - 소요시간 내 완료 시 100점, 1분 초과시 1점 차감.
    limit_time_q2 = int(data_question[qid2][4])
    if pt <= limit_time_q2:
        score = 100
    else:
        score = 100 - (pt - limit_time_q2)
    predicted_score = pr*0.65 + limit_time_q2*0.35 # TC통과율 가중치 65%, 소요시간 가중치 35%
#     print(pr,pt,limit_time_q2, round(predicted_score,1))
    return round(predicted_score,1)





bucket = "dev-luxrobo-stream"
file_name = "evaluation_result_view.csv"

s3 = boto3.client('s3')
obj = s3.get_object(Bucket= bucket, Key= file_name)
data_eval = pd.read_csv(obj['Body'])


def find_user_score(uid):
    idxs = data_eval.index[data_eval['user_no'] == uid].tolist()
    idx = idxs[0]

    # 첫번째 인덱스의 문제번호, TC통과율, 소요시간, 종합점수 추출
    qid = data_eval['question_no'][idx]
    passrate = data_eval['accuracy_score'][idx]
    time = data_eval['duration_time'][idx]
    score = data_eval['total_score'][idx]

    return qid, passrate, time, score


def predict(user_no, question_no):
    qid_new = question_no
    qid_old, passrate, time, score = find_user_score(user_no)  # user_no 83 available
    p_passrate = predict_passrate(qid_old, passrate, qid_new)
    p_time = predict_time(qid_old, time, qid_new)
    p_score = predict_score(qid_old, passrate, time, qid_new)

    return p_passrate, p_time, p_score


print(predict(83, 3))