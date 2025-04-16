import streamlit as st
import pandas as pd

# =====================
# 📦 데이터 불러오기 & 처리
# =====================
@st.cache_data
def load_and_process_data():
    df = pd.read_excel("company_total.xlsx", sheet_name="차량별")

    # 컬럼명 매핑
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

    # 속도필터 0만 필터링 (급가속/급감속 계산용)
    df_speed0 = df[df['속도필터'] == 0]

    # 일반 그룹 집계
    grouped = df.groupby(['년월', '운수사']).agg({
        '주행거리': 'sum',
        '연료소모량': 'sum',
        '웜업시간': 'sum',
        '공회전시간': 'sum',
        '주행시간': 'sum',
        '탄력운전거리': 'sum',
        '평균속도': 'mean'
    }).reset_index()

    # 속도필터=0 그룹 집계
    aggr_speed0 = df_speed0.groupby(['년월', '운수사']).agg({
        '급가속': 'sum',
        '급감속': 'sum',
        '주행거리': 'sum'
    }).rename(columns={'주행거리': '주행거리_속도0'}).reset_index()

    # 병합
    result = pd.merge(grouped, aggr_speed0, on=['년월', '운수사'], how='left')

    # 계산식 적용
    result['달성율'] = result['주행거리'] / result['연료소모량']
    result['웜업률'] = result['웜업시간'] / result['주행시간']
    result['공회전율'] = result['공회전시간'] / result['주행시간']
    result['탄력운전비율'] = result['탄력운전거리'] / result['주행거리']
    result['급가속(회/100km)'] = result['급가속'] * 100 / result['주행거리_속도0']
    result['급감속(회/100km)'] = result['급감속'] * 100 / result['주행거리_속도0']

    return result[['년월', '운수사', '달성율', '웜업률', '공회전율', '탄력운전비율', '평균속도', '급가속(회/100km)', '급감속(회/100km)']]

# =====================
# 🚀 Streamlit UI
# =====================
st.set_page_config(page_title="운수사 관리자 분석", layout="wide")

st.title("🧑‍💼 운수사 관리자용 분석 대시보드")
st.markdown("운수사별로 월별 주요 항목들을 비교하고 순위를 확인할 수 있습니다.")

# 데이터 로딩
df = load_and_process_data()

# UI 선택 영역
yearmonth_options = sorted(df["년월"].unique())
metric_options = ['달성율', '웜업률', '공회전율', '탄력운전비율', '평균속도', '급가속(회/100km)', '급감속(회/100km)']

selected_ym = st.selectbox("📅 년월 선택", yearmonth_options)
selected_metric = st.selectbox("📊 항목 선택", metric_options)

# 데이터 필터링 및 정렬
filtered = df[df["년월"] == selected_ym].copy()

# 📌 항목별 정렬 방향 반영
ascending_map = {
    '달성율': False,
    '탄력운전비율': False,
    '평균속도': False,
    '웜업률': True,
    '공회전율': True,
    '급가속(회/100km)': True,
    '급감속(회/100km)': True
}
ascending = ascending_map.get(selected_metric, False)
filtered["순위"] = filtered[selected_metric].rank(ascending=ascending, method="min").astype(int)
filtered = filtered.sort_values("순위")

# 결과 출력
st.markdown(f"### {selected_ym}월 - **{selected_metric}** 기준 운수사 순위")
st.dataframe(filtered[["운수사", selected_metric, "순위"]].reset_index(drop=True), use_container_width=True)
