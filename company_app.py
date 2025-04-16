import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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
        '평균속도': 'mean',
        '운수사달성율' : 'sum'
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
    result['달성율'] = result['운수사달성율']
    result['연비'] = result['주행거리'] / result['연료소모량']
    result['웜업률'] = result['웜업시간'] / result['주행시간']
    result['공회전율'] = result['공회전시간'] / result['주행시간']
    result['탄력운전비율'] = result['탄력운전거리'] / result['주행거리']
    result['급가속(회/100km)'] = result['급가속'] * 100 / result['주행거리_속도0']
    result['급감속(회/100km)'] = result['급감속'] * 100 / result['주행거리_속도0']

    return result[['년월', '운수사', '달성율', '웜업률', '공회전율', '탄력운전비율', '평균속도', '급가속(회/100km)', '급감속(회/100km)']]

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

# =====================
# 🚀 Streamlit UI
# =====================
st.set_page_config(page_title="운수사 관리자 분석", layout="wide")

st.title("📊 운수사 관리자용 분석 대시보드")

# 데이터 로딩
df = load_and_process_data()

# UI 선택 영역
selected_month = st.selectbox("📅 년월 선택", sorted(df['년월'].unique()))
selected_company = st.selectbox("🚍 운수사 선택", sorted(df['운수사'].unique()))

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
df_month = df[df['년월'] == selected_month].copy()
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
                     width:100px; height:100px; display:flex; flex-direction:column; 
                     justify-content:center; align-items:center; margin:auto;'>
            <b style='font-size:24px;'>{rank}위</b>
            <div style='font-size:12px;'>{metric}</div>
        </div>
        """, unsafe_allow_html=True)

# =====================
# 인천 전체 보고서 보기 구조 (항목별로 다시 계산한 평균)
# =====================
st.markdown("---")
st.markdown(f"### 📈 {selected_company} vs 인천 전체 평균 (지표별 추이)")

compare_metrics = ['웜업률', '공회전율', '급감속(회/100km)', '평균속도']

# 인천 전체 지표 재계산 (월별로 다시 계산)
df_incheon = df.groupby('년월').apply(lambda x: pd.Series({
    '웜업률': x['웜업시간'].sum() / x['주행시간'].sum(),
    '공회전율': x['공회전시간'].sum() / x['주행시간'].sum(),
    '급감속(회/100km)': x[x['속도필터'] == 0]['급감속(회/100km)'].sum() * 100 / x[x['속도필터'] == 0]['주행거리'].sum(),
    '평균속도': x['평균속도'].mean()
})).reset_index()

df_target = df[df['운수사'] == selected_company][['년월'] + compare_metrics]

# 선 그래프 출력
for metric in compare_metrics:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_incheon['년월'], y=df_incheon[metric], mode='lines+markers', name='인천 평균'))
    fig.add_trace(go.Scatter(x=df_target['년월'], y=df_target[metric], mode='lines+markers', name=selected_company))
    fig.update_layout(title=f"📊 {metric} 추이", xaxis_title='년월', yaxis_title=metric)
    st.plotly_chart(fig, use_container_width=True)
