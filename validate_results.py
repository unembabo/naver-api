"""
네이버 플레이스 크롤링 결과 검증 스크립트
results 폴더의 JSON 파일들을 분석하여 에러 리포트 생성
"""

import json
import os
from datetime import datetime
from collections import defaultdict

class ResultValidator:
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        self.total_files = 0
        self.success_files = []
        self.error_files = defaultdict(list)
        
    def validate_file(self, filepath):
        """단일 JSON 파일 검증"""
        filename = os.path.basename(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 기본 구조 확인
            if not isinstance(data, dict):
                return {
                    "filename": filename,
                    "error_type": "invalid_structure",
                    "error_message": "JSON 구조가 올바르지 않습니다.",
                    "count": 0
                }
            
            keyword = data.get('keyword', 'Unknown')
            success = data.get('success', False)
            count = data.get('count', 0)
            results = data.get('results', [])
            
            # 에러 체크
            errors = []
            
            # 1. success가 False인 경우
            if not success:
                error_msg = data.get('error', 'Unknown error')
                
                # 429 에러 체크
                if '429' in error_msg or 'Too Many Requests' in error_msg:
                    return {
                        "filename": filename,
                        "keyword": keyword,
                        "error_type": "429_error",
                        "error_message": error_msg,
                        "count": 0
                    }
                else:
                    return {
                        "filename": filename,
                        "keyword": keyword,
                        "error_type": "api_error",
                        "error_message": error_msg,
                        "count": 0
                    }
            
            # 2. 결과가 200개 미만인 경우 (순위 부족)
            if count < 200:
                return {
                    "filename": filename,
                    "keyword": keyword,
                    "error_type": "insufficient_results",
                    "error_message": f"순위가 {count}개만 저장됨 (200개 미만)",
                    "count": count
                }
            
            # 3. count와 results 길이 불일치
            if count != len(results):
                return {
                    "filename": filename,
                    "keyword": keyword,
                    "error_type": "count_mismatch",
                    "error_message": f"count({count})와 results 길이({len(results)})가 불일치",
                    "count": count
                }
            
            # 정상 파일
            return {
                "filename": filename,
                "keyword": keyword,
                "error_type": None,
                "count": count,
                "status": "success"
            }
            
        except json.JSONDecodeError:
            return {
                "filename": filename,
                "error_type": "json_parse_error",
                "error_message": "JSON 파싱 실패",
                "count": 0
            }
        except Exception as e:
            return {
                "filename": filename,
                "error_type": "unknown_error",
                "error_message": str(e),
                "count": 0
            }
    
    def validate_all(self):
        """results 폴더의 모든 JSON 파일 검증"""
        if not os.path.exists(self.results_dir):
            print(f"❌ '{self.results_dir}' 폴더를 찾을 수 없습니다.")
            return
        
        json_files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
        
        if not json_files:
            print(f"❌ '{self.results_dir}' 폴더에 JSON 파일이 없습니다.")
            return
        
        self.total_files = len(json_files)
        print(f"📁 총 {self.total_files}개 파일 검증 중...\n")
        
        for filename in json_files:
            filepath = os.path.join(self.results_dir, filename)
            result = self.validate_file(filepath)
            
            if result.get('error_type'):
                self.error_files[result['error_type']].append(result)
            else:
                self.success_files.append(result)
        
        self.print_report()
        self.save_report()
    
    def print_report(self):
        """검증 결과 출력"""
        print("="*80)
        print("📊 네이버 플레이스 크롤링 결과 검증 리포트")
        print("="*80)
        print(f"검증 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"검증 폴더: {self.results_dir}")
        print("-"*80)
        
        success_count = len(self.success_files)
        error_count = sum(len(files) for files in self.error_files.values())
        
        print(f"\n✅ 정상: {success_count}개")
        print(f"❌ 에러: {error_count}개")
        
        if not self.error_files:
            print("\n🎉 모든 파일이 정상적으로 크롤링되었습니다!")
            return
        
        # 에러 타입별 상세 정보
        print("\n" + "="*80)
        print("❌ 에러 상세")
        print("="*80)
        
        # 1. 429 에러
        if '429_error' in self.error_files:
            files = self.error_files['429_error']
            print(f"\n1️⃣ 429 에러 (Too Many Requests): {len(files)}개")
            print("-"*80)
            for item in files:
                print(f"   📄 {item['filename']}")
                print(f"      키워드: {item['keyword']}")
                print(f"      에러: {item['error_message']}")
                print()
        
        # 2. 200위 미만 (순위 부족)
        if 'insufficient_results' in self.error_files:
            files = self.error_files['insufficient_results']
            print(f"\n2️⃣ 200위 미만 (순위 부족): {len(files)}개")
            print("-"*80)
            # 순위 개수별로 정렬
            sorted_files = sorted(files, key=lambda x: x['count'])
            for item in sorted_files:
                print(f"   📄 {item['filename']}")
                print(f"      키워드: {item['keyword']}")
                print(f"      저장된 순위: {item['count']}개")
                print()
        
        # 3. API 에러
        if 'api_error' in self.error_files:
            files = self.error_files['api_error']
            print(f"\n3️⃣ API 에러: {len(files)}개")
            print("-"*80)
            for item in files:
                print(f"   📄 {item['filename']}")
                print(f"      키워드: {item['keyword']}")
                print(f"      에러: {item['error_message']}")
                print()
        
        # 4. 기타 에러
        other_errors = {k: v for k, v in self.error_files.items() 
                       if k not in ['429_error', 'insufficient_results', 'api_error']}
        
        if other_errors:
            print(f"\n4️⃣ 기타 에러: {sum(len(v) for v in other_errors.values())}개")
            print("-"*80)
            for error_type, files in other_errors.items():
                print(f"\n   [{error_type}]: {len(files)}개")
                for item in files:
                    print(f"   📄 {item['filename']}")
                    if 'keyword' in item:
                        print(f"      키워드: {item['keyword']}")
                    print(f"      에러: {item.get('error_message', 'Unknown')}")
                    print()
        
        print("="*80)
        print("\n💡 재요청이 필요한 키워드 목록:")
        print("-"*80)
        retry_keywords = []
        for files in self.error_files.values():
            for item in files:
                if 'keyword' in item and item['keyword'] != 'Unknown':
                    retry_keywords.append(item['keyword'])
        
        if retry_keywords:
            print(", ".join(retry_keywords))
        else:
            print("없음")
        
        print("\n")
    
    def save_report(self):
        """검증 결과를 JSON 파일로 저장"""
        report = {
            "validation_time": datetime.now().isoformat(),
            "results_dir": self.results_dir,
            "summary": {
                "total_files": self.total_files,
                "success_count": len(self.success_files),
                "error_count": sum(len(files) for files in self.error_files.values())
            },
            "errors_by_type": {
                error_type: [
                    {
                        "filename": item['filename'],
                        "keyword": item.get('keyword', 'Unknown'),
                        "error_message": item.get('error_message', ''),
                        "count": item.get('count', 0)
                    }
                    for item in files
                ]
                for error_type, files in self.error_files.items()
            },
            "success_files": [
                {
                    "filename": item['filename'],
                    "keyword": item['keyword'],
                    "count": item['count']
                }
                for item in self.success_files
            ]
        }
        
        # 리포트 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"validation_report_{timestamp}.json"
        report_filepath = os.path.join(self.results_dir, report_filename)
        
        with open(report_filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📁 검증 리포트 저장: {report_filepath}\n")


def main():
    import sys
    
    # 폴더 경로 인자 받기
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║   네이버 플레이스 크롤링 결과 검증 스크립트              ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    validator = ResultValidator(results_dir)
    validator.validate_all()


if __name__ == "__main__":
    main()


# ============================================
# 사용법:
#
# 1. 기본 사용 (results 폴더 검증)
#    python validate_results.py
#
# 2. 특정 폴더 검증
#    python validate_results.py /path/to/results
#
# ============================================