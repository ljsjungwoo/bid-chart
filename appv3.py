import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# ── 페이지 설정 (최상단) ──────────────────────────────────────────
st.set_page_config(page_title='업체별 PQ 투찰 예가율', layout='wide')

# ── 1. 데이터 불러오기 (캐시 사용) ────────────────────────────────
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('biddata.csv', encoding='cp949', index_col=0)
        df = df[~(df.index.isna() | (df.index.astype(str).str.strip() == '') | (df.index.astype(str).str.strip() == 'nan'))]
        df = df.dropna(how='all')
        for col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='coerce')
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류 발생: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("데이터가 비어있습니다. 'biddata.csv' 파일을 확인해주세요.")
    st.stop()

companies = df.index.tolist()
n = len(companies)

# ── 2. 사이드바 설정 ──────────────────────────────────────────────
st.sidebar.header('⚙️ 차트 설정')
y_start = st.sidebar.slider('Y축 최솟값 (%)', 97.0, 99.5, 98.5, step=0.1)
y_end   = st.sidebar.slider('Y축 최댓값 (%)', 100.5, 103.0, 101.5, step=0.1)
# 초기 높이를 조금 낮게(1200px) 설정해서 먼저 뜨는지 확인합니다.
chart_height = st.sidebar.slider('차트 높이 (px)', 600, 5000, 1200, step=100)

# ── 3. 기준선 데이터 ──────────────────────────────────────────────
special_lines = [98.1193, 98.4078, 98.6813, 98.9429, 99.1882, 99.4573, 99.7570,
                 100.0619, 100.2842, 100.5235, 100.7972, 101.0775, 101.3374, 101.6024, 101.8581]
blue_lines = [99.0, 99.5, 100.5, 101.0]
company_label_ys = [round(y, 1) for y in np.arange(98.6, 101.5, 0.2)]

# ── 4. 차트 생성 ──────────────────────────────────────────────────
st.title('업체별 2026 PQ 투찰 예가율 분석')

fig = go.Figure()

# 가로선 및 레이블 추가
shapes = []
annotations = []

# 100% 빨간 실선 (최우선 표시)
if y_start <= 100.0 <= y_end:
    shapes.append(dict(type='line', x0=0, x1=1, xref='paper', y0=100.0, y1=100.0, yref='y',
                       line=dict(color='red', width=3)))

# 데이터 일괄 추가 (속도 최적화)
for x_idx, company in enumerate(companies):
    vals = df.loc[company].dropna().values
    y_vals = [v for v in vals if y_start <= v <= y_end]
    
    if y_vals:
        fig.add_trace(go.Scatter(
            x=[x_idx] * len(y_vals), y=y_vals,
            mode='text',
            text=[f"<b>{v:.4f}</b>" for v in y_vals],
            textfont=dict(size=10, color='black'),
            showlegend=False
        ))

fig.update_layout(
    height=chart_height,
    margin=dict(l=50, r=50, t=50, b=50),
    plot_bgcolor='white',
    xaxis=dict(tickmode='array', tickvals=list(range(n)), ticktext=companies, tickangle=-90, showgrid=True, gridcolor='#EEEEEE'),
    yaxis=dict(range=[y_start, y_end], dtick=0.1, tickformat='.2f', showgrid=True, gridcolor='#E8E8E8'),
)

# ── 5. 최종 렌더링 ────────────────────────────────────────────────
# 'width="stretch"' 대신 최신 규격인 'use_container_width=True' 사용
st.plotly_chart(fig, use_container_width=True)