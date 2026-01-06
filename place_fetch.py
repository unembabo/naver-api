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


# 전역 변수: 마지막 요청 시간 추적
_last_request_time = 0
_request_lock = None
_global_session = None  # 전역 세션 추가

def _get_lock():
    """Thread-safe lock for rate limiting"""
    global _request_lock
    if _request_lock is None:
        import threading
        _request_lock = threading.Lock()
    return _request_lock

def _get_session():
    """전역 세션 재사용"""
    global _global_session
    if _global_session is None:
        _global_session = requests.Session()
    return _global_session


def fetch_reviews(payload_string, max_retries=2):
    """
    Given a payload string, this function uses requests to fetch review data
    from Naver Place API and returns a list of extracted item data.

    429 에러 방지를 위해 전역 rate limiting + User-Agent 랜덤화 적용
    """
    global _last_request_time

    results = []

    session = _get_session()  # 전역 세션 재사용

    # User-Agent 풀 (다양한 모바일 기기)
    user_agents = [
        # iPhone
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        # Android Samsung
        "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.135 Mobile Safari/537.36",
        # Android Pixel
        "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.128 Mobile Safari/537.36",
        # Android LG
        "Mozilla/5.0 (Linux; Android 10; LM-G900N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36",
    ]

    # 랜덤 User-Agent 선택
    user_agent = random.choice(user_agents)

    # 헤더 설정 (더 실제 브라우저처럼)
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': user_agent,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Origin': 'https://m.place.naver.com',
        'Referer': 'https://m.place.naver.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Connection': 'keep-alive',
    }
    
    # payload를 미리 파싱 (에러 조기 발견)
    try:
        print("📋 Payload JSON 파싱 중...")
        payload_dict = json.loads(payload_string)
        print("✅ Payload 파싱 성공")
    except json.JSONDecodeError as e:
        print(f"❌ Payload JSON 파싱 실패: {e}")
        print(f"Payload 내용 (처음 200자): {payload_string[:200]}")
        return []
    
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # Thread-safe rate limiting
            lock = _get_lock()
            with lock:
                current_time = time.time()
                time_since_last = current_time - _last_request_time
                
                if retry_count == 0:
                    # 최소 0.23초 간격 보장 (전역)
                    min_interval = 0.23
                    if time_since_last < min_interval:
                        additional_wait = min_interval - time_since_last
                        time.sleep(additional_wait)
                    
                    # 기본 대기 (0.3~0.5초)
                    wait_time = random.uniform(0.23, 0.25)
                    print(f"⏳ {wait_time:.2f}초 대기...")
                    time.sleep(wait_time)
                else:
                    if retry_count == 1:
                        wait_time = 1.5
                    else:
                        wait_time = random.uniform(1.5, 2.5)
                    print(f"🔄 재시도 {retry_count}/{max_retries} - {wait_time:.2f}초 대기...")
                    time.sleep(wait_time)
                
                _last_request_time = time.time()
            
            print("🚀 requests를 사용하여 API 요청을 보냅니다...")
            
            api_url = "https://api.place.naver.com/graphql"
            
            response = session.post(
                api_url,
                json=payload_dict,
                headers=headers,
                timeout=30
            )
            
            # 429 에러 처리
            if response.status_code == 429:
                retry_count += 1
                
                if retry_count > max_retries:
                    print(f"❌ 최대 재시도 횟수({max_retries})를 초과했습니다.")
                    return []
                
                print(f"⚠️ 429 Too Many Requests - 대기 후 재시도...")
                continue
            
            # 응답 확인
            if not response.ok:
                print(f"❌ 요청 실패: {response.status_code} {response.reason}")
                print(f"응답 내용: {response.text[:500]}...")
                return []
            
            print("✅ 요청 성공! 응답에서 필요한 데이터를 추출합니다.")
            
            print(f"📊 응답 상태: {response.status_code}")
            print(f"📊 Content-Type: {response.headers.get('Content-Type')}")
            print(f"📊 응답 크기: {len(response.content)} bytes")
            
            if not response.content or len(response.content) == 0:
                print("⚠️ 응답이 비어있습니다.")
                return []
            
            try:
                response_text = response.text
             
            except Exception as e:
                print(f"⚠️ 응답 텍스트 읽기 실패: {e}")
            
            # JSON 파싱
            try:
                response_json = response.json()
            except json.JSONDecodeError as e:
                print(f"⚠️ 응답 JSON 파싱 에러: {e}")
                print(f"📄 응답 내용: {response.text[:300] if response.text else '(비어있음)'}")
                retry_count += 1
                if retry_count > max_retries:
                    print(f"❌ 최대 재시도 횟수({max_retries})를 초과했습니다.")
                    return []
                print("🔄 재시도합니다...")
                continue
            
            items = response_json.get('data', {}).get('businesses', {}).get('items', [])
            
            if not items:
                print("⚠️ 응답에서 'items'를 찾을 수 없거나 비어있습니다.")
                print(f"  - 전체 응답: {json.dumps(response_json, ensure_ascii=False)[:500]}")
                if 'data' in response_json:
                    print(f"  - data 키 존재: {list(response_json['data'].keys())}")
                return []
            
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
            
        except Exception as e:
            print(f"❌ 예상치 못한 에러: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    return results


if __name__ == "__main__":
    print("🚀 스크립트를 직접 실행합니다. query.json 파일에서 설정을 읽어옵니다.")
    try:
        with open('query.json', 'r', encoding='utf-8') as f:
            payload = f.read()
        
        print(f"📄 읽은 payload 길이: {len(payload)} 문자")
        print(f"📄 Payload 내용 (처음 200자): {payload[:200]}")
        
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