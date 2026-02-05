import streamlit as st
import pandas as pd

# 모듈 임포트
from utils.db_manager import load_data, apply_filters
from utils.metrics import (
    calculate_metrics_with_comparison, 
    calculate_delta, 
    format_number,
    get_comparison_metrics,
    get_key_metrics_summary # 추가
)
from components.charts import (
    create_main_performance_map, 
    get_top_bottom_ranking, 
    get_performance_summary, 
    create_top_states_trend, 
    create_satisfaction_vs_sales,
    create_monthly_sales_chart,
    create_top5_categories_chart
)
from components.pdf_report import generate_download_button

# -----------------------------------------------------------------------------
# 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Brazilian E-Commerce Dashboard", 
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 커스텀 CSS (Premium Design)
# - 사용자 이미지와 최대한 유사한 스타일 복원
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* 메인 타이틀 스타일 */
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0px;
    }
    .main-title span {
        font-size: 1.5rem;
        color: #aaaaaa;
        vertical-align: middle;
    }

    /* 메트릭 값 스타일 (Metric Value) */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700;
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #262730;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 메인 로직
# -----------------------------------------------------------------------------

def main():
    # 1. 헤더: 사용자 이미지에 맞춰 심플하게 타이틀만 배치
    # "Brazilian E-Commerce 대시보드" + 아이콘 형태
    st.markdown('<div class="main-title">Brazilian E-Commerce 대시보드 <span>🔗</span></div>', unsafe_allow_html=True)
    st.markdown("---")

    # 2. 데이터 로드
    # 로딩 메시지 없이 조용히 로드 (사용자 경험 개선)
    df, df_geolocation = load_data()

    if df.empty:
        st.error("데이터를 불러오는데 실패했습니다. DB 연결 설정을 확인해주세요.")
        return

    # 3. 사이드바 (필터링)
    with st.sidebar:
        st.title("필터 옵션")
        
        # 연월 리스트 생성
        if 'y_mth' in df.columns:
            year_mth_list = ['All'] + sorted(df['y_mth'].unique())
        else:
            year_mth_list = ['All']
            
        selected_month = st.selectbox("연월 선택", year_mth_list, index=0)
        
        # 지역 리스트
        state_options = sorted(df_geolocation['geolocation_state'].unique().tolist())
        selected_state = st.multiselect("지역 선택", state_options)
        
        st.markdown("### 📄 리포트 다운로드")
        download_container = st.container()

    # 4. 필터링 적용
    filtered_df = apply_filters(df, selected_month, selected_state)

    # 5. 핵심 메트릭 계산
    current_metrics, prev_metrics, can_compare = calculate_metrics_with_comparison(
        filtered_df, selected_month, df, selected_state
    )

    deltas = {}
    if can_compare:
        for key in current_metrics.keys():
            deltas[key] = calculate_delta(current_metrics[key], prev_metrics.get(key, 0))

    # -------------------------------------------------------------------------
    # SEC 1: 상단 KPI 섹션 (5 Columns)
    # -------------------------------------------------------------------------
    # 레이아웃 간격 조정을 위해 columns 사용
    st.markdown("<br>", unsafe_allow_html=True)
    kpi_cols = st.columns(5)
    
    # helper for metrics
    def display_kpi(col, label, value, delta_val=None):
        col.metric(label, value, delta_val)

    display_kpi(kpi_cols[0], "총 매출", f"{format_number(current_metrics['total_amount'])} BRL", 
                f"{deltas.get('total_amount'):.1f}%" if can_compare and deltas.get('total_amount') else None)
    
    display_kpi(kpi_cols[1], "총 주문 수", f"{format_number(current_metrics['total_orders'])}", 
                f"{deltas.get('total_orders'):.1f}%" if can_compare and deltas.get('total_orders') else None)

    display_kpi(kpi_cols[2], "고객 수", f"{format_number(current_metrics['total_customers'])}", 
                f"{deltas.get('total_customers'):.1f}%" if can_compare and deltas.get('total_customers') else None)

    display_kpi(kpi_cols[3], "평균 주문 금액", f"{current_metrics['avg_order_value']:,.0f} BRL", 
                f"{deltas.get('avg_order_value'):.1f}%" if can_compare and deltas.get('avg_order_value') else None)

    display_kpi(kpi_cols[4], "상품 수", f"{format_number(current_metrics['total_products'])}", 
                f"{deltas.get('total_products'):.1f}%" if can_compare and deltas.get('total_products') else None)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SEC 2: 메인 차트 (월별 매출 + 카테고리)
    # -------------------------------------------------------------------------
    col_trend, col_cat = st.columns(2)

    with col_trend:
        # st.subheader("월별 결제 금액") -> 차트 타이틀로 이동됨
        if 'y_mth' in df.columns:
            monthly_data = df.groupby('y_mth')['payment_value'].sum().reset_index()
            fig_trend = create_monthly_sales_chart(monthly_data, selected_month)
            st.plotly_chart(fig_trend, use_container_width=True)

    with col_cat:
        # 타이틀은 plotly 차트 내부 혹은 바로 위에
        fig_cat = create_top5_categories_chart(filtered_df, selected_month)
        st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SEC 3: 운영 지표 (4 Columns)
    # -------------------------------------------------------------------------
    op_cols = st.columns(4)
    
    op_cols[0].metric(
        "정시 배송률", 
        f"{current_metrics['on_time_delivery_rate']:.1f}%",
        delta=f"{deltas.get('on_time_delivery_rate'):.1f}%" if can_compare and deltas.get('on_time_delivery_rate') else None
    )
    op_cols[1].metric(
        "평균 배송 소요시간", 
        f"{current_metrics['avg_shipping_time']:.1f}일",
        delta=f"{deltas.get('avg_shipping_time'):.1f}%" if can_compare and deltas.get('avg_shipping_time') else None,
        delta_color='inverse'
    )
    op_cols[2].metric(
        "재구매율", 
        f"{current_metrics['repeat_purchase_rate']:.2f}%",
        delta=f"{deltas.get('repeat_purchase_rate'):.2f}%" if can_compare and deltas.get('repeat_purchase_rate') else None
    )
    op_cols[3].metric(
        "고객 평균 평점", 
        f"{current_metrics['avg_review_score']:.2f}/5",
        delta=f"{deltas.get('avg_review_score'):.2f}%" if can_compare and deltas.get('avg_review_score') else None
    )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # SEC 4: 지역별 성과 분석
    # display_regional_performance_dashboard 내용 직접 구현 (Single Page Flow)
    # -------------------------------------------------------------------------
    st.subheader("🌎 지역별 성과 분석")
    
    # 4-1. 필터 적용 현황 (Comparison Metrics)
    comp_metrics = get_comparison_metrics(df, filtered_df)
    st.markdown("#### 📊 필터 적용 현황")
    
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    f_col1.metric("매출 비중", f"{comp_metrics['sales_ratio']:.1f}%", 
                  f"{comp_metrics['total_filtered_sales']:,.0f} / {comp_metrics['total_all_sales']:,.0f} BRL")
    f_col2.metric("주문 비중", f"{comp_metrics['orders_ratio']:.1f}%")
    f_col3.metric("고객 비중", f"{comp_metrics['customers_ratio']:.1f}%")
    f_col4.metric("필터 선택도", f"{100 - comp_metrics['sales_ratio']:.1f}%", "제외된 데이터 비율", delta_color="inverse")

    st.markdown("---")

    # 4-2. 지도 & 핵심 지표 사이드바
    st.markdown("#### 🎯 주별 종합 성과 지표 (필터 적용)") # 타이틀 명시
    
    col_map, col_map_sidebar = st.columns([2, 1])
    
    with col_map:
        fig_map = create_main_performance_map(filtered_df)
        st.plotly_chart(fig_map, use_container_width=True)

    with col_map_sidebar:
        st.markdown("#### 📊 핵심 지표 (필터 적용)")
        # get_key_metrics_summary 사용
        region_metrics = get_key_metrics_summary(filtered_df)
        
        rm_col1, rm_col2 = st.columns(2)
        rm_col1.metric("총 매출", f"{region_metrics['total_sales']:,.0f}")
        rm_col1.metric("총 고객수", f"{region_metrics['total_customers']:,}")
        rm_col1.metric("참여 주", f"{region_metrics['total_states']}")
        
        rm_col2.metric("총 주문수", f"{region_metrics['total_orders']:,}")
        rm_col2.metric("평균 평점", f"{region_metrics['avg_rating']:.2f}/5")
        rm_col2.metric("재구매율", f"{region_metrics['repeat_rate']:.1f}%")

    # 4-3. 성과 점수 설명
    with st.expander("📖 성과 점수 계산 방식"):
        st.info("""
        **종합 성과 점수 = 매출 비중(40%) + 평점 비중(30%) + 주문수 비중(30%)**
        - 🔴 낮은 성과 (0-40점)
        - 🟡 보통 성과 (40-70점)  
        - 🟢 높은 성과 (70-100점)
        
        원의 크기는 총 매출액을 반영합니다.
        ⚠️ **주의**: 지도와 랭킹은 필터된 데이터를 기준으로 합니다.
        """)

    # 4-4. 상위/하위 랭킹 (HTML Card Style)
    top_states, bottom_states = get_top_bottom_ranking(filtered_df)
    
    rank_col1, rank_col2 = st.columns(2)
    
    with rank_col1:
        st.markdown("### 🏆 매출 상위 지역 (필터 기준)")
        for i, row in top_states.head(5).iterrows():
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #2E8B57 0%, #90EE90 100%); 
                        padding: 10px; margin: 5px 0; border-radius: 5px; color: white;">
                <strong>{row['state']}</strong><br>
                💰 {row['total_sales']:,.0f} BRL<br>
                📦 {row['total_orders']:,} 주문
            </div>
            """, unsafe_allow_html=True)
            
    with rank_col2:
        st.markdown("### 📈 개선 기회 지역 (필터 기준)")
        for i, row in bottom_states.head(3).iterrows():
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #CD5C5C 0%, #FFA07A 100%); 
                        padding: 10px; margin: 5px 0; border-radius: 5px; color: white;">
                <strong>{row['state']}</strong><br>
                💰 {row['total_sales']:,.0f} BRL<br>
                ⭐ {row['avg_rating']:.1f}/5
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 4-5. 하단 차트
    chart_row2_col1, chart_row2_col2 = st.columns(2)
    with chart_row2_col1:
        fig_trend2 = create_top_states_trend(df)
        st.plotly_chart(fig_trend2, use_container_width=True)
    with chart_row2_col2:
        fig_scatter = create_satisfaction_vs_sales(df)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # 4-6. 상세 데이터 테이블
    st.markdown("#### 📋 전체 지역별 상세 성과 (필터 적용)")
    with st.expander("데이터 보기", expanded=True):
        perf_summary = get_performance_summary(filtered_df)
        # 3단 분리 표시
        if not perf_summary.empty:
            t_col1, t_col2, t_col3 = st.columns(3)
            rows = len(perf_summary)
            chunk_size = (rows // 3) + 1
            
            t_col1.dataframe(perf_summary.iloc[:chunk_size], use_container_width=True, hide_index=True)
            t_col2.dataframe(perf_summary.iloc[chunk_size:chunk_size*2], use_container_width=True, hide_index=True)
            t_col3.dataframe(perf_summary.iloc[chunk_size*2:], use_container_width=True, hide_index=True)

    # 4-7. 인사이트 (자동 생성 로직)
    # 간단한 로직으로 복원 
    st.markdown("#### 💡 핵심 인사이트 & 추천사항")
    
    # 인사이트 계산 로직 간단 구현 (metrics.py로 뺄 수도 있지만, UI 종속적이라 여기에 둠)
    state_gb = filtered_df.groupby('customer_state').agg({
        'payment_value': 'sum', 'review_score': 'mean', 'order_id': 'nunique'
    })
    
    if not state_gb.empty:
        best_sales_st = state_gb['payment_value'].idxmax()
        best_rating_st = state_gb['review_score'].idxmax()
        
        # 시장 집중도
        total_sales_val = state_gb['payment_value'].sum()
        top3_sales = state_gb['payment_value'].nlargest(3).sum()
        concentration = (top3_sales / total_sales_val) * 100 if total_sales_val > 0 else 0
        
        i_col1, i_col2, i_col3 = st.columns(3)
        
        with i_col1:
            st.success(f"""
            **🏆 성과 우수 지역**
            
            **매출 1위**: {best_sales_st}  
            💰 {state_gb.loc[best_sales_st, 'payment_value']:,.0f} BRL
            
            **평점 1위**: {best_rating_st}  
            ⭐ {state_gb.loc[best_rating_st, 'review_score']:.2f}/5
            """)
            
        with i_col2:
            st.info(f"""
            **📊 시장 분석**
            
            **시장 집중도**: {concentration:.1f}%  
            (상위 3개 주가 전체 매출의 60% 이상 차지 시 집중도 높음)
            
            **활성 주문 지역**: {state_gb['order_id'].idxmax()}  
            📦 {state_gb['order_id'].max():,} 주문
            """)
            
        with i_col3:
            st.warning(f"""
            **🎯 개선 제안**
            
            **집중 지원 필요**: {best_sales_st}  
            매출 대비 고객만족도 개선 필요 여부 확인
            
            **확장 기회**: 하위 지역 마케팅 강화  
            신규 고객 유치 및 브랜드 인지도 제고
            """)

    # 8. 리포트 다운로드 사이드바 버튼 활성화
    with download_container:
        if st.button("📊 PDF 리포트 생성", use_container_width=True):
            with st.spinner('리포트 생성 중...'):
                pdf_data, filename = generate_download_button(
                    df, filtered_df, selected_month, selected_state,
                    current_metrics, prev_metrics, can_compare
                )
                if pdf_data and filename:
                    st.download_button(
                        label="📥 PDF 다운로드",
                        data=pdf_data,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error("리포트 생성 실패")

if __name__ == "__main__":
    main()