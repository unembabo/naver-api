# import json
# import time
# import random
# import requests

# def clean_and_convert_to_int(value):
#     """
#     Cleans a value by removing commas if it's a string,
#     then converts it to an integer. Handles None and errors.
#     """
#     if value is None:
#         return 0
#     if isinstance(value, str):
#         try:
#             return int(value.replace(',', ''))
#         except (ValueError, TypeError):
#             return 0
#     try:
#         return int(value)
#     except (ValueError, TypeError):
#         return 0


# def fetch_reviews(payload_string, max_retries=3):
#     """
#     Given a payload string, this function uses requests to fetch review data
#     from Naver Place API and returns a list of extracted item data.
    
#     429 에러 발생 시 자동으로 재시도합니다.
#     """
#     results = []
    
#     # 세션 사용 (자동 압축 해제)
#     session = requests.Session()
    
#     # iPhone 12 Pro User-Agent
#     user_agent = (
#         "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) "
#         "AppleWebKit/605.1.15 (KHTML, like Gecko) "
#         "Version/14.0 Mobile/15E148 Safari/604.1"
#     )
    
#     # 헤더 설정 (Accept-Encoding은 requests가 자동으로 처리)
#     headers = {
#         'Content-Type': 'application/json; charset=utf-8',
#         'User-Agent': user_agent,
#         'Accept': 'application/json',
#         'Accept-Language': 'ko-KR,ko;q=0.9',
#         'Origin': 'https://m.place.naver.com',
#         'Referer': 'https://m.place.naver.com/',
#     }
    
#     try:
#         # 속도 조절 (0.2~0.3초)
#         wait_time = random.uniform(0.23, 0.25)
#         print(f"⏳ {wait_time:.2f}초 대기...")
#         time.sleep(wait_time)

#         print("🚀 requests를 사용하여 API 요청을 보냅니다...")

#         api_url = "https://api.place.naver.com/graphql"

#         # POST 요청 전송 (json 파라미터 사용 - 자동 인코딩)
#         payload_dict = json.loads(payload_string)

#         response = session.post(
#             api_url,
#             json=payload_dict,
#             headers=headers,
#             timeout=30
#         )

#         # 429 에러 처리 (재시도 없이 에러 출력만)
#         if response.status_code == 429:
#             print(f"❌ 요청 실패: 429 Too Many Requests")
#             return []

#         # 응답 확인
#         if not response.ok:
#             print(f"❌ 요청 실패: {response.status_code} {response.reason}")
#             print(f"응답 내용: {response.text[:500]}...")
#             return []

#         print("✅ 요청 성공! 응답에서 필요한 데이터를 추출합니다.")

#         response_json = response.json()

#         items = response_json.get('data', {}).get('businesses', {}).get('items', [])

#         if not items:
#             print("⚠️ 응답에서 'items'를 찾을 수 없거나 비어있습니다.")
#             if 'data' in response_json:
#                 print(f"  - data 키 존재: {list(response_json['data'].keys())}")
#             else:
#                 print(f"  - data 키 없음. 응답 키: {list(response_json.keys())}")
#             return []

#         # 데이터 추출
#         for item in items:
#             place_id = item.get('id')
#             url = f"https://m.place.naver.com/place/{place_id}" if place_id else 'N/A'

#             result_item = {
#                 'URL': url,
#                 '이름': item.get('name', 'N/A'),
#                 '방문자 리뷰': clean_and_convert_to_int(item.get('visitorReviewCount')),
#                 '블로그/카페 리뷰': clean_and_convert_to_int(item.get('blogCafeReviewCount')),
#                 '예약자 리뷰': clean_and_convert_to_int(item.get('bookingReviewCount'))
#             }
#             results.append(result_item)

#         print(f"✅ 데이터 {len(results)}개 추출 완료.")
#         return results

#     except requests.exceptions.Timeout:
#         print("❌ 요청 시간 초과 (30초)")
#         return []

#     except requests.exceptions.ConnectionError as e:
#         print(f"❌ 연결 실패: {e}")
#         return []

#     except requests.exceptions.RequestException as e:
#         print(f"❌ 요청 에러: {e}")
#         return []

#     except json.JSONDecodeError as e:
#         print(f"❌ JSON 파싱 에러: {e}")
#         return []

#     except Exception as e:
#         print(f"❌ 예상치 못한 에러: {type(e).__name__}: {e}")
#         import traceback
#         traceback.print_exc()
#         return []

#     finally:
#         session.close()


# if __name__ == "__main__":
#     print("🚀 스크립트를 직접 실행합니다. query.json 파일에서 설정을 읽어옵니다.")
#     try:
#         with open('query.json', 'r', encoding='utf-8') as f:
#             payload = f.read()
        
#         review_data = fetch_reviews(payload)
        
#         if review_data:
#             print("\n--- 추출된 데이터 ---")
#             import pandas as pd
#             df = pd.DataFrame(review_data)
#             print(df)
#             print(f"\n총 {len(review_data)}개의 결과를 출력했습니다.")
#         else:
#             print("\n추출된 데이터가 없습니다.")
    
#     except FileNotFoundError:
#         print("❌ 'query.json' 파일을 찾을 수 없습니다. 스크립트를 종료합니다.")
#     except Exception as e:
#         print(f"❌ 에러: {e}")
#         import traceback
#         traceback.print_exc()



#################################################################################################################################
#####################################################################################################################
################################################################################################################


import json
import time
import random
import requests

def clean_and_convert_to_int(value):
    """
    Cleans a value by removing commas if it's a string,
    then converts it to an integer. Handles None and errors.
    """
    if value is None:
        return 0
    if isinstance(value, str):
        try:
            return int(value.replace(',', ''))
        except (ValueError, TypeError):
            return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def fetch_reviews(payload_string, max_retries=3):
    """
    Given a payload string, this function uses requests to fetch review data
    from Naver Place API and returns a list of extracted item data.
    
    429 에러 발생 시 자동으로 재시도합니다.
    """
    results = []
    
    # 세션 사용 (자동 압축 해제)
    session = requests.Session()
    
    # iPhone 12 Pro User-Agent
    user_agent = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/14.0 Mobile/15E148 Safari/604.1"
    )
    
    # 헤더 설정 (Accept-Encoding은 requests가 자동으로 처리)
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': user_agent,
        'Accept': 'application/json',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Origin': 'https://m.place.naver.com',
        'Referer': 'https://m.place.naver.com/',
    }
    
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # 속도 조절 (0.2~0.3초)
            wait_time = random.uniform(0.2, 0.3)
            
            # 재시도인 경우 더 긴 대기
            if retry_count > 0:
                wait_time = random.uniform(2.0, 4.0)
                print(f"🔄 재시도 {retry_count}/{max_retries} - {wait_time:.2f}초 대기...")
            else:
                print(f"⏳ {wait_time:.2f}초 대기...")
            
            time.sleep(wait_time)
            
            print("🚀 requests를 사용하여 API 요청을 보냅니다...")
            
            api_url = "https://api.place.naver.com/graphql"
            
            # POST 요청 전송 (json 파라미터 사용 - 자동 인코딩)
            payload_dict = json.loads(payload_string)
            
            response = session.post(
                api_url,
                json=payload_dict,  # json 파라미터로 전송 (자동 압축 해제)
                headers=headers,
                timeout=30
            )
            
            # 429 에러 처리
            if response.status_code == 429:
                print(f"⚠️ 429 Too Many Requests - 재시도 대기 중...")
                retry_count += 1
                
                if retry_count > max_retries:
                    print(f"❌ 최대 재시도 횟수({max_retries})를 초과했습니다.")
                    return []
                
                # 다음 루프로 계속 (재시도)
                continue
            
            # 응답 확인
            if not response.ok:
                print(f"❌ 요청 실패: {response.status_code} {response.reason}")
                print(f"응답 내용: {response.text[:500]}...")
                return []
            
            print("✅ 요청 성공! 응답에서 필요한 데이터를 추출합니다.")
            
            response_json = response.json()
            
            items = response_json.get('data', {}).get('businesses', {}).get('items', [])
            
            if not items:
                print("⚠️ 응답에서 'items'를 찾을 수 없거나 비어있습니다.")
                # 디버깅 정보
                if 'data' in response_json:
                    print(f"  - data 키 존재: {list(response_json['data'].keys())}")
                else:
                    print(f"  - data 키 없음. 응답 키: {list(response_json.keys())}")
                return []
            
            # 데이터 추출
            for item in items:
                place_id = item.get('id')
                url = f"https://m.place.naver.com/place/{place_id}" if place_id else 'N/A'
                
                result_item = {
                    'URL': url,
                    '이름': item.get('name', 'N/A'),
                    '방문자 리뷰': clean_and_convert_to_int(item.get('visitorReviewCount')),
                    '블로그/카페 리뷰': clean_and_convert_to_int(item.get('blogCafeReviewCount')),
                    '예약자 리뷰': clean_and_convert_to_int(item.get('bookingReviewCount'))
                }
                results.append(result_item)
            
            print(f"✅ 데이터 {len(results)}개 추출 완료.")
            return results
        
        except requests.exceptions.Timeout:
            print("❌ 요청 시간 초과 (30초)")
            retry_count += 1
            if retry_count > max_retries:
                return []
            continue
            
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 연결 실패: {e}")
            retry_count += 1
            if retry_count > max_retries:
                return []
            continue
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 에러: {e}")
            return []
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 에러: {e}")
            print(f"응답 타입: {response.headers.get('Content-Type')}")
            print(f"응답 인코딩: {response.encoding}")
            print(f"응답 크기: {len(response.content)} bytes")
            return []
            
        except Exception as e:
            print(f"❌ 예상치 못한 에러: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    session.close()
    return results


if __name__ == "__main__":
    print("🚀 스크립트를 직접 실행합니다. query.json 파일에서 설정을 읽어옵니다.")
    try:
        with open('query.json', 'r', encoding='utf-8') as f:
            payload = f.read()
        
        review_data = fetch_reviews(payload)
        
        if review_data:
            print("\n--- 추출된 데이터 ---")
            import pandas as pd
            df = pd.DataFrame(review_data)
            print(df)
            print(f"\n총 {len(review_data)}개의 결과를 출력했습니다.")
        else:
            print("\n추출된 데이터가 없습니다.")
    
    except FileNotFoundError:
        print("❌ 'query.json' 파일을 찾을 수 없습니다. 스크립트를 종료합니다.")
    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback
        traceback.print_exc()