import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import requests
import numpy as np
from PIL import Image, ImageOps
import matplotlib as mpl 
import matplotlib.pyplot as plt 
import matplotlib.font_manager as fm  
import matplotlib.ticker as ticker
from openpyxl import load_workbook
import calendar
import datetime
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import io
#페이지 설정 (가장 맨위에 호출시켜야함!)
st.set_page_config(page_title="운수사 관리자 페이지", layout="wide")

# 한글 폰트 설정
font_path = "./malgun.ttf"  # 또는 절대 경로로 설정 (예: C:/install/FINAL_APP/dashboard/malgun.ttf)
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

# =====================
# 파이스트로 버튼 hover 핸드와 css 설정
# =====================
st.markdown("""
    <style>
    .menu-btn {
        padding: 10px 20px;
        margin-bottom: 5px;
        border: 1px solid #d1d1d1;
        border-radius: 8px;
        background-color: #f5f5f5;
        font-weight: bold;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    .menu-btn:hover {
        background-color: #d0eaff;
        transform: scale(1.02);
        box-shadow: 0 0 5px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)


#메뉴 생성
menu_items = [
    ("1. 특별관리", "🔥"),
    ("2. 대시보드", "📊"),
    ("3. 운전성향분석표", "📁"),
    ("4. 집중관리명단", "⚠"),
    ("5. 인증현황", "🏊"),
    ("6. ID 조회", "🆔"),
    ("7. 차량정보확인", "🚐"),
    ("8. A/S 현황", "🚰"),
    ("9. 운전자등급", "⭐"),
    ("10. 개별분석표", "📌")
]
# 사이드바 메뉴
# st.sidebar.title("📋 메뉴")
# menu = st.sidebar.radio(
#     "이동할 항목을 선택하세요:",
#     [
#         "1. 특별관리",
#         "2. 대시보드",
#         "3. 운전성향분석표",
#         "4. 집중관리명단",
#         "5. 인증현황",
#         "6. ID 조회",
#         "7. 차량정보확인",
#         "8. A/S 현황",
#         "9. 운전자등급",
#         "10. 개별분석표"
#     ]
# )

if "current_page" not in st.session_state:
    st.session_state.current_page = menu_items[0][0]

# 왼쪽 메뉴: hover 효과와 버튼을 합치기
with st.sidebar:
    st.markdown("### 📋 메뉴 선택")
    for item, icon in menu_items:
        if st.button(f"{icon} {item[3:]}", use_container_width=True, key=item):
            st.session_state.current_page = item

# 운수사 선택
st.sidebar.title("🏢 운수사 선택")
selected_company = st.sidebar.selectbox("운수사를 선택하세요", 
                                        ["운수사를 선택해주세요", "강인교통", "강인여객", "강화교통", "강인여객", "공영급행", "대인교통", "도영운수", "동화운수", "마니교통", "은혜교통", "미래교통", "미추홀교통", "부성여객", "삼환교통", "삼환운수", "선진여객", "성산여객", "성원운수", "세운교통", "송도버스", "시영운수", "신동아교통", "신화여객", "신흥교통", "영종운수", "원진운수", "인천교통공사", "인천스마트", "인천제물포교통", "청라교통", "청룡교통", "태양여객", "해성운수"])  # 실제 값으로 변경 필요

if selected_company != "운수사를 선택해주세요":

    # 엑셀 파일 로딩 함수
    @st.cache_data
    def load_excel_data(file_path):
        xls = pd.ExcelFile(file_path)
        sheet_dict = {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}
        return sheet_dict

    # 엑셀 파일 경로 설정
    #전체 파일
    excel_file_path = "company_total.xlsx"  
    data_sheets = load_excel_data(excel_file_path) #시트명으로 들어가짐 ex. data_sheets['차량별']

    #연료절감대장(차량관리, as현황)
    carinfo_as_path = "car_info&as.xlsx"  
    carinfo_as_sheets = load_excel_data(carinfo_as_path)

    #구글시트 이용용
    # google_excel_url = "https://drive.google.com/uc?export=download&id=1QeM7mK92DkQWOXNHp6SSX66MZa8Enfrh"
    # @st.cache_data
    # def load_google_excel(url):
    #     xls = pd.ExcelFile(url)
    #     return {sheet: xls.parse(sheet) for sheet in xls.sheet_names}
    # data_sheets = load_google_excel(google_excel_url)

    # 함수
    @st.cache_data
    # 컬럼명 재설정
    def load_data(df):

        df = df.rename(columns={
            '주행거리(km)': '주행거리',
            '연료소모량(m3': '연료소모량',
            '웜업시간': '웜업시간',
            '공회전시간': '공회전시간',
            '주행시간': '주행시간',
            '탄력운전 거리(km)': '탄력운전거리',
            '평균속도': '평균속도',
            '급가속횟수': '급가속',
            '급감속횟수': '급감속',
            '속도필터': '속도필터'
        })
        return df

    # 속도필터 0인것만 계산, 어떤 데이터로 그룹을 묶는지 설정하는 함수
    def process_data(df, group_cols):
        df_speed0 = df[df['속도필터'] == 0]

        grouped = df.groupby(group_cols).agg({
            '주행거리': 'sum',
            '연료소모량': 'sum',
            '웜업시간': 'sum',
            '공회전시간': 'sum',
            '주행시간': 'sum',
            '탄력운전거리': 'sum',
            '평균속도': 'mean',
            '운수사달성율': 'sum'
        }).reset_index()

        aggr_speed0 = df_speed0.groupby(group_cols).agg({
            '급가속': 'sum',
            '급감속': 'sum',
            '주행거리': 'sum'
        }).rename(columns={'주행거리': '주행거리_속도0'}).reset_index()

        result = pd.merge(grouped, aggr_speed0, on=group_cols, how='left')

        result['달성율'] = result['운수사달성율']
        result['연비'] = result['주행거리'] / result['연료소모량']
        result['웜업률'] = result['웜업시간'] / result['주행시간']
        result['공회전율'] = result['공회전시간'] / result['주행시간']
        result['탄력운전비율'] = result['탄력운전거리'] / result['주행거리']
        result['급가속(회/100km)'] = result['급가속'] * 100 / result['주행거리_속도0']
        result['급감속(회/100km)'] = result['급감속'] * 100 / result['주행거리_속도0']

        # 년월 → 범주형 라벨 추가
        result['년월_label'] = result['년월'].astype(str).apply(lambda x: f"20{x[:2]}년 {int(x[2:])}월")

        return result

    # =====================
    # 각 항목 순위 UI 제출
    # =====================
    def get_color_by_rank(rank):
        if rank <= 5:
            return "#a8e6a2"  # 초록
        elif rank >= 26:
            return "#f58a8a"  # 빨간
        else:
            return "#cce5ff"  # 포장색


    # 페이지 타이틀
    st.title("🚍 운수사 관리자 페이지")
    menu = st.session_state.current_page

    # 각 메뉴별 페이지 처리
    if menu == "1. 특별관리":
        st.header("🔥 특별관리")
        # 예시: st.dataframe(data_sheets["차량별"])

    elif menu == "2. 대시보드":
        # st.set_page_config(page_title="운수사 관리자 분석", layout="wide")
        st.title(f"📊 {selected_company}의 전체 대시보드")

        # 데이터 병합 처리 (24년 + 25년)
        df_24 = load_data(data_sheets.get("차량별(24년)"))
        df_25 = load_data(data_sheets.get("차량별(25년)"))
        raw_df = pd.concat([df_24, df_25], ignore_index=True)
        
        #속도필터반영
        df_company = process_data(raw_df, ['년월', '운수사'])
        df_incheon = process_data(raw_df, ['년월'])

        # UI 선택 영역
        selected_month = st.selectbox("📅 년월 선택", sorted(df_company['년월'].unique()))
        selected_company = st.selectbox("🚍 운수사 선택", sorted(df_company['운수사'].unique()))

        # 항목별 정렬 기준 정의
        metric_info = {
            '달성율': False,
            '웜업률': True,
            '공회전율': True,
            '탄력운전비율': False,
            '평균속도': False,
            '급가속(회/100km)': True,
            '급감속(회/100km)': True
        }

        # 선택된 년월 데이터 필터링 후 순위 계산
        df_month = df_company[df_company['년월'] == selected_month].copy()
        for col, asc in metric_info.items():
            df_month[f"{col}_순위"] = df_month[col].rank(ascending=asc, method="min")

        # 선택 운수사 데이터 추출
        target = df_month[df_month['운수사'] == selected_company].iloc[0]

        # 결과 UI 출력
        st.markdown(f"### 🚩 {selected_month[:2]}년 {selected_month[2:]}월 - **{selected_company}** 항목별 순위")
        cols = st.columns(len(metric_info))
        for i, (metric, _) in enumerate(metric_info.items()):
            rank = int(target[f"{metric}_순위"])
            color = get_color_by_rank(rank)
            with cols[i]:
                st.markdown(f"""
                <div style='text-align:center; padding:10px; background:{color}; border-radius:50%; 
                            width:120px; height:120px; display:flex; flex-direction:column; 
                            justify-content:center; align-items:center; margin:auto;'>
                    <b style='font-size:24px;'>{rank}위</b>
                    <div style='font-size:12px;'>{metric}</div>
                </div>
                """, unsafe_allow_html=True)

        # =====================
        # 인천 전체 평균 추이 비교
        # =====================
        st.markdown("---")
        st.markdown(f"### 📈 {selected_company} vs 인천 전체 평균 (지표별 추이)")

        compare_metrics = ['웜업률', '공회전율', '급감속(회/100km)', '평균속도']
        df_target = df_company[df_company['운수사'] == selected_company][['년월_label'] + compare_metrics]
        df_incheon = df_incheon[['년월_label'] + compare_metrics]

        for metric in compare_metrics:
            y_unit = "%" if metric in ['웜업률', '공회전율'] else ""
            df_target[metric] = df_target[metric] * 100 if y_unit else df_target[metric]
            df_incheon[metric] = df_incheon[metric] * 100 if y_unit else df_incheon[metric]

            df_target[metric] = df_target[metric].round(2)
            df_incheon[metric] = df_incheon[metric].round(2)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_incheon['년월_label'], y=df_incheon[metric], mode='lines+markers', name='인천 평균'))
            fig.add_trace(go.Scatter(x=df_target['년월_label'], y=df_target[metric], mode='lines+markers', name=selected_company))
            fig.update_layout(title=f"📊 {metric} 추이", xaxis_title='년월', yaxis_title=metric + y_unit)
            st.plotly_chart(fig, use_container_width=True)

        
    elif menu == "3. 운전성향분석표":
        st.header("📑 운전성향분석표")
        # 예시: st.dataframe(data_sheets["운전자별"])

    elif menu == "4. 집중관리명단":
        st.header("⚠ 집중관리명단")
        # 예시: st.dataframe(data_sheets["집중관리명단"])

    elif menu == "5. 인증현황":
        st.header("🏆 인증현황")

        df_24_cert = data_sheets["5. 24년인증현황"]
        df_25 = data_sheets["운전자별(25년)"]

        # ✅ 2024년 인증자 명단
        st.subheader("⭐ 2024년 인증 대상자 명단 ⭐")
        df_24_filtered = df_24_cert[df_24_cert["운수사"] == selected_company]
        if not df_24_filtered.empty:
            st.dataframe(df_24_filtered[["운수사", "성명", "아이디"]], use_container_width=True)
        else:
            st.info("해당 운수사에서 2024년 인증 대상자가 없습니다.")

        # ✅ 2025년 인증 대상자 분석
        st.subheader("⭐ 2025년 분기별 인증 대상자 명단 ⭐")

        # 1. 년월 → 년/월/분기 분리
        df_25 = df_25[df_25["년월"].astype(str).str.len() == 4].copy()
        df_25["년"] = df_25["년월"].astype(str).str[:2].astype(int)
        df_25["월"] = df_25["년월"].astype(str).str[2:].astype(int)
        df_25["분기"] = df_25["월"].apply(lambda x: (x - 1) // 3 + 1)

        # 2. 2025년 & 해당 운수사만 필터링
        df_25 = df_25[(df_25["년"] == 25) & (df_25["운수사"] == selected_company)]

        # 3. 분기별 운전자 평균 가중달성율 계산
        grouped = df_25.groupby(["운전자ID", "운전자이름", "분기"])["가중달성율"].mean().reset_index()
        certified = grouped[grouped["가중달성율"] >= 95]

        # 4. 인증자 명단 출력
        if not certified.empty:
            for q in sorted(certified["분기"].unique()):
                st.markdown(f"#### 🏅 2025년 {q}분기 인증자")
                q_df = certified[certified["분기"] == q]
                st.dataframe(q_df[["운전자ID", "운전자이름", "가중달성율"]].round(2), use_container_width=True)
        else:
            st.info("해당 운수사에서 2025년 인증 대상자가 없습니다.")

        # ✅ 인증율 요약 (운전자이름이 NULL인 경우 제외)
        st.subheader("📊 인증 대상자 비율")

        df_named = df_25[df_25["운전자이름"].notnull()]
        driver_base = df_named.groupby(["운전자ID", "운전자이름", "분기"]).size().reset_index().rename(columns={0: "횟수"})

        certified_count = certified.groupby("분기").size().reset_index().rename(columns={0: "인증자수"})
        total_count = driver_base.groupby("분기").size().reset_index().rename(columns={0: "전체운전자수"})

        summary = pd.merge(total_count, certified_count, on="분기", how="left").fillna(0)
        summary["인증율(%)"] = (summary["인증자수"] / summary["전체운전자수"] * 100).round(1)

        st.dataframe(summary, use_container_width=True)

        # ✅ 인증자 명단 다운로드 (Excel) 다음에 시도해보기
        # st.subheader("⬇ 인증자 명단 다운로드")

        # output = io.BytesIO()
        # with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        #     for q in sorted(certified["분기"].unique()):
        #         q_df = certified[certified["분기"] == q][["운전자ID", "운전자이름", "가중달성율"]].copy()
        #         q_df.to_excel(writer, index=False, sheet_name=f"{q}분기인증자")
        #     writer.save()
        #     excel_data = output.getvalue()

        # st.download_button(
        #     label="📥 인증자 명단 Excel 다운로드",
        #     data=excel_data,
        #     file_name=f"{selected_company}_2025_인증자명단.xlsx",
        #     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        # )


    elif menu == "6. ID 조회":
        st.header("🆔 ID 조회")
        # 파일 로드
        # def load_data():
        #     file_path = "인천ID.xlsx"
        #     xls = pd.ExcelFile(file_path)
        #     df = pd.read_excel(xls, sheet_name='ID목록')
        #     return df
        
        id_file_path = "인천ID.xlsx"
        data_id = load_excel_data(id_file_path)

        df = data_id['ID목록']

        # '퇴사여부' 컬럼의 NaN 값을 빈 문자열로 변경
        df['퇴사여부'] = df['퇴사여부'].fillna('')

        # Streamlit UI 설정
        # st.title("👥운전자 명단 조회")

        # 선택된 운수사가 '운수사를 선택해주세요'가 아닐 때만 필터링 실행
        df_filtered = df[df['운수사'] == selected_company].reset_index(drop=True)  # 기존 인덱스 제거 후 재정렬
        df_filtered.insert(0, "번호", df_filtered.index + 1)  # 새로운 인덱스 추가 (1부터 시작)

        # 검색창 추가 (이름 & ID 검색 가능)
        search_query = st.markdown("**운전자 이름** 또는 **ID**를 입력하세요:")
        search_query = st.text_input("")

        st.subheader(f"{selected_company}의 운전자 명단")

        if search_query:
            df_filtered = df_filtered[
                df_filtered['운전자이름'].str.contains(search_query, na=False, case=False) |
                df_filtered['운전자ID'].astype(str).str.contains(search_query, na=False, case=False)
            ].reset_index(drop=True)  # 검색 후에도 인덱스 다시 설정
            #df_filtered.insert(0, "번호", df_filtered.index + 1)  # 번호 다시 설정

        # 결과 출력 (기본 인덱스 숨기기)
        st.dataframe(df_filtered, hide_index=True)

        # 예시: st.dataframe(data_sheets["ID"])

    elif menu == "7. 차량정보확인":
        st.header("🚐 차량정보확인")

        df_vehicle = carinfo_as_sheets['7. 차량정보확인']

        if df_vehicle is not None:
            df_filtered = df_vehicle[df_vehicle['운수사'] == selected_company].reset_index(drop=True)

            #순번 새로 부여
            df_filtered.insert(0, "순번", df_filtered.index + 1)

            # 날짜형 컬럼 정리: 시간 제거, None은 빈 문자열 처리
            date_cols = ['운행개시일', '운행종료일', '최초등록일', '수신일', '처리일']
            for col in date_cols:
                if col in df_filtered.columns:
                    df_filtered[col] = df_filtered[col].fillna("").astype(str).str[:10].replace(["NaT", "nan", "None"], "")

            # None 값을 빈 문자열로 처리
            df_filtered = df_filtered.fillna("")

            df_display = df_filtered[[col for col in df_filtered.columns]]

            # 스타일 지정 (가독성 + 특정 컬럼 강조)
            st.markdown("""
                <style>
                .stDataFrame thead tr th {
                    background-color: #f0f0f0;
                    font-weight: bold;
                    text-align: center;
                }
                .stDataFrame td {
                    text-align: center;
                    font-size: 13px;
                }
                .stDataFrame tbody tr:hover {
                    background-color: #e6f2ff;
                }
                </style>
            """, unsafe_allow_html=True)

            # 강조 컬럼 배경색 지정 함수
            def highlight_yellow(s):
                return ['background-color: #fff8b3' if s.name in ['처리여부', '수신일', '처리일', '적용사항'] else [''] * len(s)][0]

            styled_df = df_display.style.apply(highlight_yellow, axis=0).hide(axis="index")

            st.dataframe(styled_df, use_container_width=True, height=len(df_display) * 35 + 60, hide_index=True)

        else:
            st.warning("📂 '차량정보 변동사항이 없습니다.' ")

    elif menu == "8. A/S 현황":
        st.header("🛠 A/S 현황")

        df_as = carinfo_as_sheets['8. AS현황']

        if df_as is not None:
            df_filtered = df_as[df_as['운수사'] == selected_company].copy()

            #순번 새로 부여
            df_filtered.insert(0, "순번", range(1, len(df_filtered) + 1))

            # 날짜형 컬럼 정리: 시간 제거, None은 빈 문자열 처리
            date_cols = ['접수일자', '발생일시', '처리일']
            for col in date_cols:
                if col in df_filtered.columns:
                    df_filtered[col] = df_filtered[col].fillna("").astype(str).str[:10].replace(["NaT", "nan", "None"], "")

            # None 값을 빈 문자열로 처리
            df_filtered = df_filtered.fillna("")

            print_columns = ['순번', '운수사', '접수일자', '노선', '차량번호', '운행사원', '발생일시', '증상', '비고', '처리여부', '처리일', '적용사항']

            df_display = df_filtered[[col for col in print_columns]]

            # 스타일 지정 (가독성 + 특정 컬럼 강조)
            st.markdown("""
                <style>
                .stDataFrame thead tr th {
                    background-color: #f0f0f0;
                    font-weight: bold;
                    text-align: center;
                }
                .stDataFrame td {
                    text-align: center;
                    font-size: 13px;
                }
                .stDataFrame tbody tr:hover {
                    background-color: #e6f2ff;
                }
                </style>
            """, unsafe_allow_html=True)

            # 강조 컬럼 배경색 지정 함수
            def highlight_yellow(s):
                return ['background-color: #fff8b3' if s.name in ['처리여부', '처리일', '적용사항'] else [''] * len(s)][0]

            styled_df = df_display.style.apply(highlight_yellow, axis=0).hide(axis="index")

            st.dataframe(styled_df, use_container_width=True, height=len(df_display) * 35 + 60, hide_index=True)

        else:
            st.warning("📂 'AS접수사항이 없습니다.' ")

    elif menu == "9. 운전자등급":
        st.header(f"🏁 {selected_company} 운전자등급")

        # 📅 년/월 선택
        year = st.selectbox("년도 선택", ["2024", "2025"])
        month = st.selectbox("월 선택", [f"{i:02d}" for i in range(1, 13)])
        ym = int(year[2:] + month)

        #등급별 색깔 함수
        # 차트용
        def color_by_grade(val):
            color_map = {
                "S": "#00B050", "A": "#00B050",  # 초록
                "B": "#0070C0", "C": "#0070C0",  # 파랑
                "D": "#FF0000", "F": "#FF0000",  # 빨강
            }
            color = color_map.get(val, "")
            return f"background-color: {color}; color: white"
        # 텍스트용
        def get_grade_color(val):
            color_map = {
                "S": "#00B050", "A": "#00B050",
                "B": "#0070C0", "C": "#0070C0",
                "D": "#FF0000", "F": "#FF0000",
            }
            return color_map.get(val, "#000")

        #시트 선택
        sheet_name = f"운전자별({year[2:]}년)"

        df_person = data_sheets[sheet_name]

        if df_person is not None:

            df_person = df_person.copy()
            df_person = df_person[(df_person["년월"]==ym) & (df_person["운수사"] == selected_company)]

            if not df_person.empty:

                #등급설명 추가
                grade_desc = {"S":"최우수", "A": "우수", "B": "양호", "C": "보통", "D": "주의", "F": "경고"}
                df_person['등급설명'] = df_person['등급'].map(grade_desc)

                # 유효한 운전자 필터링 (이름 null, ID 0, 9999 제외)
                df_nonull = df_person[
                    df_person["운전자이름"].notnull() &
                    ~df_person["운전자ID"].isin([0, 9999])
                ]
                
                # ✅ 평균등급 계산
                grade_to_score = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
                score_to_grade = {v: k for k, v in grade_to_score.items()}
                avg_score = df_nonull["등급"].map(grade_to_score).mean()
                rounded = int(round(avg_score))
                avg_grade = score_to_grade.get(rounded, "N/A")
                color = get_grade_color(avg_grade)

                # ✅ 평균등급 강조 출력
                st.markdown(f"""
                <div style="font-size:28px; font-weight:bold;">
                <span style="color: #444;">{year}년 {int(month)}월 평균등급 :</span>
                <span style="color:{color};"> {avg_grade} 등급</span>
                </div>
                """, unsafe_allow_html=True)

                # 1. 등급 비중 시각화
                st.subheader("📊 등급별 비중")

                # 등급별 비중
                grade_order = ["S", "A", "B", "C", "D", "F"]
                grade_counts = df_nonull["등급"].value_counts().reindex(grade_order, fill_value=0).reset_index()
                grade_counts.columns = ["등급", "인원수"]
                # 차트 색상
                pie_colors  = {
                    "S": "#006400",  # 진초록
                    "A": "#00B050",  # 초록
                    "B": "#003399",  # 진파랑
                    "C": "#0070C0",  # 파랑
                    "D": "#B22222",  # 진빨강
                    "F": "#FF0000",  # 빨강
                }
                # grade_counts = Counter(df_nonull["등급"])
                # labels = ["S", "A", "B", "C", "D", "F"]
                # values = [grade_counts.get(g, 0) for g in labels]
                # colors = ["#00B050", "#00B050", "#0070C0", "#0070C0", "#FF0000", "#FF0000"]

                # fig = go.Figure(data=[go.Pie(
                #     labels=labels,
                #     values=values,
                #     hole=0.4,
                #     marker=dict(colors=colors),
                #     textinfo='label+percent',
                #     textfont=dict(size=18),
                # )])
                # fig.update_layout(title=f"{year}년 {int(month)}월 운전자 등급 비중", legend_title="등급")
                # st.plotly_chart(fig, use_container_width=True)
                # grade_counts = df_nonull["등급"].value_counts().reset_index()
                # grade_counts.columns = ["등급", "인원수"]

                fig = go.Figure(data=[go.Pie(
                    labels=grade_counts["등급"],
                    values=grade_counts["인원수"],
                    hole=0.4,
                    marker=dict(colors=[pie_colors[g] for g in grade_counts["등급"]]),
                    textinfo='label+percent',
                    textfont=dict(size=18),
                    sort=False  # 등급 순서 고정
                )])
                fig.update_layout(title=f"{year}년 {int(month)}월 운전자 등급 비중", legend_title="등급")
                st.plotly_chart(fig, use_container_width=True)

                # 3. 운수사별 명단 테이블
                st.subheader("🧾 등급별 명단")
                selected_cols = ["운수사", "노선번호", "운전자이름", "운전자ID", "가중달성율", "등급", "등급설명", "차량번호4", "주행거리(km)"]
                df_display = df_nonull[selected_cols].fillna("")
                df_display = df_display.sort_values(by="가중달성율", ascending=False)

                df_display = df_display.rename(columns={
                    '주행거리(km)': '주행거리',
                    '노선번호' : '노선',
                    '운전자이름' : '사원명',
                    '가중달성율' : '목표달성율',
                    '차량번호4' : '주운행차량'
                })

                # 목표달성율 퍼센트 표시+정렬용 숫자 컬럼

                # ✅ 목표달성율 퍼센트 표시
                df_display["목표달성율_정렬값"] =  df_nonull["가중달성율"]
                df_display = df_display.sort_values(by="목표달성율_정렬값", ascending=False).drop(columns=["목표달성율_정렬값"])

                # 목표달성율 % 형식
                df_display["목표달성율"] = df_display["목표달성율"].astype(float).apply(
                    lambda x: f"{round(x * 100)}%" if str(x).replace('.', '', 1).isdigit() else x
                )

                # ✅ 주행거리 천단위 쉼표
                df_display["주행거리"] = df_display["주행거리"].apply(
                    lambda x: f"{int(float(x)):,}" if str(x).replace('.', '', 1).isdigit() else x
                )

                # 순번 추가
                df_display.insert(0, "순번", range(1, len(df_display) + 1))

                #출력
                st.caption(f"총 {len(df_display)}명")
                st.dataframe(
                    df_display.style.applymap(color_by_grade, subset=["등급"]),
                    use_container_width=True,
                    height=len(df_display) * 35 + 60,
                    hide_index=True
                )
            else:
               st.markdown(f"❗ '{selected_company}' {year}년 {month}의 자료가 없습니다.") 
            
        else:
            st.markdown(f"❗ '{selected_company}' 의 자료가 없습니다.")



        # 예시: st.dataframe(data_sheets["운전자별"])

    elif menu == "10. 개별분석표":
        st.header("📌 개별분석표")

        # 기본 경로 설정
        file_dir = "./file"
        file_url_template = "https://github.com/ucarsystem/company_analysis/file/인천%20개인별%20대시보드_{year}년{month}월.xlsx"

        # 엑셀 파일 로드 함수
        def load_excel(path, sheetname):
            try:
                return pd.read_excel(path, sheet_name=sheetname)
            except Exception as e:
                st.error(f"엑셀 파일 로드 오류: {e}")
                return None
            
        # 📂 운수사 목록 불러오기
        company_file = os.path.join(file_dir, "company_info.xlsx")
        df_company = pd.read_excel(company_file, sheet_name="Sheet1", header=None) if os.path.exists(company_file) else pd.DataFrame()
        company_list = df_company[0].dropna().tolist() if not df_company.empty else []
        df_code = pd.read_excel(company_file, sheet_name="code") if os.path.exists(company_file) else pd.DataFrame()


        # Streamlit UI 구성🚍
        company_input = selected_company

        user_id_input = st.text_input("운전자 ID를 입력하세요")
        st.markdown("""
            <a href='https://driverid-xgkps9rbvh4iph8yrcvovb.streamlit.app/' target='_blank' 
            style='display: inline-block; padding: 10px 20px; background-color: green; color: white; font-weight: bold; 
            text-align: center; text-decoration: none; border-radius: 5px;'>내 ID를 모른다면? >> ID 조회하기</a>
        """, unsafe_allow_html=True)
        user_name_input = st.text_input("운전자 이름을 입력하세요")

        year_input = st.text_input("년도를 입력하세요 (예: 25)")
        month_input = st.text_input("월을 입력하세요 (예: 02)").zfill(2)
        input_yyyymm = f"{year_input}{month_input}"

        if st.button("조회하기") and company_input and user_id_input and user_name_input and year_input and month_input:
            file_name = f"인천 개인별 대시보드_{year_input}년{month_input}월.xlsx"
            file_path = os.path.join(file_dir, file_name)

            df = load_excel(file_path, "매크로(운전자리스트)")
            df_vehicle = load_excel(file_path, "차량+운전자별")
            df_monthly = load_excel(file_path, "운전자별")
            df_daily = load_excel(file_path, "일별)차량+운전자")
            df_cert_24 = load_excel(file_path, "24년 명단")
            df_cert_25 = load_excel(file_path, "25년 후보자")

            # 조건 필터링
            filtered = df[
                (df["운수사"] == company_input) &
                (df["운전자이름"] == user_name_input) &
                (df["운전자ID"].astype(str) == user_id_input)
            ]

            #등급함수
            def calc_grade(score):
                score *= 100
                if score >= 100: return "S"
                elif score >= 95: return "A"
                elif score >= 90: return "B"
                elif score >= 85: return "C"
                elif score >= 80: return "D"
                elif score >= 65: return "F"
                else: return ""

            if not filtered.empty:
                row = filtered.iloc[0]
                st.success(f"✅ 운전자 {user_name_input} (ID: {user_id_input}) 정보 조회 성공")

                st.markdown("---")

                #값 정의
                #이번달
                this_grade = row[input_yyyymm] #등급
                this_percent = row['이번달달성율']
                this_warm = row['이번달웜업비율(%)']
                this_idle = row["이번달공회전비율(%)"] 
                this_break = row['이번달급감속(회)/100km']
                this_line = row['주운행노선']
                this_bus = row['주운행차량']

                #전월
                last_grade = row['전월등급']
                last_percent = row['전월달성율']
                last_warm = row['전월웜업비율(%)']
                last_idle = row["전월공회전비율(%)"] 
                last_break = row['전월급감속(회)/100km']

                #노선평균
                ave_grade = row['노선평균등급']
                ave_percent = row['노선평균달성율']
                ave_warm = row['노선평균웜업비율(%)']
                ave_idle = row["노선평균공회전비율(%)"] 
                ave_break = row['노선평균급감속(회)/100km']

                #다음달
                next_month = 1 if int(month_input) == 12 else int(month_input)+1 


                grade_color = {"S": "🟩", "A": "🟩", "B": "🟨", "C": "🟨", "D": "🟥", "F": "🟥"}
                grade_target = "C" if this_grade in ["F", "D"] else "B" if this_grade == "C" else "A" if this_grade == "B" else "S"
                grade_text_color = "green" if this_grade in ["S", "A"] else "orange" if this_grade in ["B", "C"] else "red"

                # 🚌 이번달 핵심 성과 요약
                summary_msg = ""
                if this_grade in ["S", "A"]:
                    summary_msg = f"🎉 {int(month_input)}월 <b>{this_grade}</b>등급 달성! 안정적인 운전 감사합니다."
                elif this_break < 5:
                    summary_msg = f"✅ {int(month_input)}월 급감속 <b>{this_break:.1f}</b>회! <b>{grade_target}등급</b>까지 도전해보세요!"
                elif this_idle > ave_idle:
                    summary_msg = f"⚠️ 공회전율이 다소 높습니다. 시동 관리를 통해 <b>{grade_target}등급</b> 도전해보세요!"
                else:
                    summary_msg = f"📌 {int(month_input)}월 <b>{this_grade}</b>등급! 조금만 더 노력하면 <b>{grade_target}</b>도 가능합니다."

                st.markdown(f"""
                <div style='
                    background-color: #f9f9f9; 
                    padding: 12px; 
                    margin-bottom: 20px; 
                    border-left: 6px solid #FFA500; 
                    font-size: 18px;
                    font-weight: bold;
                '>
                {summary_msg}
                </div>
                """, unsafe_allow_html=True)

                # ✅ 2. 기존 요약 (대표 차량, 노선, 등급, 주요 지표)
                st.markdown(f"""
                <div style='display: flex; align-items: center;'>
                    <img src='https://img.icons8.com/color/48/bus.png' style='margin-right: 10px;'>
                    <div>
                        <div><strong>대표 차량:</strong> {this_bus}</div>
                        <div><strong>노선:</strong> {this_line}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)
                col1.markdown(f"<div style='font-size: 20px; font-weight: bold;'>{int(month_input)}월 등급</div><div style='font-size: 28px; font-weight: bold; color: {grade_text_color};'>{grade_color.get(this_grade, '')} {this_grade}</div>", unsafe_allow_html=True)
                col2.metric("달성률", f"{round(row['이번달달성율'] * 100)}%")
                col3.metric("공회전", f"{round(this_idle * 100)}%")
                col4.metric("급감속", f"{round(this_break, 2)}")

                # 순위표시

                # [운전자별] 시트에서 순위 계산
                df_incheon = df_monthly[(df_monthly['년월'] == int(input_yyyymm))&
                                    (df_monthly['운전자이름'].notnull())
                ].copy()

                # 인천 전체 순위
                df_incheon = df_incheon.sort_values(by="가중달성율", ascending=False).reset_index(drop=True)
                incheon_rank = df_incheon[(df_incheon['운전자ID'].astype(str) == user_id_input) & (df_incheon['운수사'] == company_input)].index[0] + 1
                incheon_total = len(df_incheon)
                incheon_percent = incheon_rank / incheon_total * 100

                df_company_driver = df_monthly[
                    (df_monthly['년월'] == int(input_yyyymm)) &
                    (df_monthly['운수사'] == company_input) &
                    (df_monthly['운전자이름'].notnull())
                ].sort_values(by="가중달성율", ascending=False).reset_index(drop=True)
                # 운수사 내부 순위
                company_driver_match = df_company_driver[df_company_driver['운전자ID'].astype(str) == user_id_input]
                if not company_driver_match.empty:
                    company_rank = company_driver_match.index[0] + 1
                    company_total = len(df_company_driver)
                    company_percent = company_rank / company_total * 100
                else:
                    company_rank = "-"
                    company_total = len(df_company_driver)
                    company_percent = 0.0  # 또는 표시하지 않도록 설정

                # 표시(순위)
                st.markdown(f"""
                <div style='background-color: #f9f9f9; padding: 15px; border-radius: 8px; line-height: 1.8;'>

                <p style='font-size: 18px; margin: 5px 0;'>
                    <strong>🚩 인천시 전체 순위</strong>: 
                    <span style='font-size: 20px; font-weight: bold; color: orange;'>{incheon_rank}등</span> / 총 {incheon_total}명 → 
                    <span style='font-size: 20px; font-weight: bold; color: orange;'>상위 {incheon_percent:.1f}%</span>
                </p>

                <p style='font-size: 18px; margin: 5px 0;'>
                    <strong>🧑‍💼 {company_input} 내 순위</strong>: 
                    <span style='font-size: 20px; font-weight: bold; color: orange;'>{company_rank}등</span> / 총 {company_total}명 → 
                    <span style='font-size: 20px; font-weight: bold; color: orange;'>상위 {company_percent:.1f}%</span>
                </p>

                </div>
                """, unsafe_allow_html=True)

                # 2. 인증 현황🏅
                st.markdown("---")
                st.subheader("🏆나의 인증 현황")


                st.markdown(f"<div style='background-color: rgba(211, 211, 211, 0.3); padding: 10px; border-radius: 5px; margin-bottom: 20px;'> 4분기 모두 우수인증자 수여 시 그랜드슬림 달성!", unsafe_allow_html=True)

                from calendar import month_abbr
                df_cert_25_summary = df_monthly[
                    (df_monthly['운수사'] == company_input) &
                    (df_monthly['운전자ID'].astype(str) == user_id_input) &
                    (df_monthly['운전자이름'] == user_name_input)&
                    (df_monthly['년월'].astype(str).str.startswith("25"))
                ]

                medal_url = "https://raw.githubusercontent.com/ucarsystem/company_analysis/main/medal.png"
                medal_black_url = "https://raw.githubusercontent.com/ucarsystem/company_analysis/main/medal_black.png"

                # 분기/월 전처리
                df_cert_25_summary['년'] = df_cert_25_summary['년월'].astype(str).str[:2].astype(int)
                df_cert_25_summary['월'] = df_cert_25_summary['년월'].astype(str).str[2:].astype(int)
                df_cert_25_summary['분기'] = df_cert_25_summary['월'].apply(lambda m: (m - 1) // 3 + 1)

                # 분기별 평균: 각 분기에 해당하는 월의 평균
                quarter_avg = (
                    df_cert_25_summary
                    .groupby(['년', '분기'])
                    .agg({'가중달성율': 'mean'})
                    .reset_index()
                )

                quarter_avg['등급'] = quarter_avg['가중달성율'].apply(calc_grade)

                grouped_month = df_cert_25_summary[['년', '월', '등급']].copy()
                grouped_month = grouped_month.rename(columns={'등급': '월별등급'})

                # 24년 인증 확인
                is_cert_24 = not df_cert_24[
                    (df_cert_24['운수사'] == company_input) &
                    (df_cert_24['성명'] == user_name_input) &
                    (df_cert_24['아이디'].astype(str) == user_id_input)
                ].empty

                if is_cert_24:
                    medal_24 = (
                        "<div style='width: 180px; height: 180px; text-align: center; border: 2px solid #888; border-radius: 10px; padding: 10px; margin-bottom: 30px;'>"
                        "<div style='font-size: 15px; font-weight: bold;'>24년 전체</div>"
                        f"<img src='{medal_url}' width='100'>"
                        f"<div style='font-weight:bold; font-size: 15px; background: linear-gradient(to right, #FFD700, #FFA500); -webkit-background-clip: text; -webkit-text-fill-color: transparent;display: inline-block;'>🏅 우수운전자 🏅</div>"
                        "</div>"
                    )
                else:
                    medal_24 = (
                        "<div style='width: 180px; height: 180px; text-align: center; border: 2px solid #888; border-radius: 10px; padding: 10px; margin-bottom: 30px;'>"
                        "<div style='font-size: 15px; font-weight: bold;'>24년 전체</div>"
                        f"<img src='{medal_black_url}' width='100'>"
                        f"<div style='font-weight:bold; font-size: 13px; display: inline-block;'>다음 기회를 도전해보세요!</div>"
                        "</div>"

                    )
                st.markdown(medal_24, unsafe_allow_html=True)

                cert_grid = "<div style='display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start;'>"

                # 현재 날짜 기준으로 현재 연도/월 확인
                now = datetime.datetime.now()
                current_year = int(str(now.year)[-2:])  # 25
                current_month = now.month
                current_quarter = (current_month - 1) // 3 + 1

                for q_idx, q_row in quarter_avg.iterrows():
                    year, quarter, avg_score, grade = q_row['년'], int(q_row['분기']), q_row['가중달성율'], q_row['등급']
                    quarter_title = f"{year}년 {quarter}분기"

                    months_in_quarter = grouped_month[
                        (grouped_month['년'] == year) & 
                        (grouped_month['월'].between((quarter - 1) * 3 + 1, quarter * 3))
                    ]

                    if year < current_year or (year == current_year and quarter < current_quarter):
                        if avg_score >= 0.95:
                            medal = (
                                f"<img src='{medal_url}' width='100'>"
                                f"<div style='font-weight:bold; font-size: 15px; background: linear-gradient(to right, #FFD700, #FFA500); -webkit-background-clip: text; -webkit-text-fill-color: transparent;display: inline-block;'>✨ 우수운전자 ✨</div>"
                            )
                        else:
                            medal = (
                                f"<img src='{medal_black_url}' width='100'>"
                                f"<div style='font-weight:bold;'>{grade}({avg_score*100:.0f}%)</div>"
                            )
                    else:
                        medal = (
                            f"<img src='{medal_black_url}' width='100'>"
                            f"<div style='font-size: 13px;'>진행중...({avg_score*100:.0f}%)</div>"
                        )

                    # 월별 박스를 가로 배치하기 위한 container 추가
                    month_boxes = "".join([
                        "<div style='margin: 15px; text-align: center; display: inline-block;'>"
                        f"<div style='font-size: 16px; font-weight: bold;'>{m_row['월']}월</div>"
                        f"<div style='font-size: 24px;'>{'🥇' if m_row['월별등급'] in ['S', 'A'] else m_row['월별등급']}</div>"
                        "</div>"
                        for _, m_row in months_in_quarter.iterrows()
                    ])

                    cert_grid += (
                        "<div style='width: 200px; text-align: center; border: 1px solid #ccc; border-radius: 10px; padding: 10px;'>"
                        f"<div style='font-size: 15px; font-weight: bold;'>{quarter_title}</div>"
                        f"{medal}"
                        f"<div style='margin-top: 15px; display: flex; justify-content: center;'>{month_boxes}</div>"
                        "</div>"
                    )

                cert_grid += "</div>"
                st.markdown(cert_grid, unsafe_allow_html=True)

                # 3. 📅 일별 달성률 및 등급 표시
                st.markdown("---")
                st.subheader("📅 일별 등급 스탬프")
                df_daily_filtered = df_daily[
                    (df_daily['운수사'] == company_input) &
                    (df_daily['운전자ID'].astype(str) == user_id_input) &
                    (df_daily['운전자이름'] == user_name_input)
                ]
                if not df_daily_filtered.empty:
                    grouped = df_daily_filtered.groupby('DATE')['가중평균달성율'].sum().reset_index()

                    grouped['달성률값'] = (grouped['가중평균달성율'] * 100).round(0)
                    grouped['등급'] = grouped['가중평균달성율'].apply(calc_grade)
                    grouped['날짜'] = pd.to_datetime(grouped['DATE'])


                    # 📅 달력형 등급 표시
                    import calendar
                    year = grouped['날짜'].dt.year.iloc[0]
                    month = grouped['날짜'].dt.month.iloc[0]
                    grade_map = grouped.set_index(grouped['날짜'].dt.day)['등급'].to_dict()
                    cal = calendar.Calendar()
                    month_days = cal.monthdayscalendar(year, month)

                    calendar_rows = []
                    for week in month_days:
                        low = []
                        for i, day in enumerate(week):
                            if day == 0:
                                low.append("<td style='height: 80px;'></td>")
                            else:
                                grade = grade_map.get(day, "")
                                if grade in ["S", "A"]:
                                    emoji = "<div style='font-size: 30px;'>🎖️</div>"
                                    label = ""
                                elif grade in ["B", "C"]:
                                    emoji = f"<div style='color: orange; font-size: 30px; font-weight: bold;'>{grade}</div>"
                                elif grade in ["D", "F"]:
                                    emoji = f"<div style='color: red; font-size: 30px; font-weight: bold;'>{grade}</div>"
                                else:
                                    emoji = f"<span style='font-weight: bold; font-size: 20px;'>"  "</span>"
                                color = "red" if i == 0 else "black"
                                low.append(f"""
                                    <td style='padding: 8px; border: 1px solid #ccc; color: {color}; height: 80px;'>
                                        <div style='font-size: 16px; font-weight: bold;'>{day}</div>
                                        {emoji}
                                    </td>""")
                        calendar_rows.append("<tr>" + "".join(low) + "</tr>")

                    html = """
                    <table style='border-collapse: collapse; margin: auto; background-color: #fff;'>
                    <tr style='background-color: #f2f2f2;'>
                        <th style='color: red; width: 80px;'>일</th><th style='width: 80px;'>월</th><th style='width: 80px;'>화</th><th style='width: 80px;'>수</th><th style='width: 80px;'>목</th><th style='width: 80px;'>금</th><th style='width: 80px;'>토</th>
                    </tr>
                    """ + "".join(calendar_rows) + "</table>"
                    # <table style='border-collapse: collapse; width: 100%; text-align: center; background-color: #f0f5ef;'>
                    # <tr style='background-color: #e0e0e0;'>
                    #     <th style='color: red;'>일</th><th>월</th><th>화</th><th>수</th><th>목</th><th>금</th><th>토</th>
                    # </tr>
                    # """ + "".join(calendar_rows) + "</table>"

                    st.markdown(html, unsafe_allow_html=True)


                # 4. 운전습관 지표 비교
                st.markdown("---")
                st.subheader("🚦 운전 습관 핵심 지표 비교 🚦")
                compare_df = pd.DataFrame({
                    "지표": ["달성률(%)", "웜업률(%)", "공회전률(%)", "급감속(회/100km)"],
                    "이달": [
                        f"{round(this_percent * 100)}%",
                        f"{round(this_warm * 100, 1)}%",
                        f"{round(this_idle * 100, 1)}%",
                        f"{round(this_break, 2)}"
                    ],
                    "전월": [
                        f"{round(last_percent * 100)}%",
                        f"{round(last_warm * 100, 1)}%",
                        f"{round(last_idle * 100, 1)}%",
                        f"{round(last_break, 2)}"
                    ],  # 예시값
                    "노선 평균": [
                        f"{round(ave_percent * 100)}%",
                        f"{round(ave_warm * 100, 1)}%",
                        f"{round(ave_idle * 100, 1)}%",
                        f"{round(ave_break, 2)}"
                    ],  # 예시값
                })

                st.write("""
                <style>
                td span {
                    font-size: 13px;
                }
                table td {
                    white-space: nowrap !important;
                    text-align: center;
                    vertical-align: middle;
                }
                </style>
                """, unsafe_allow_html=True)
                st.write(compare_df.to_html(escape=False, index=False), unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("📊 이달 vs 노선 평균 그래프")
                labels = [
                    "웜업률(%)", "공회전률(%)", "탄력운전률(%)",
                    "연료소모율", "급가속(/100km)", "급감속(/100km)"
                ]
                driver_vals = [
                    this_warm * 100,
                    this_idle * 100,
                    row["이번달탄력운전비율(%)"] * 100,
                    row["이번달평균연료소모율"],
                    row["이번달급가속(회)/100km"],
                    this_break
                ]
                avg_vals = [
                    ave_warm * 100,
                    ave_idle * 100,
                    row["노선평균탄력운전비율(%)"] * 100,
                    row["노선평균평균연료소모율"],
                    row["노선평균급가속(회)/100km"],
                    ave_break
                ]

                # 조건에 따른 색상 정의
                def get_color(i, d, a):
                    good_if_higher = (i == 2)  # 탄력운전률만 높을수록 좋음
                    if (good_if_higher and d >= a) or (not good_if_higher and d <= a):
                        return '#C8E6C9'  # 연한 녹색
                    else:
                        return '#2E7D32'  # 진한 녹색 (기준보다 나쁠 때)

                colors = [get_color(i, d, a) for i, (d, a) in enumerate(zip(driver_vals, avg_vals))]

                fig, ax = plt.subplots(figsize=(9, 5))
                x = range(len(labels))
                bar_width = 0.4

                bars1 = ax.barh(x, driver_vals, height=bar_width, label='운전자', align='center', color=colors)
                bars2 = ax.barh([i + bar_width for i in x], avg_vals, height=bar_width, label='노선 평균', align='center', color='#FFE08C')

                # 값 표시
                for i, (d, a) in enumerate(zip(driver_vals, avg_vals)):
                    ax.text(d + 0.8, i, f"{d:.1f}", va='center', fontsize=10, fontweight='bold', color='black')
                    ax.text(a + 0.8, i + bar_width, f"{a:.1f}", va='center', fontsize=10, fontweight='bold', color='black')

                # 라벨 및 제목 스타일 조정
                ax.set_yticks([i + bar_width / 2 for i in x])
                ax.set_yticklabels(labels, fontproperties=font_prop, fontsize=11)
                ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
                ax.invert_yaxis()
                ax.legend(prop=font_prop)
                ax.set_title("이달 수치 vs 노선 평균 비교", fontsize=15, fontweight='bold', fontproperties=font_prop)
                ax.set_axisbelow(True)
                ax.grid(True, axis='x', linestyle='--', alpha=0.4)

                st.pyplot(fig)

                # 5. 전월대비 변화
                st.markdown("---")
                st.subheader("📈 전월 대비 개선 여부")
                def get_prev_yyyymm(yyyymm):
                    y, m = int(yyyymm[:2]), int(yyyymm[2:])
                    if m == 1:
                        return f"{y - 1 if y > 0 else 99}12"
                    else:
                        return f"{y:02d}{m - 1:02d}"
                    
                prev_yyyymm = get_prev_yyyymm(input_yyyymm)
                df_prev = df_monthly[
                    (df_monthly['운수사'] == company_input) &
                    (df_monthly['운전자ID'].astype(str) == user_id_input) &
                    (df_monthly['운전자이름'] == user_name_input)
                ]

                prev_row = df_prev[df_prev['년월'] == int(prev_yyyymm)]
                curr_row = df_prev[df_prev['년월'] == int(input_yyyymm)]

                if not prev_row.empty and not curr_row.empty:
                    prev = prev_row.iloc[0]
                    curr = curr_row.iloc[0]
                    compare = pd.DataFrame({
                        "지표": ["달성률(%)", "웜업률(%)", "공회전률(%)", "탄력운전비율(%)", "급감속"],
                        "전월": [
                            round(last_percent * 100, 0),
                            round(last_warm* 100, 2),
                            round(last_idle * 100, 2),
                            round(row['전월탄력운전비율(%)'] * 100, 2),
                            round(last_break, 2)
                        ],
                        "이달": [
                            round(this_percent* 100, 0),
                            round(this_warm * 100, 2),
                            round(this_idle* 100, 2),
                            round(row['이번달탄력운전비율(%)'] * 100, 2),
                            round(this_break, 2)
                        ]
                    })

                    #변화 계산 및 방향 아이콘 추가
                    def trend_icon(idx, diff):
                        if idx in [0, 3]:  # 달성률, 탄력운전률: 높을수록 좋음
                            if diff > 0:
                                return f"<span style='color: green;'>🟢 +{diff:.2f} 개선</span>"
                            elif diff < 0:
                                return f"<span style='color: red;'>🔴 -{abs(diff):.2f} 악화</span>"
                        else: #웜업률, 공회전률, 급감속: 낮을수록 좋음
                            if diff < 0:
                                return f"<span style='color: green;'>🟢 +{abs(diff):.2f} 개선</span>"
                            elif diff > 0:
                                return f"<span style='color: red;'>🔴 -{diff:.2f} 악화</span>"
                        return "-"

                    compare['변화'] = [trend_icon(i, compare['이달'][i] - compare['전월'][i]) for i in range(len(compare))]
                    st.write("""
                    <style>
                    td span {
                        font-size: 13px;
                    }
                    table td {
                        white-space: nowrap !important;
                        text-align: center;
                        vertical-align: middle;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    st.write(compare.to_html(escape=False, index=False), unsafe_allow_html=True)

                st.markdown("---")

                # 6.차량별요약      
                st.subheader("🚘 차량별 요약")
                df_vehicle_filtered = df_vehicle[
                    (df_vehicle['운수사'] == company_input) &
                    (df_vehicle['운전자ID'].astype(str) == user_id_input) &
                    (df_vehicle['운전자이름'] == user_name_input) &
                    (df_vehicle['년월'] == int(input_yyyymm))
                ].sort_values(by="주행거리(km)", ascending=False).head(5)

                if not df_vehicle_filtered.empty:
                    df_vehicle_display = df_vehicle_filtered.copy()
                    df_vehicle_display["주행거리(km)"] = df_vehicle_display["주행거리(km)"].apply(lambda x: f"{int(x):,} km")
                    df_vehicle_display["웜업비율(%)"] = df_vehicle_display["웜업비율(%)"].apply(lambda x: f"{x * 100:.2f}%")
                    df_vehicle_display["공회전비율(%)"] = df_vehicle_display["공회전비율(%)"].apply(lambda x: f"{x * 100:.2f}%")
                    df_vehicle_display["급감속(회)/100km"] = df_vehicle_display["급감속(회)/100km"].apply(lambda x: f"{x:.2f}")
                    df_vehicle_display["연비(km/m3)"] = df_vehicle_display["연비(km/m3)"].apply(lambda x: f"{x:.2f}")

                    def format_grade(g):
                        color = "green" if g in ["S", "A"] else "orange" if g in ["B", "C"] else "red"
                        return f"<span style='color:{color}; font-weight:bold'>{g}</span>"

                    df_vehicle_display["등급"] = df_vehicle_display["등급"].apply(format_grade)

                    df_vehicle_display = df_vehicle_display[["노선번호", "차량번호4", "주행거리(km)", "웜업비율(%)", "공회전비율(%)", "급감속(회)/100km", "연비(km/m3)", "등급"]]

                    df_vehicle_display = df_vehicle_display.rename(columns={
                        "노선번호" : "노선",
                        "차량번호4": "차량번호",
                        "주행거리(km)" : "주행거리",
                        "웜업비율(%)" : "웜업률(%)", 
                        "공회전비율(%)" : "공회전율(%)",
                        "연비(km/m3)": "연비"
                    })

                    st.write("""
                    <style>
                    td span {
                        font-size: 15px;
                    }
                    table td {
                        white-space: nowrap !important;
                        text-align: center;
                        vertical-align: middle;
                    }
                    </style>
                    """, unsafe_allow_html=True)

                    st.write(df_vehicle_display.to_html(escape=False, index=False), unsafe_allow_html=True)

                st.markdown("---")

                # 7. 개인 맞춤 피드백
                st.subheader("🗣️ 개인 맞춤 피드백")

                #급감속 멘트
                break_text = f"""
                <br>
                <p style='font-size: 22px; font-style: italic;'>
                <b>{next_month}</b>월에는, <b>급감속</b>을 줄여봅시다.<br>
                이번달 급감속 <b>{round(this_break, 2)}</b> 급감속은 <b>매탕 1회 미만!</b><br>
                이것만 개선해도 연비 5% 개선, 
                <span style='color: green; font-weight: bold;'>{grade_target}등급</span>까지 도달 목표!!
                </p>"""

                #공회전멘트
                idle_text = f"""
                <br>
                <p style='font-size: 22px; font-style: italic;'>
                <b>{next_month}</b>월에는, <b>공회전</b>을 줄여봅시다.<br>
                이번달 공회전 <b>{round(this_idle * 100)}%</b> 공회전은 <b>5분 미만!</b><br>
                이것만 개선해도 연비 5% 개선, 
                <span style='color: green; font-weight: bold;'>{grade_target}등급</span>까지 도달 목표!!
                </p>"""

                #급감속이 5보다 작으면 공회전관리멘트 보여주기
                additional_text = idle_text if this_break <5 else  break_text

                st.markdown(f"""
                <div style='background-color: rgba(211, 211, 211, 0.3); padding: 10px; border-radius: 5px;'>
                {additional_text}
                </div>
                """, unsafe_allow_html=True)

                # 조건별 자동 피드백 생성
                # st.markdown("### 📌 사고위험/공회전 분석 피드백")
                break_ = row["이번달급가속(회)/100km"]
                idle = row["이번달공회전비율(%)"] * 100

                feedback_parts = []
                if break_ < row["노선평균급감속(회)/100km"]:
                    feedback_parts.append("✅ 사고위험 발생이 매우 적어 안전 운전에 기여하고 있습니다.")
                elif break_ < 80:
                    feedback_parts.append("🟡 사고위험이 다소 발생하고 있습니다. ")
                else:
                    feedback_parts.append("⚠️ 사고위험 지수가 높습니다. 매탕 급감속 횟수 1회씩만 줄여보세요.")

                if idle > row["노선평균공회전비율(%)"]*100:
                    feedback_parts.append("⚠️ 공회전 비율이 높습니다. 정차 시 시동 관리에 유의해 주세요.")
                elif idle > 40:
                    feedback_parts.append("🟡 공회전이 평균보다 다소 높습니다. 불필요한 정차를 줄여주세요.")
                else:
                    feedback_parts.append("✅ 공회전 관리가 잘 되고 있습니다.")

                st.markdown("<br>".join(feedback_parts), unsafe_allow_html=True)

                
            else:
                    st.warning("운수사, 운전자 ID, 운전자 이름을 확인해주세요.")
        # 예시: st.dataframe(data_sheets["운전자별"])

    # 사용자가 선택한 운수사 출력 (디버깅용)
    st.sidebar.markdown(f"선택한 운수사: **{selected_company}**")

