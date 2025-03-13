import streamlit as st
import os
import pandas as pd

# 기본 경로 설정 (실제 파일 경로로 변경 필요)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 자동으로 현재 경로 인식

# 회사 목록 설정 (실제 폴더 구조에서 불러올 수도 있음)
company_list = ["강인교통", "강인여객", "강화교통", "공영급행", "대인교통", "도영운수", "동화운수", "마니교통", "은혜교통", "미래교통", "미추홀교통", "부성여객", "삼환교통", "삼환운수", "선진여객", "성산여객", "성원운수", "세운교통", "송도버스", "시영운수", "신동아교통", "신화여객", "신흥교통", "영종운수", "원진운수", "인천교통공사", "인천스마트", "인천제물포교통", "청라교통", "청룡교통", "태양여객", "해성운수"]

# 년/월 폴더 목록 가져오기
if os.path.exists(BASE_DIR):
    year_month_folders = sorted([f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))])
else:
    year_month_folders = []

# 모든 년/월 폴더에서 파일 수집
file_dict = {}

for ym in year_month_folders:
    folder_path = os.path.join(BASE_DIR, ym)
    if os.path.exists(folder_path):
        files = [f for f in os.listdir(folder_path) if f.endswith(".xlsx") or f.endswith(".csv")]
        file_dict[ym] = files

# 운수사 목록 추출 (파일명에서 운수사 부분만 가져옴)
company_dict = {}  # {회사명: 비밀번호} 저장
for files in file_dict.values():
    for file in files:
        parts = file.split("_")[0]  # "01.강인교통" 추출
        if "." in parts:
            num, name = parts.split(".", 1)  # "01", "강인교통" 분리
            password = f"5{num}"  # 비밀번호 설정: "501", "502" ...
            company_dict[name] = password  # 딕셔너리에 저장

company_list = sorted(company_dict.keys())

# 기본 선택값 추가
company_list.insert(0, "운수사를 선택해주세요")

# 운수사 선택
selected_company = st.sidebar.selectbox("운수사 선택", company_list, index=0)

# 기본 선택값일 경우 안내 메시지만 출력
if selected_company == "운수사를 선택해주세요":
    st.write("### 🚗 운수사를 선택해주세요.")
else:
    # 비밀번호 입력 필드 추가
    entered_password = st.sidebar.text_input(f"{selected_company} 비밀번호 입력:", type="password")

    # 올바른 비밀번호 확인
    correct_password = company_dict.get(selected_company, "")

    if entered_password == correct_password:
        st.write(f"### {selected_company} 운전성향분석표 파일 목록")

        # 선택된 운수사의 파일 목록 표시
        for ym, files in file_dict.items():
            # 해당 운수사 관련 파일만 필터링
            filtered_files = [f for f in files if selected_company in f]
            
            if filtered_files:
                st.write(f"#### 📂 {ym}")  # 연/월 폴더명 표시
                
                for file in filtered_files:
                    file_path = os.path.join(BASE_DIR, ym, file)

                    with open(file_path, "rb") as f:
                        file_data = f.read()

                    st.download_button(
                        label=f"📥 {file}",
                        data=file_data,
                        file_name=file,
                        mime="application/octet-stream"
                    )
    else:
        st.warning("🚫 올바른 비밀번호를 입력하세요.")