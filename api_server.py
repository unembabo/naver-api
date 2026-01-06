"""
네이버 플레이스 크롤링 API 서버 v2
실행 시마다 날짜/시간 폴더에 결과 저장
"""

from flask import Flask, request, Response
from flask_cors import CORS
import json
from datetime import datetime
import threading
import uuid
from queue import Queue
from collections import OrderedDict
import os

from place_fetch import fetch_reviews, clean_and_convert_to_int
from validate_results import ResultValidator

app = Flask(__name__)
CORS(app)

def json_response(data, status=200):
    """한글이 유니코드 이스케이프 없이 출력되는 JSON 응답"""
    return Response(
        json.dumps(data, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )

# 결과 저장 폴더 (실행 시 생성)
BASE_RESULTS_DIR = "results"



CURRENT_SESSION_DIR = None  # 현재 세션의 결과 폴더

def create_session_folder():
    """실행 시마다 새로운 날짜/시간 폴더 생성"""
    global CURRENT_SESSION_DIR
    
    if not os.path.exists(BASE_RESULTS_DIR):
        os.makedirs(BASE_RESULTS_DIR)
    
    # 날짜_시간 형식으로 폴더명 생성
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    CURRENT_SESSION_DIR = os.path.join(BASE_RESULTS_DIR, timestamp)
    os.makedirs(CURRENT_SESSION_DIR)
    
    print(f"📁 결과 저장 폴더 생성: {CURRENT_SESSION_DIR}")
    return CURRENT_SESSION_DIR

# ============================================
# 작업 큐 시스템
# ============================================
job_queue = Queue()
job_results = OrderedDict()  # job_id -> result
MAX_JOBS = 100  # 최대 저장할 작업 수


def process_job(job_id, keywords, max_results, mode=None):
    try:
        job_results[job_id]['status'] = 'processing'
        job_results[job_id]['started_at'] = datetime.now().isoformat()

        all_results = {}
        total_count = 0

        for idx, keyword in enumerate(keywords, 1):
            job_results[job_id]['progress'] = f"{idx}/{len(keywords)} - '{keyword}' 검색 중..."
            print(f"\n[Job {job_id[:8]}] [{idx}/{len(keywords)}] '{keyword}' 검색 중...")

            keyword_results = []
            repetitions = (max_results + 99) // 100

            for page in range(repetitions):
                start = page * 100 + 1
                display = min(100, max_results - len(keyword_results))

                if display <= 0:
                    break

                payload = create_query_payload(keyword, start, display)
                payload_string = json.dumps(payload)

                results = fetch_reviews(payload_string)

                if not results:
                    break

                for item in results:
                    rank = len(keyword_results) + 1
                    keyword_results.append({
                        "rank": rank,
                        "url": item.get('URL', 'N/A'),
                        "name": item.get('이름', 'N/A'),
                        "visitorReviews": item.get('방문자 리뷰', 0),
                        "blogReviews": item.get('블로그/카페 리뷰', 0),
                        "bookingReviews": item.get('예약자 리뷰', 0)
                    })

                if len(results) < display:
                    break

            all_results[keyword] = keyword_results
            total_count += len(keyword_results)

            # 키워드별 JSON 파일 저장 (날짜 폴더 내에 간단한 이름으로)
            # 세션 폴더가 없으면 생성
            if CURRENT_SESSION_DIR is None:
                create_session_folder()
            if not os.path.exists(CURRENT_SESSION_DIR):
                os.makedirs(CURRENT_SESSION_DIR)
                print(f"📁 폴더 생성: {CURRENT_SESSION_DIR}")

            safe_keyword = keyword.replace(" ", "_").replace("/", "_")
            keyword_filename = f"{safe_keyword}.json"
            keyword_filepath = os.path.join(CURRENT_SESSION_DIR, keyword_filename)

            keyword_data = {
                "success": True,
                "keyword": keyword,
                "count": len(keyword_results),
                "results": keyword_results
            }

            with open(keyword_filepath, 'w', encoding='utf-8') as f:
                json.dump(keyword_data, f, ensure_ascii=False, indent=2)

            print(f"📁 '{keyword}' 저장: {keyword_filename}")

        # 전체 결과 데이터 생성 (메모리용)
        result_data = {
            "success": True,
            "totalKeywords": len(keywords),
            "totalResults": total_count,
            "data": all_results
        }

        job_results[job_id]['status'] = 'completed'
        job_results[job_id]['completed_at'] = datetime.now().isoformat()
        job_results[job_id]['progress'] = '완료'
        job_results[job_id]['data'] = result_data
        job_results[job_id]['session_folder'] = CURRENT_SESSION_DIR
        job_results[job_id]['files'] = [f"{k.replace(' ', '_').replace('/', '_')}.json" for k in keywords]
        print(f"✅ [Job {job_id[:8]}] 완료 - 총 {total_count}개, 파일 {len(keywords)}개 생성")

        # 결과 검증 (mode가 "debug"일 때만 실행)
        if mode == "debug":
            print(f"\n🔍 [Job {job_id[:8]}] 결과 검증 시작...")
            validator = ResultValidator(CURRENT_SESSION_DIR)
            validator.validate_all()
            job_results[job_id]['validation'] = {
                "success_count": len(validator.success_files),
                "error_count": sum(len(files) for files in validator.error_files.values()),
                "errors_by_type": {k: len(v) for k, v in validator.error_files.items()},
                "count_stats": {
                    "count_0_total_fail": len(validator.count_stats["count_0"]),
                    "count_1_100_first_page": len(validator.count_stats["count_100"]),
                    "count_101_200_second_page": len(validator.count_stats["count_200"]),
                    "count_201_300_success": len(validator.count_stats["count_300"])
                }
            }
            print(f"✅ [Job {job_id[:8]}] 결과 검증 완료")

    except Exception as e:
        job_results[job_id]['status'] = 'failed'
        job_results[job_id]['error'] = str(e)
        print(f"❌ [Job {job_id[:8]}] 실패: {e}")


def worker():
    """큐에서 작업을 가져와 처리하는 워커"""
    while True:
        job = job_queue.get()
        if job is None:
            break
        job_id, keywords, max_results, mode = job
        process_job(job_id, keywords, max_results, mode)
        job_queue.task_done()


# 워커 스레드 시작
worker_thread = threading.Thread(target=worker, daemon=True)
worker_thread.start()


def create_query_payload(keyword, start=1, display=100):
    """
    네이버 플레이스 GraphQL 쿼리 생성
    """
    return {
        "operationName": "getPlacesList",
        "variables": {
            "input": {
                "query": keyword,
                "start": start,
                "display": display,
                "adult": False,
                "spq": False,
                "queryRank": "",
                "x": "0",
                "y": "0",
                "deviceType": "mobile"
            }
        },
        "query": """query getPlacesList($input: PlacesInput) {
  businesses: places(input: $input) {
    total
    items {
      id
      name
      normalizedName
      category
      cid
      detailCid {
        c0
        c1
        c2
        c3
        __typename
      }
      categoryCodeList
      dbType
      distance
      roadAddress
      address
      fullAddress
      commonAddress
      bookingUrl
      phone
      virtualPhone
      businessHours
      daysOff
      imageUrl
      imageCount
      x
      y
      visitorReviewCount
      visitorReviewScore
      blogCafeReviewCount
      bookingReviewCount
      __typename
    }
    __typename
  }
}"""
    }


# ============================================
# API 엔드포인트
# ============================================

@app.route('/')
def home():
    """API 정보 페이지"""
    return json_response({
        "service": "네이버 플레이스 크롤링 API v2",
        "version": "2.0",
        "current_session": CURRENT_SESSION_DIR,
        "endpoints": {
            "/api/search": {
                "method": "POST",
                "description": "네이버 플레이스 검색",
                "parameters": {
                    "keyword": "검색 키워드 (필수)",
                    "maxResults": "최대 결과 수 (기본값: 300)"
                }
            },
            "/api/queue": {
                "method": "POST",
                "description": "여러 키워드 큐에 추가",
                "parameters": {
                    "keywords": "키워드 배열 (필수)",
                    "maxResults": "키워드당 최대 결과 수 (기본값: 300)"
                }
            }
        }
    })


@app.route('/api/search', methods=['POST'])
def search():
    """
    단일 키워드 검색

    Request:
        {
            "keyword": "강남 카페",
            "maxResults": 300
        }
    """
    try:
        data = request.get_json()

        if not data or 'keyword' not in data:
            return json_response({
                "success": False,
                "error": "키워드(keyword)가 필요합니다."
            }, 400)

        keyword = data['keyword']
        max_results = data.get('maxResults', 300)

        print(f"\n{'='*60}")
        print(f"📥 검색 요청 받음")
        print(f"  - 키워드: {keyword}")
        print(f"  - 최대 개수: {max_results}")
        print(f"{'='*60}\n")

        # 페이징 처리 (100개씩)
        formatted_results = []
        repetitions = (max_results + 99) // 100

        for page in range(repetitions):
            start = page * 100 + 1
            display = min(100, max_results - len(formatted_results))

            if display <= 0:
                break

            print(f"  - 페이지 {page + 1}: {start}~{start + display - 1}")

            payload = create_query_payload(keyword, start, display)
            payload_string = json.dumps(payload)

            results = fetch_reviews(payload_string)

            if not results:
                if page == 0:
                    return json_response({
                        "success": False,
                        "error": "검색 결과가 없거나 요청에 실패했습니다."
                    }, 300)
                print(f"  - 더 이상 결과 없음")
                break

            for item in results:
                rank = len(formatted_results) + 1
                formatted_results.append({
                    "rank": rank,
                    "url": item.get('URL', 'N/A'),
                    "name": item.get('이름', 'N/A'),
                    "visitorReviews": item.get('방문자 리뷰', 0),
                    "blogReviews": item.get('블로그/카페 리뷰', 0),
                    "bookingReviews": item.get('예약자 리뷰', 0)
                })

            if len(results) < display:
                print(f"  - 마지막 페이지")
                break

        print(f"\n✅ {len(formatted_results)}개 결과 반환\n")

        return json_response({
            "success": True,
            "keyword": keyword,
            "count": len(formatted_results),
            "results": formatted_results
        })
    
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}\n")
        import traceback
        traceback.print_exc()

        return json_response({
            "success": False,
            "error": str(e)
        }, 300)


@app.route('/health', methods=['GET'])
def health():
    """헬스체크"""
    return json_response({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "current_session": CURRENT_SESSION_DIR
    })


# ============================================
# 큐 API 엔드포인트
# ============================================

@app.route('/api/queue', methods=['POST'])
def submit_job():
    """
    작업을 큐에 추가하고 job_id 반환

    Request:
        {
            "keywords": ["강남 카페", "포항물회"],
            "maxResults": 300
        }
    """
    data = request.get_json()

    if not data or 'keywords' not in data:
        return json_response({
            "success": False,
            "error": "키워드 배열(keywords)이 필요합니다."
        }, 400)

    keywords = data['keywords']
    max_results = data.get('maxResults', 300)
    mode = data.get('mode', None)  # "debug" 모드일 때만 validation 실행

    if not isinstance(keywords, list):
        return json_response({
            "success": False,
            "error": "keywords는 배열이어야 합니다."
        }, 400)

    # Job ID 생성
    job_id = str(uuid.uuid4())

    # 오래된 작업 정리
    while len(job_results) >= MAX_JOBS:
        job_results.popitem(last=False)

    # 작업 정보 저장
    job_results[job_id] = {
        "status": "queued",
        "progress": "대기 중...",
        "keywords": keywords,
        "maxResults": max_results,
        "mode": mode,
        "created_at": datetime.now().isoformat(),
        "data": None,
        "session_folder": CURRENT_SESSION_DIR
    }

    # 큐에 추가
    job_queue.put((job_id, keywords, max_results, mode))

    print(f"📥 [Job {job_id[:8]}] 큐에 추가됨 - 키워드: {keywords}")

    return json_response({
        "success": True,
        "jobId": job_id,
        "message": "작업이 큐에 추가되었습니다.",
        "sessionFolder": CURRENT_SESSION_DIR,
        "checkUrl": f"/api/queue/{job_id}"
    })


@app.route('/api/queue/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """작업 상태/결과 조회"""
    if job_id not in job_results:
        return json_response({
            "success": False,
            "error": "존재하지 않는 작업 ID입니다."
        }, 404)

    job = job_results[job_id]

    response = {
        "success": True,
        "jobId": job_id,
        "status": job['status'],
        "progress": job.get('progress', ''),
        "createdAt": job.get('created_at'),
        "startedAt": job.get('started_at'),
        "completedAt": job.get('completed_at'),
        "sessionFolder": job.get('session_folder')
    }

    if job['status'] == 'completed':
        response['data'] = job['data']
        response['files'] = job.get('files', [])
        response['validation'] = job.get('validation')
    elif job['status'] == 'failed':
        response['error'] = job.get('error', 'Unknown error')

    return json_response(response)


@app.route('/api/queue', methods=['GET'])
def list_jobs():
    """모든 작업 목록 조회"""
    jobs = []
    for job_id, job in job_results.items():
        jobs.append({
            "jobId": job_id,
            "status": job['status'],
            "progress": job.get('progress', ''),
            "keywords": job.get('keywords', []),
            "createdAt": job.get('created_at'),
            "sessionFolder": job.get('session_folder')
        })

    return json_response({
        "success": True,
        "count": len(jobs),
        "queueSize": job_queue.qsize(),
        "currentSession": CURRENT_SESSION_DIR,
        "jobs": jobs
    })


if __name__ == '__main__':
    # 서버 시작 시 세션 폴더 생성
    create_session_folder()
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║      네이버 플레이스 크롤링 API 서버 v2                  ║
╚═══════════════════════════════════════════════════════════╝

🚀 서버 시작...
📍 주소: http://localhost:5000
📁 결과 저장: {folder}

    """.format(folder=CURRENT_SESSION_DIR))

    app.run(host='0.0.0.0', port=5000, threaded=True)


# ============================================
# 폴더 구조:
# 
# 프로젝트/
# ├── api_server_v2.py
# ├── place_fetch.py
# └── results/
#     ├── 2025-12-30_13-00-00/
#     │   ├── 강남_카페.json
#     │   └── 홍대_맛집.json
#     └── 2025-12-30_15-30-00/
#         ├── 성수_카페.json
#         └── 이태원_술집.json
# ============================================