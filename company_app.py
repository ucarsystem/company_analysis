import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io
#페이지 설정 (가장 맨위에 호출시켜야함!)
st.set_page_config(page_title="운수사 관리자 페이지", layout="wide")
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
        st.header("📊 대시보드")
        st.title("📊 운수사 관리자용 분석 대시보드")

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
        st.markdown(f"### 🚩 {selected_month}월 - **{selected_company}** 항목별 순위")
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
        st.header(f"⭐ {selected_company} 운전자등급")

        # 📅 년/월 선택
        year = st.selectbox("년도 선택", ["2024", "2025"])
        month = st.selectbox("월 선택", [f"{i:02d}" for i in range(1, 13)])
        ym = int(year[2:] + month)

        #등급별 색깔 함수
        def color_by_grade(val):
            color_map = {
                "S": "#00B050",  # 초록
                "A": "#00B050",  # 초록
                "B": "#0070C0",  # 파랑
                "C": "#0070C0",  # 파랑
                "D": "#FF0000",  # 빨강
                "F": "#FF0000",  # 빨강
            }
            color = color_map.get(val, "")
            return f"background-color: {color}; color: white"
        # 텍스트용
        def get_grade_color(val):
            color_map = {
                "S": "#00B050",  # 초록
                "A": "#00B050",
                "B": "#0070C0",
                "C": "#0070C0",
                "D": "#FF0000",
                "F": "#FF0000",
            }
            return color_map.get(val, "#000")

        #시트 선택
        sheet_name = f"운전자별({year[:2]})"
        df_person = data_sheets[sheet_name]

        if df_person is not None:
            df_person = df_person.copy()
            df_person = df_person[(df_person["년월"]==ym) & (df_person["운수사"] == selected_company)]

            #등급설명 추가
            grade_desc = {"S":"최우수", "A": "우수", "B": "양호", "C": "보통", "D": "주의", "F": "경고"}
            df_person['등급설명'] = df_person['등급'].map(grade_desc)

            # 1. 등급 비중 시각화
            st.subheader("📊 등급별 비중")

            #null제외
            df_nonull = df_person[df_person["운전자이름"].notnull()]

            #운수사별 평균 등급

            # 등급 → 점수 변환
            grade_to_score = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
            score_to_grade = {v: k for k, v in grade_to_score.items()}

            avg_score = df_nonull["등급"].map(grade_to_score).mean()
            rounded = int(round(avg_score))
            avg_grade = score_to_grade.get(rounded, "N/A")
            color = get_grade_color(avg_grade)

            # 텍스트로 강조 출력
            st.markdown(f"""
            <div style="font-size:20px; font-weight:bold;">
            <span style="color: #444;">{year}년 {int(month)}월 평균등급 :</span>
            <span style="color:{color};"> {avg_grade} 등급</span>
            </div>
            """, unsafe_allow_html=True)

            # 등급별 비중
            grade_counts = df_nonull["등급"].value_counts().reset_index()
            grade_counts.columns = ["등급", "인원수"]

            fig = px.pie(
                grade_counts,
                values="인원수",
                names="등급",
                title=f"{year}년 {int(month)}월 운전자 등급 비중",
                color_discrete_map = {
                    "S": "#00B050",  # 초록
                    "A": "#00B050",  # 초록
                    "B": "#0070C0",  # 파랑
                    "C": "#0070C0",  # 파랑
                    "D": "#FF0000",  # 빨강
                    "F": "#FF0000",  # 빨강
                }
            )
            st.plotly_chart(fig, use_container_width=True)

            # 2. 운수사별 명단 테이블
            st.subheader("🧾 등급별 명단")
            selected_cols = ["운수사", "노선번호", "운전자이름", "운전자ID", "가중달성율", "등급", "등급설명", "주운행차량", "주행거리(km)"]
            df_display = df_person[selected_cols].fillna("")

            df_display = df_display.rename(columns={
                '주행거리(km)': '주행거리',
                '노선번호' : '노선',
                '운전자이름' : '사원명',
                '가중달성율' : '목표달성율'
            })

            st.dataframe(
                df_display.style.applymap(color_by_grade, subset=["등급"]).hide(axis="index"),
                use_container_width=True,
                height=len(df_display) * 35 + 60
            )
            
        else:
            st.markdown(f"❗ '{selected_company}' 의 자료가 없습니다.")



        # 예시: st.dataframe(data_sheets["운전자별"])

    elif menu == "10. 개별분석표":
        st.header("📌 개별분석표")
        # 예시: st.dataframe(data_sheets["운전자별"])

    # 사용자가 선택한 운수사 출력 (디버깅용)
    st.sidebar.markdown(f"선택한 운수사: **{selected_company}**")

