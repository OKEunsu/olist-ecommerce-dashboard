import os
import pandas as pd

def create_dashboard_mart():
    print("🚀 데이터 최적화 작업을 시작합니다...")
    
    # 1. 파일 경로 설정
    # 06_dashboard/utils/create_mart.py 위치 기준
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "00_cleand_data")
    output_path = os.path.join(base_dir, "06_dashboard", "dashboard_mart.csv")

    if not os.path.exists(data_dir):
        print(f"❌ 데이터 폴더를 찾을 수 없습니다: {data_dir}")
        return

    # 2. 데이터 로드 (필요한 컬럼만 로드하여 메모리 절약)
    try:
        print("📥 원본 데이터를 읽는 중...")
        orders = pd.read_csv(os.path.join(data_dir, "orders.csv"))
        items = pd.read_csv(os.path.join(data_dir, "order_items.csv"))
        products = pd.read_csv(os.path.join(data_dir, "products.csv"))
        reviews = pd.read_csv(os.path.join(data_dir, "order_reviews.csv"))
        customers = pd.read_csv(os.path.join(data_dir, "customers.csv"))
        # sellers - 대시보드 KPI에 직접 안쓰이므로 제외 가능
        geo = pd.read_csv(os.path.join(data_dir, "geolocation.csv"))
        cat_trans = pd.read_csv(os.path.join(data_dir, "product_category_name_translation.csv"))

        # 3. 데이터 병합 (Merge)
        print("🔄 데이터를 하나로 합치는 중...")
        
        # Orders 기본 전처리
        orders = orders.rename(columns={'order_purchase_timestamp': 'order_date'})
        
        # Order + Items
        df = items.merge(orders[['order_id', 'customer_id', 'order_date', 'order_approved_at', 
                               'order_delivered_customer_date', 'order_estimated_delivery_date']], 
                       on='order_id', how='inner')

        # + Products
        products = products.merge(cat_trans, on='product_category_name', how='left')
        df = df.merge(products[['product_id', 'product_category_name_english']], on='product_id', how='left')
        
        # 영문 카테고리명 보정
        if 'product_category_name_english' in df.columns:
             df['product_category_name'] = df['product_category_name_english'].fillna('Others')
        else:
             df['product_category_name'] = 'Others'

        # + Customers
        df = df.merge(customers[['customer_id', 'customer_unique_id', 'customer_zip_code_prefix', 'customer_city', 'customer_state']], 
                    on='customer_id', how='left')

        # + Reviews (평균 평점만)
        rv_agg = reviews.groupby('order_id')['review_score'].mean().reset_index()
        df = df.merge(rv_agg, on='order_id', how='left')

        # + Geolocation (Zipcode 기준 중복 제거 후 병합)
        geo_agg = geo.groupby('geolocation_zip_code_prefix')[['geolocation_lat', 'geolocation_lng']].first().reset_index()
        df = df.merge(geo_agg, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix', how='left')

        # 4. 파생 변수 생성 및 컬럼 정리
        print("✂️ 불필요한 데이터를 잘라내는 중...")
        
        # 매출액 (가격 + 배송비)
        df['payment_value'] = df['price'] + df['freight_value']
        
        # 연월 컬럼
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['y_mth'] = df['order_date'].dt.strftime('%Y-%m')
        
        # 기간 필터링 (2017-01 ~ 2018-08)
        df = df[(df['y_mth'] >= '2017-01') & (df['y_mth'] <= '2018-08')]

        # 최종 저장할 컬럼만 선택
        final_columns = [
            'order_id', 
            'order_date', 
            'y_mth',
            'order_delivered_customer_date',
            'order_estimated_delivery_date',
            'customer_unique_id',
            'customer_state',
            'geolocation_lat',  # customer_lat
            'geolocation_lng',  # customer_lng
            'product_id',
            'product_category_name',
            'payment_value',
            'review_score'
        ]
        
        # 컬럼 이름 깔끔하게 변경
        rename_map = {
            'geolocation_lat': 'customer_lat',
            'geolocation_lng': 'customer_lng'
        }
        
        result_df = df[final_columns].rename(columns=rename_map)
        
        # 5. CSV 저장
        print(f"💾 파일 저장 중... ({len(result_df)} rows)")
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig') # 한글/특수문자 대비 utf-8-sig
        
        print(f"✅ 성공! 통합 데이터 파일이 생성되었습니다: {output_path}")
        print(f"   --> 이 파일만 구글 시트에 올리시면 됩니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    create_dashboard_mart()
