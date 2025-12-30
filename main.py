# import json
# import os
# import re
# import pandas as pd
# from datetime import datetime
# from tkinter import Tk, filedialog
# from place_fetch import fetch_reviews


# def sanitize_filename(name):
#     """Remove characters that are invalid in Windows filenames."""
#     return re.sub(r'[\\/*?:"<>|]', "", name)


# def get_unique_filename(directory, base_name):
#     """
#     Generates a unique filename inside a given directory.
#     If 'base_name.json' exists, it tries 'base_name_2.json', etc.
#     """
#     sanitized_name = sanitize_filename(base_name)
#     counter = 1
#     file_path = os.path.join(directory, f"{sanitized_name}.json")

#     while os.path.exists(file_path):
#         counter += 1
#         file_path = os.path.join(directory, f"{sanitized_name}_{counter}.json")

#     return file_path


# def run_automation_json():
#     """
#     Orchestrates reading keywords, fetching reviews, and saving them
#     to JSON files within a timestamped results folder.
#     """
#     try:
#         now = datetime.now()
#         folder_name = now.strftime("%Y-%m-%d_%H-%M-%S")
#         os.makedirs(folder_name, exist_ok=True)
#         print(f"📂 결과는 '{folder_name}' 폴더에 저장됩니다.")

#         # pagination settings
#         repetitions = 3
#         display_count = 100

#         # 1) Excel path
#         root = Tk()
#         root.withdraw()
#         excel_path = filedialog.askopenfilename(
#             title="검색할 키워드가 있는 엑셀 파일을 선택하세요",
#             filetypes=(("Excel files", "*.xlsx *.xls"), ("All files", "*.*"))
#         )
#         if not excel_path:
#             print("❌ 파일 선택이 취소되었습니다.")
#             return

#         # 2) Read keywords
#         print(f"📖 '{excel_path}' 파일의 A열에서 키워드를 읽어옵니다.")
#         df = pd.read_excel(excel_path, header=None, usecols=[0])
#         keywords = df[0].dropna().astype(str).tolist()

#         if not keywords:
#             print("⚠️ 엑셀 파일의 A열에서 키워드를 찾을 수 없습니다.")
#             return

#         print(f"✅ 총 {len(keywords)}개의 키워드를 찾았습니다.")

#         # 3) JSON query template
#         with open('query.json', 'r', encoding='utf-8') as f:
#             query_template = json.load(f)

#     except FileNotFoundError:
#         print("❌ 파일을 찾을 수 없습니다. 경로를 다시 확인해주세요.")
#         return
#     except Exception as e:
#         print(f"❌ 파일 처리 중 오류가 발생했습니다: {e}")
#         return

#     # 4) Loop
#     for i, keyword in enumerate(keywords):
#         print(f"\n--- [{i+1}/{len(keywords)}] 키워드 처리 중: {keyword} ---")

#         all_keyword_results = []
#         seen_keys = set()  # 중복 감지(페이징 무시/반복 응답 방지)

#         for page in range(repetitions):
#             start_index = 1 + (page * display_count)
#             print(f"  - ({page + 1}/{repetitions}) 페이지 로드 중 (start: {start_index}, display: {display_count})...")

#             # 안전하게 input dict 보장
#             variables = query_template.setdefault("variables", {})
#             input_obj = variables.setdefault("input", {})

#             input_obj["query"] = keyword
#             input_obj["start"] = start_index
#             input_obj["display"] = display_count  # ✅ display도 강제 세팅

#             payload_string = json.dumps(query_template, ensure_ascii=False)

#             try:
#                 results_data = fetch_reviews(payload_string)

#                 if not results_data:
#                     print("  - 더 이상 결과가 없거나(API 하드캡/페이징 제한) 응답이 비어 중단합니다.")
#                     break

#                 # ✅ “새로운 항목”만 추가 (API가 start를 무시하고 같은 100개 반복하는 경우 감지)
#                 new_items = []
#                 for item in results_data:
#                     # 고유키 우선순위: url -> (name, rank) -> 전체 json
#                     if isinstance(item, dict):
#                         key = item.get("URL") or item.get("url") or (item.get("이름"), item.get("순위")) or json.dumps(item, ensure_ascii=False, sort_keys=True)
#                     else:
#                         key = str(item)

#                     if key not in seen_keys:
#                         seen_keys.add(key)
#                         new_items.append(item)

#                 if not new_items:
#                     print("  - 이번 페이지는 이전 페이지와 동일한 결과로 판단되어(페이징 무시) 중단합니다.")
#                     break

#                 all_keyword_results.extend(new_items)
#                 print(f"  - {len(new_items)}개 신규 결과 추가. (누적 {len(all_keyword_results)}개 / 원본응답 {len(results_data)}개)")

#                 # 혹시 300을 넘길 경우 컷
#                 if len(all_keyword_results) >= repetitions * display_count:
#                     all_keyword_results = all_keyword_results[:repetitions * display_count]
#                     break

#             except Exception as e:
#                 print(f"❌ '{keyword}' 처리 중 오류 발생 (start: {start_index}): {e}")
#                 break

#         if all_keyword_results:
#             results_df = pd.DataFrame(all_keyword_results)

#             # Rank Column
#             if '순위' in results_df.columns:
#                 # 이미 순위가 있다면 유지하고, 없으면 새로 부여
#                 pass
#             else:
#                 results_df.insert(0, '순위', range(1, len(results_df) + 1))

#             # Ensure review counts are integers
#             review_cols = ['방문자 리뷰', '블로그/카페 리뷰', '예약자 리뷰']
#             for col in review_cols:
#                 if col in results_df.columns:
#                     results_df[col] = pd.to_numeric(results_df[col], errors="coerce").fillna(0).astype(int)

#             # Rename columns to English
#             results_df.rename(columns={
#                 '순위': 'rank',
#                 '이름': 'name',
#                 '방문자 리뷰': 'visitor_reviews',
#                 '블로그/카페 리뷰': 'blog_cafe_reviews',
#                 '예약자 리뷰': 'booking_reviews',
#                 'URL': 'url'
#             }, inplace=True)

#             output_filename = get_unique_filename(folder_name, keyword)
#             results_df.to_json(output_filename, orient='records', force_ascii=False, indent=4)
#             print(f"💾 '{output_filename}' 파일에 총 {len(all_keyword_results)}개의 결과를 저장했습니다.")
#         else:
#             print(f"🤷‍♂️ '{keyword}'에 대한 검색 결과가 없습니다.")

#     print("\n🎉 모든 키워드에 대한 작업이 완료되었습니다.")


# if __name__ == "__main__":
#     run_automation_json()
