import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_main_performance_map(filtered_df):
    """주별 매출 성과 (크기 + 색상) - Mapbox"""
    # 주별 성과 데이터 집계
    state_performance = filtered_df.groupby(['customer_state']).agg({
        'payment_value': ['sum', 'mean'],
        'order_id': 'nunique',
        'customer_unique_id': 'nunique',
        'review_score': 'mean',
        'customer_lat': 'mean',  # 대표 위치
        'customer_lng': 'mean'
    }).round(2)
    
    # 컬럼명 정리
    state_performance.columns = ['total_sales', 'avg_order_value', 'total_orders', 'total_customers', 'avg_rating', 'lat', 'lng']
    state_performance = state_performance.reset_index()
    
    # 성과 점수 계산 (매출 + 평점 + 주문수를 종합)
    if not state_performance.empty:
        max_sales = state_performance['total_sales'].max() or 1
        max_orders = state_performance['total_orders'].max() or 1
        
        state_performance['performance_score'] = (
            (state_performance['total_sales'] / max_sales * 0.4) +
            (state_performance['avg_rating'] / 5 * 0.3) +
            (state_performance['total_orders'] / max_orders * 0.3)
        ) * 100
    else:
        state_performance['performance_score'] = 0
    
    fig = px.scatter_mapbox(
        state_performance,
        lat='lat',
        lon='lng',
        size='total_sales',
        color='performance_score',
        hover_name='customer_state',
        hover_data={
            'total_sales': ':,.0f',
            'total_orders': ':,',
            'total_customers': ':,',
            'avg_order_value': ':,.0f',
            'avg_rating': ':.1f',
            'performance_score': ':.1f'
        },
        color_continuous_scale='RdYlGn',  # 빨강(낮음) → 노랑 → 초록(높음)
        size_max=30,
        zoom=2,
        center=dict(lat=-14.2350, lon=-51.9253),
        title='🎯 주별 종합 성과 지표 (필터 적용)'
    )
    
    fig.update_layout(
        mapbox_style='open-street-map',
        height=600,
        coloraxis_colorbar=dict(
            title="성과 점수",
            ticksuffix="점"
        )
    )
    
    return fig

def create_top_states_trend(df):
    """월별 상위 지역 트렌드"""
    if df.empty:
        return px.line(title='데이터 없음')

    # 전체 데이터에서 상위 5개 주의 월별 트렌드
    top_states_series = df.groupby('customer_state')['payment_value'].sum().nlargest(5)
    if top_states_series.empty:
        return px.line(title='데이터 부족')
        
    top_states = top_states_series.index
    
    trend_data = df[df['customer_state'].isin(top_states)].groupby(['y_mth', 'customer_state'])['payment_value'].sum().reset_index()
    
    fig = px.line(
        trend_data,
        x='y_mth',
        y='payment_value',
        color='customer_state',
        title='📈 상위 5개 주 매출 트렌드 (전체 기간)',
        markers=True
    )
    
    fig.update_layout(
        height=300,
        xaxis_title='월',
        yaxis_title='매출 (BRL)',
        legend_title='주',
        yaxis=dict(tickformat='~s'),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    
    return fig

def create_satisfaction_vs_sales(df):
    """지역별 고객 만족도 vs 매출 산점도"""
    if df.empty:
        return px.scatter(title='데이터 없음')

    # 전체 데이터로 전반적인 패턴 분석
    state_data = df.groupby('customer_state').agg({
        'payment_value': 'sum',
        'review_score': 'mean',
        'order_id': 'nunique'
    }).reset_index()
    
    fig = px.scatter(
        state_data,
        x='review_score',
        y='payment_value',
        size='order_id',
        hover_name='customer_state',
        title='⭐ 고객 만족도 vs 매출 관계 (전체 데이터)',
        labels={
            'review_score': '평균 평점',
            'payment_value': '총 매출 (BRL)',
            'order_id': '주문수'
        }
    )
    
    fig.update_layout(height=300)
    
    return fig

def create_monthly_sales_chart(monthly_data, selected_month):
    """월별 매출 라인 차트"""
    fig = px.line(
        monthly_data,
        x='y_mth',
        y='payment_value',
        title='월별 결제 금액',
        markers=True
    )

    # 축 설정
    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        yaxis=dict(tickformat='~s')
    )

    # 선택된 월 하이라이트 (add_shape 사용)
    if selected_month != 'All' and selected_month in monthly_data['y_mth'].values:
        fig.add_shape(
            type="line",
            x0=selected_month, x1=selected_month,
            y0=0, y1=1,
            yref="paper",  # y축을 전체 차트 높이 기준으로
            line=dict(color="red", width=2, dash="dash")
        )
        
        # 텍스트 주석 추가
        val = monthly_data[monthly_data['y_mth'] == selected_month]['payment_value'].iloc[0] if not monthly_data[monthly_data['y_mth'] == selected_month].empty else 0
        fig.add_annotation(
            x=selected_month,
            y=val,
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
        )
    return fig

def create_top5_categories_chart(filtered_df, selected_month):
    """상위 5개 카테고리 바 차트"""
    if filtered_df.empty:
        return px.bar(title='데이터 없음')

    top5_categories = (
        filtered_df.groupby('product_category_name')['payment_value']
        .sum()
        .nlargest(5)  # 상위 5개만
    ).reset_index()

    # 결과 조정
    top5_categories.columns = ['product_category_name', 'sum_amount']
    top5_categories = top5_categories.sort_values('sum_amount', ascending=True)

    fig = px.bar(
        top5_categories, 
        x='sum_amount', 
        y='product_category_name',
        orientation='h',  # 수평 바차트
        title=f'[{selected_month}] 상위 5개 카테고리별 매출'
    )

    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        yaxis=dict(tickformat='~s')
    )
    return fig

def get_top_bottom_ranking(filtered_df):
    """상위/하위 성과 지역 랭킹 데이터 반환"""
    if filtered_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # 주별 데이터 준비
    state_data = filtered_df.groupby('customer_state').agg({
        'payment_value': 'sum',
        'order_id': 'nunique',
        'customer_unique_id': 'nunique',
        'review_score': 'mean'
    }).reset_index()
    
    state_data.columns = ['state', 'total_sales', 'total_orders', 'total_customers', 'avg_rating']
    
    # 상위 8개, 하위 5개 주 선택
    top_states = state_data.nlargest(8, 'total_sales')
    bottom_states = state_data.nsmallest(5, 'total_sales')
    
    return top_states, bottom_states

def get_performance_summary(filtered_df):
    """지역별 성과 메트릭 테이블 데이터 반환"""
    if filtered_df.empty:
        return pd.DataFrame()

    # 주별 상세 성과 데이터
    state_details = filtered_df.groupby('customer_state').agg({
        'payment_value': 'sum',
        'review_score': 'mean',
        'order_id': 'nunique'
    }).round(2)
    
    state_details.columns = ['매출', '평점', '주문수']
    state_details = state_details.reset_index()
    state_details = state_details.sort_values('매출', ascending=False)
    
    return state_details
