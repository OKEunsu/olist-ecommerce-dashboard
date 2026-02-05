import pandas as pd

def format_number(num):
    """
    숫자를 K, M 단위로 포맷팅하는 함수
    """
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return f"{num:,.0f}"

def calculate_delta(current, previous):
    """증감률 계산"""
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100

def calculate_metrics_with_comparison(filtered_df, selected_month, df, selected_state=[]):
    """
    현재 메트릭과 전월 대비 증감률을 계산하는 함수 (추가 메트릭 포함)
    """
    if filtered_df.empty:
        # 빈 데이터프레임 처리
        empty_metrics = {
            'total_amount': 0, 'total_orders': 0, 'total_customers': 0,
            'avg_order_value': 0, 'total_products': 0,
            'on_time_delivery_rate': 0, 'avg_shipping_time': 0,
            'repeat_purchase_rate': 0, 'avg_review_score': 0
        }
        return empty_metrics, {}, False

    # ========================
    # 현재 메트릭 계산
    # ========================
    current_metrics = _calculate_single_period_metrics(filtered_df)
    
    # ========================
    # 전월 대비 계산
    # ========================
    can_compare = False
    prev_metrics = {}
    
    if selected_month != 'All':
        try:
            # 현재 월을 datetime으로 변환
            current_date = pd.to_datetime(selected_month, format='%Y-%m')
            # 전월 계산
            prev_date = current_date - pd.DateOffset(months=1)
            prev_month = prev_date.strftime('%Y-%m')
            
            # 전월 데이터가 있는지 확인
            if prev_month in df['y_mth'].values:
                # 전월 데이터 필터링 (지역 필터 적용)
                prev_df = df[df['y_mth'] == prev_month].copy()
                if selected_state:  # 지역 필터가 있으면 적용
                    prev_df = prev_df[prev_df['customer_state'].isin(selected_state)]
                
                if not prev_df.empty:
                    prev_metrics = _calculate_single_period_metrics(prev_df)
                    can_compare = True
        except Exception as e:
            print(f"전월 비교 계산 중 오류: {e}")
            can_compare = False
    
    return current_metrics, prev_metrics, can_compare

def _calculate_single_period_metrics(df):
    """단일 기간에 대한 메트릭 계산 (내부 헬퍼 함수)"""
    total_amount = df.groupby('y_mth')['payment_value'].sum().sum()
    total_orders = len(df['order_id'].unique())
    total_customers = len(df['customer_unique_id'].unique())
    avg_order_value = total_amount / total_orders if total_orders > 0 else 0
    total_products = len(df['product_id'].unique())
    
    # 정시 배송률 (%)
    df_copy = df.copy() # SettingWithCopyWarning 방지
    if 'order_delivered_customer_date' in df_copy.columns and 'order_estimated_delivery_date' in df_copy.columns:
        df_copy['on_time'] = df_copy['order_delivered_customer_date'] <= df_copy['order_estimated_delivery_date']
        on_time_delivery_rate = df_copy['on_time'].mean() * 100
    else:
        on_time_delivery_rate = 0
        
    # 평균 배송 소요시간 (일수)
    if 'order_delivered_customer_date' in df_copy.columns and 'order_date' in df_copy.columns:
        df_copy['shipping_days'] = (df_copy['order_delivered_customer_date'] - df_copy['order_date']).dt.days
        avg_shipping_time = df_copy['shipping_days'].mean()
    else:
        avg_shipping_time = 0
    
    # 재구매율
    customer_order_counts = df_copy.groupby('customer_unique_id')['order_id'].nunique()
    repeat_customers = (customer_order_counts >= 2).sum()
    total_cust_count = len(customer_order_counts)
    repeat_purchase_rate = (repeat_customers / total_cust_count) * 100 if total_cust_count > 0 else 0
    
    # 고객 평균 평점
    avg_review_score = df_copy.groupby('customer_id')['review_score'].mean().mean()
    
    return {
        'total_amount': total_amount,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'avg_order_value': avg_order_value,
        'total_products': total_products,
        'on_time_delivery_rate': on_time_delivery_rate,
        'avg_shipping_time': avg_shipping_time,
        'repeat_purchase_rate': repeat_purchase_rate,
        'avg_review_score': avg_review_score
    }

def get_comparison_metrics(df, filtered_df):
    """전체 데이터 대비 필터된 데이터 비교"""
    # 전체 데이터 지표
    total_all_sales = df['payment_value'].sum()
    total_all_orders = df['order_id'].nunique()
    total_all_customers = df['customer_unique_id'].nunique()
    
    # 필터된 데이터 지표
    total_filtered_sales = filtered_df['payment_value'].sum()
    total_filtered_orders = filtered_df['order_id'].nunique()
    total_filtered_customers = filtered_df['customer_unique_id'].nunique()
    
    # 비율 계산
    sales_ratio = (total_filtered_sales / total_all_sales) * 100 if total_all_sales > 0 else 0
    orders_ratio = (total_filtered_orders / total_all_orders) * 100 if total_all_orders > 0 else 0
    customers_ratio = (total_filtered_customers / total_all_customers) * 100 if total_all_customers > 0 else 0
    
    return {
        'sales_ratio': sales_ratio,
        'orders_ratio': orders_ratio,
        'customers_ratio': customers_ratio,
        'total_all_sales': total_all_sales,
        'total_filtered_sales': total_filtered_sales
    }

def get_key_metrics_summary(filtered_df):
    """핵심 지표 계산 - Dict 반환"""
    total_sales = filtered_df['payment_value'].sum()
    total_orders = filtered_df['order_id'].nunique()
    total_customers = filtered_df['customer_unique_id'].nunique()
    avg_rating = filtered_df['review_score'].mean()
    total_states = filtered_df['customer_state'].nunique()
    
    # 재구매율 계산
    customer_orders = filtered_df.groupby('customer_unique_id')['order_id'].nunique()
    repeat_rate = ((customer_orders >= 2).sum() / len(customer_orders)) * 100 if len(customer_orders) > 0 else 0
    
    return {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'avg_rating': avg_rating,
        'total_states': total_states,
        'repeat_rate': repeat_rate
    }
