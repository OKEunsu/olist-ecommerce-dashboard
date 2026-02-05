import os
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

@st.cache_data(ttl=3600)
def load_data():
    """
    통합된 단일 데이터 소스(Google Sheets 또는 로컬 CSV)를 로드합니다.
    """
    df = pd.DataFrame()
    
    # 1. Google Sheets 연결 시도
    try:
        # secrets에 설정이 있는지 확인
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            # 단일 시트 'data' (또는 첫 번째 시트) 읽기
            # 사용자가 파일 하나만 올렸으므로 복잡한 로직 불필요
            df = conn.read()  # 기본적으로 첫 번째 시트를 읽음
            
            # 날짜 컬럼 형변환 (CSV/Sheet 로드 시 문자열로 될 수 있음)
            time_cols = ['order_date', 'order_delivered_customer_date', 'order_estimated_delivery_date']
            for col in time_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Geolocation 데이터 분리 (dashboard.py에서 df_geolocation을 따로 요구함)
            # 여기서는 이미 join된 상태이므로, df에서 중복을 제거하여 geo정보만 추출
            df_geolocation = df[['customer_state', 'customer_lat', 'customer_lng']].drop_duplicates().rename(columns={
                'customer_state': 'geolocation_state',
                'customer_lat': 'geolocation_lat', # 차트 호환성 유지
                'customer_lng': 'geolocation_lng'
            })
            
            return df, df_geolocation
            
    except Exception as e:
        # 에러 발생 시 로깅만 하고 로컬 파일로 넘어감
        pass
        
    # 2. 로컬 파일 폴백 (dashboard_mart.csv 사용)
    return load_data_local()

def load_data_local():
    """로컬 dashboard_mart.csv 파일에서 데이터 로드"""
    # 현재 파일 위치: 06_dashboard/utils/db_manager.py
    # 목표 파일 위치: 06_dashboard/dashboard_mart.csv
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "dashboard_mart.csv")
    
    if not os.path.exists(file_path):
        st.error(f"데이터 파일을 찾을 수 없습니다: {file_path}")
        return pd.DataFrame(), pd.DataFrame()
        
    df = pd.read_csv(file_path)
    
    # 날짜 형변환
    time_cols = ['order_date', 'order_delivered_customer_date', 'order_estimated_delivery_date']
    for col in time_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
    # Geo 정보 추출 (unique State list 생성을 위해 필요)
    df_geolocation = df[['customer_state', 'customer_lat', 'customer_lng']].drop_duplicates().rename(columns={
        'customer_state': 'geolocation_state'
    })
    
    return df, df_geolocation

def apply_filters(df, selected_month, selected_state):
    if df.empty: return df
    filtered_df = df.copy()
    
    if selected_month != 'All':
        filtered_df = filtered_df[filtered_df['y_mth'] == selected_month]
        
    if selected_state:
        filtered_df = filtered_df[filtered_df['customer_state'].isin(selected_state)]
        
    return filtered_df
