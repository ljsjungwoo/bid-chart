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
chart_height = st.sidebar.slider('차트 높이 (px)', 600, 5000, 1500, step=100)

# ── 3. 기준선 데이터 ──────────────────────────────────────────────
# 요청하신 15개의 핵심 가로선 데이터
special_lines = [98.1193, 98.4078, 98.6813, 98.9429, 99.1882, 99.4573, 99.7570,
                 100.0619, 100.2842, 100.5235, 100.7972, 101.0775, 101.3374, 101.6024, 101.8581]

# ── 4. 차트 생성 ──────────────────────────────────────────────────
st.title('업체별 2026 PQ 투찰 예가율 분석')

fig = go.Figure()

shapes = []
annotations = []

# ── 4-1. 요청하신 15개 가로선 (special_lines) 그리기 ──────────────────
for i, line_val in enumerate(special_lines):
    # 현재 설정된 Y축 범위 내에 있을 때만 그립니다.
    if y_start <= line_val <= y_end:
        num = i + 1  # 1번부터 번호 부여
        
        # 가로 점선 추가
        shapes.append(dict(
            type='line', x0=0, x1=1, xref='paper',
            y0=line_val, y1=line_val, yref='y',
            line=dict(color='red', width=1, dash='dash')
        ))
        
        # 왼쪽 라벨 추가
        annotations.append(dict(
            x=0, xref='paper', y=line_val, yref='y',
            text=f"<b>{num}번 ({line_val:.4f})</b>",
            showarrow=False, xanchor='right', xshift=-10,
            font=dict(color='red', size=11), bgcolor='rgba(255,255,255,0.8)'
        ))
        
        # 오른쪽 라벨 추가
        annotations.append(dict(
            x=1, xref='paper', y=line_val, yref='y',
            text=f"<b>{num}번 ({line_val:.4f})</b>",
            showarrow=False, xanchor='left', xshift=10,
            font=dict(color='red', size=11), bgcolor='rgba(255,255,255,0.8)'
        ))

# ── 4-2. 100% 빨간 실선 강조 (기존 유지) ───────────────────────────────
if y_start <= 100.0 <= y_end:
    shapes.append(dict(
        type='line', x0=0, x1=1, xref='paper',
        y0=100.0, y1=100.0, yref='y',
        line=dict(color='red', width=3)
    ))

# ── 4-3. 데이터 숫자 뿌리기 (X표시 없음) ───────────────────────────────
for x_idx, company in enumerate(companies):
    vals = df.loc[company].dropna().values
    y_vals = [v for v in vals if y_start <= v <= y_end]
    
    if y_vals:
        fig.add_trace(go.Scatter(
            x=[x_idx] * len(y_vals), y=y_vals,
            mode='text',
            text=[f"<b>{v:.4f}</b>" for v in y_vals],
            textfont=dict(size=10, color='black'),
            showlegend=False,
            hoverinfo='none'
        ))

# ── 5. 레이아웃 및 디자인 설정 ──────────────────────────────────────────
fig.update_layout(
    shapes=shapes,
    annotations=annotations,
    height=chart_height,
    margin=dict(l=100, r=100, t=50, b=100), # 라벨 공간 확보를 위해 좌우 여백 확대
    plot_bgcolor='white',
    xaxis=dict(
        tickmode='array', tickvals=list(range(n)), ticktext=companies,
        tickangle=-90, showgrid=True, gridcolor='#EEEEEE', zeroline=False
    ),
    yaxis=dict(
        range=[y_start, y_end], dtick=0.1, tickformat='.2f',
        showgrid=True, gridcolor='#E8E8E8', zeroline=False
    ),
)

# ── 6. 최종 렌더링 ────────────────────────────────────────────────
st.plotly_chart(fig, use_container_width=True)
