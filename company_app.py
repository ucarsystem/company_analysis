import streamlit as st
import os
import pandas as pd

# 기본 경로 설정 (실제 파일 경로로 변경 필요)
BASE_DIR = "path_to_files"  # 실제 운전성향분석표가 저장된 루트 폴더 경로로 변경
company_info_path = os.path.join(BASE_DIR, "company_info.xlsx")

# 엑셀에서 회사 목록 불러오기
if os.path.exists(company_info_path):
    df = pd.read_excel(company_info_path)
    company_list = df["운수사사"].tolist()  # 'Company' 컬럼이 회사명이라고 가정
else:
    company_list = []

# 회사 선택
selected_company = st.sidebar.selectbox("운수사 선택", company_list)

# 회사별 폴더 경로 설정
company_dir = os.path.join(BASE_DIR, selected_company)

# 해당 회사의 년/월 폴더 목록 가져오기
if os.path.exists(company_dir):
    year_month_folders = sorted(os.listdir(company_dir))
else:
    year_month_folders = []

# 년/월 폴더 선택
selected_folder = st.sidebar.selectbox("연/월 선택", year_month_folders)

# 선택된 폴더의 경로
folder_path = os.path.join(company_dir, selected_folder)

# 해당 폴더 내의 운전성향분석표 파일 목록 가져오기
if os.path.exists(folder_path):
    file_list = [f for f in os.listdir(folder_path) if f.endswith(".xlsx") or f.endswith(".csv")]
else:
    file_list = []

st.write(f"### {selected_company} - {selected_folder} 운전성향분석표 파일 목록")

# 파일 다운로드 버튼 생성
for file in file_list:
    file_path = os.path.join(folder_path, file)
    
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    st.download_button(
        label=f"📥 {file}",
        data=file_data,
        file_name=file,
        mime="application/octet-stream"
    )