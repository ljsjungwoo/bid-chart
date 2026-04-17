import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# ── 페이지 설정 ───────────────────────────────────────────────────
st.set_page_config(page_title='업체별 PQ 투찰 예가율', layout='wide')

st.markdown("""
<style>
/* 차트 컨테이너가 수평 스크롤 되도록 */
.chart-wrapper {
    overflow-x: auto;
    overflow-y: auto;
    width: 100%;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    background: white;
}
/* 사이드바 안내 텍스트 */
.tip-box {
    background: #f0f4ff;
    border-left: 4px solid #2E5FA3;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 13px;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)


# ── 1. 데이터 불러오기 ────────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('biddata.csv', encoding='cp949', index_col=0)
        df = df[~(df.index.isna() |
                  (df.index.astype(str).str.strip() == '') |
                  (df.index.astype(str).str.strip() == 'nan'))]
        df = df.dropna(how='all')
        for col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace('%', ''), errors='coerce')
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류 발생: {e}")
        return pd.DataFrame()


df = load_data()
if df.empty:
    st.stop()

companies = df.index.tolist()
n = len(companies)

# ── 2. special_lines 정의 ─────────────────────────────────────────
special_lines = [
    98.1193, 98.4078, 98.6813, 98.9429, 99.1882,
    99.4573, 99.7570, 100.0619, 100.2842, 100.5235,
    100.7972, 101.0775, 101.3374, 101.6024, 101.8581
]

# ── 3. 사이드바 설정 ──────────────────────────────────────────────
st.sidebar.header('⚙️ 차트 설정')

# Y축 표시 범위 (좁게 볼수록 세로 탐색이 편함)
y_min = st.sidebar.slider('Y축 최솟값 (%)', 97.0, 99.5, 98.5, step=0.1)
y_max = st.sidebar.slider('Y축 최댓값 (%)', 100.5, 103.0, 101.5, step=0.1)

# 업체당 픽셀 너비 — 넓힐수록 X축 여유 확보
px_per_company = st.sidebar.slider(
    '업체당 폭 (px)', min_value=40, max_value=200, value=90, step=10)

chart_height = st.sidebar.slider(
    '차트 높이 (px)', 600, 3000, 1400, step=100)

data_font_size = st.sidebar.slider('숫자 크기', 8, 22, 12)

show_company_labels = st.sidebar.checkbox('예가율 행에 업체명 표시', value=True)

st.sidebar.markdown("""
<div class="tip-box">
💡 <b>탐색 방법</b><br>
• <b>좌우 스크롤</b>: 차트 아래 스크롤바 또는 Shift+휠<br>
• <b>상하 확대</b>: Y축 드래그 또는 위 슬라이더<br>
• <b>특정 값 확인</b>: 점 위에 마우스 올리기<br>
• <b>영역 확대</b>: 차트 위에서 드래그
</div>
""", unsafe_allow_html=True)

# ── 4. 차트 너비 계산 ─────────────────────────────────────────────
# 업체 수 × 업체당 픽셀 + 라벨 여백(좌우 각 160px)
chart_width = n * px_per_company + 320
chart_width = max(chart_width, 800)

# ── 5. 차트 생성 ──────────────────────────────────────────────────
st.title('업체별 2026 PQ 투찰 예가율 분석')
st.caption(f"유효 업체 수: {n}개  |  차트 너비: {chart_width:,}px  |  좌우 스크롤로 탐색하세요")

fig = go.Figure()

shapes = []
annotations = []

# ── 5-1. 배경 가로선 (0.05 간격, 연회색) ─────────────────────────
for y in np.arange(y_min, y_max + 0.001, 0.05):
    yr = round(y, 4)
    shapes.append(dict(
        type='line', x0=-0.5, x1=n - 0.5, xref='x', y0=yr, y1=yr, yref='y',
        line=dict(color='#EEEEEE', width=0.5), layer='below'
    ))

# ── 5-2. 0.1 간격 가로선 (굵기/색상 구분) ────────────────────────
blue_lines = {99.0, 99.5, 100.5, 101.0}
company_label_ys = [round(y, 1) for y in np.arange(98.6, 101.5, 0.2)]
# 100.0 포함 여부 확인용 set
label_ys_set = set(company_label_ys)

for y in np.arange(y_min, y_max + 0.001, 0.1):
    yr = round(y, 4)
    if abs(yr - 100.0) < 0.001:
        color, width = '#FF0000', 3.5
    elif yr in blue_lines:
        color, width = '#1155CC', 2.5
    elif yr in label_ys_set:
        color, width = '#444444', 2.0
    elif abs(yr % 0.5) < 0.001 or abs(yr % 0.5 - 0.5) < 0.001:
        color, width = '#888888', 1.8
    else:
        color, width = '#BBBBBB', 0.9

    if y_min <= yr <= y_max:
        shapes.append(dict(
            type='line', x0=-0.5, x1=n - 0.5, xref='x', y0=yr, y1=yr, yref='y',
            line=dict(color=color, width=width), layer='below'
        ))

# ── 5-3. 업체별 세로 가이드선 ────────────────────────────────────
for x_idx in range(n):
    shapes.append(dict(
        type='line',
        x0=x_idx, x1=x_idx, xref='x',
        y0=y_min, y1=y_max, yref='y',
        line=dict(color='#CCCCCC', width=0.8),
        layer='below'
    ))

# ── 5-4. special_lines 빨간 점선 + 번호 라벨 ─────────────────────
for i, line_val in enumerate(special_lines):
    if y_min <= line_val <= y_max:
        shapes.append(dict(
            type='line', x0=-0.5, x1=n - 0.5, xref='paper',
            y0=line_val, y1=line_val, yref='y',
            line=dict(color='#FF4444', width=1.5, dash='dash'),
            layer='above'
        ))
        label_text = f"<b>({i+1:02d}) {line_val:.4f}%</b>"
        # 왼쪽 라벨
        annotations.append(dict(
            x=-0.5, xref='x', y=line_val, yref='y',
            text=label_text, showarrow=False, xanchor='right',
            font=dict(color='red', size=11),
            bgcolor='rgba(255,255,255,0.85)'
        ))
        # 오른쪽 라벨
        annotations.append(dict(
            x=n - 0.5, xref='x', y=line_val, yref='y',
            text=label_text, showarrow=False, xanchor='left',
            font=dict(color='red', size=11),
            bgcolor='rgba(255,255,255,0.85)'
        ))

# ── 5-5. company_label_ys 행: 업체명 텍스트 ─────────────────────
if show_company_labels:
    for label_y in company_label_ys:
        if not (y_min <= label_y <= y_max):
            continue
        if abs(label_y - 100.0) < 0.001:
            continue
        for x_idx, company in enumerate(companies):
            annotations.append(dict(
                x=x_idx, xref='x',
                y=label_y + 0.020, yref='y',
                text=f"<span style='font-size:9px;color:#444'>{company}</span>",
                showarrow=False,
                xanchor='center', yanchor='bottom',
                bgcolor='rgba(255,255,255,0.75)',
                font=dict(size=9, color='#333333')
            ))

# ── 5-6. 데이터 포인트 (hover 포함) ─────────────────────────────
all_x, all_y, all_text, all_hover = [], [], [], []

for x_idx, company in enumerate(companies):
    vals = df.loc[company].dropna().values
    for v in vals:
        if y_min <= v <= y_max:
            all_x.append(x_idx)
            all_y.append(v)
            all_text.append(f"<b>{v:.4f}</b>")
            all_hover.append(f"<b>{company}</b><br>예가율: {v:.4f}%")

# 배경 마커 (흰 박스)
fig.add_trace(go.Scatter(
    x=all_x, y=all_y,
    mode='markers',
    marker=dict(
        symbol='square',
        color='rgba(255,255,255,0.9)',
        size=data_font_size * 2.6,
        line=dict(width=0)
    ),
    hoverinfo='skip',
    showlegend=False
))

# 텍스트 + hover
fig.add_trace(go.Scatter(
    x=all_x, y=all_y,
    mode='markers+text',
    text=all_text,
    textposition='middle center',
    textfont=dict(size=data_font_size, color='#111111', family='monospace'),
    marker=dict(symbol='square', color='rgba(0,0,0,0)', size=data_font_size * 2.6),
    hovertext=all_hover,
    hoverinfo='text',
    hoverlabel=dict(bgcolor='#1F3864', font_color='white', font_size=13),
    showlegend=False
))

# ── 6. 레이아웃 ───────────────────────────────────────────────────
fig.update_layout(
    width=chart_width,
    height=chart_height,
    shapes=shapes,
    annotations=annotations,
    margin=dict(l=160, r=160, t=60, b=120),
    plot_bgcolor='white',
    paper_bgcolor='white',
    title=dict(
        text='2026 업체별 투찰 예가',
        font=dict(size=18, color='#1F3864'),
        x=0.5
    ),
    xaxis=dict(
        tickmode='array',
        tickvals=list(range(n)),
        ticktext=companies,
        tickangle=-90,
        tickfont=dict(size=14, color='#000000'),
        showgrid=False,
        zeroline=False,
        range=[-0.8, n - 0.2],
        fixedrange=False,   # X축 드래그/줌 허용
    ),
    yaxis=dict(
        range=[y_min, y_max],
        dtick=0.1,
        tickformat='.2f',
        ticksuffix='%',
        showgrid=False,     # 수동 shapes로 대체
        zeroline=False,
        fixedrange=False,   # Y축 드래그/줌 허용
        tickfont=dict(size=14, color='#000000'),
    ),
    yaxis2=dict(           # 우측 Y축 (twin)
        overlaying='y',
        side='right',
        range=[y_min, y_max],
        dtick=0.1,
        tickformat='.1f',
        ticksuffix='%',
        showgrid=False,
        zeroline=False,
        tickfont=dict(size=14, color='#000000'),
    ),
    dragmode='pan',        # 기본 드래그 모드: 패닝
    hovermode='closest',
)

# ── 7. 차트 출력 (수평 스크롤 래퍼 안에) ────────────────────────
st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
st.plotly_chart(
    fig,
    use_container_width=False,   # ← False 여야 width 고정 유지 → 스크롤 작동
    config={
        'scrollZoom': True,          # 마우스 휠 줌
        'displayModeBar': True,
        'modeBarButtonsToAdd': ['pan2d', 'zoomIn2d', 'zoomOut2d', 'resetScale2d'],
        'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'bid_chart',
            'scale': 2
        }
    }
)
st.markdown('</div>', unsafe_allow_html=True)

# ── 8. 업체 검색 ─────────────────────────────────────────────────
st.divider()
st.subheader('🔍 업체별 투찰값 조회')
selected = st.selectbox('업체 선택', companies)
if selected:
    vals = df.loc[selected].dropna().values
    vals_in_range = [v for v in sorted(vals) if y_min <= v <= y_max]
    cols = st.columns(min(len(vals_in_range), 6))
    for i, v in enumerate(vals_in_range):
        # 어떤 special_line과 가장 가까운지 표시
        closest_idx = int(np.argmin([abs(v - sl) for sl in special_lines]))
        diff = v - special_lines[closest_idx]
        sign = '+' if diff >= 0 else ''
        cols[i % 6].metric(
            label=f"투찰값 {i+1}",
            value=f"{v:.4f}%",
            delta=f"({closest_idx+1:02d})번선 {sign}{diff:.4f}%p"
        )
