import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import streamlit as st

def register_fonts():
    # 폰트 파일 경로 찾기
    # 현재 파일의 위치: 06_dashboard/components/pdf_report.py
    # 폰트 위치: 06_dashboard/NanumGothic.ttf
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) # 06_dashboard
    font_path = os.path.join(project_root, 'NanumGothic.ttf')

    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
            return True
        except Exception:
            return False
    return False

def create_pdf_report(df, filtered_df, selected_month, selected_state, current_metrics, prev_metrics, can_compare):
    """
    대시보드 데이터를 PDF 리포트로 생성하는 함수
    """
    # 폰트 등록 시도
    font_registered = register_fonts()
    font_name = 'NanumGothic' if font_registered else 'Helvetica' # Fallback

    # PDF 버퍼 생성
    buffer = io.BytesIO()
    
    # PDF 문서 생성
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # 스타일 설정
    styles = getSampleStyleSheet()
    
    # 커스텀 스타일 추가
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.darkblue
    )
    
    title_text = "Brazilian E-Commerce Dashboard Report" if not font_registered else "Brazilian E-Commerce 대시보드 리포트"

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        spaceAfter=6
    )
    
    # PDF 내용 구성
    story = []
    
    # 1. 제목 및 기본 정보
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 12))
    
    # 리포트 생성 정보
    report_info = f"""
    <b>리포트 생성일:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
    <b>분석 기간:</b> {selected_month if selected_month != 'All' else '전체 기간'}<br/>
    <b>분석 지역:</b> {', '.join(selected_state) if selected_state else '전체 지역'}<br/>
    """
    story.append(Paragraph(report_info, normal_style))
    story.append(Spacer(1, 20))
    
    # 2. 핵심 KPI 요약
    story.append(Paragraph("📊 핵심 성과 지표", heading_style))
    
    # KPI 테이블 데이터 준비
    kpi_data = [
        ['지표', '현재 값', '전월 대비' if can_compare else '상태'],
        ['Total Amount', f"{current_metrics['total_amount']:,.0f} BRL", 
         f"{((current_metrics['total_amount'] - prev_metrics.get('total_amount', 0)) / prev_metrics.get('total_amount', 1) * 100):.1f}%" if can_compare and prev_metrics.get('total_amount', 0) > 0 else 'N/A'],
        ['Total Orders', f"{current_metrics['total_orders']:,}", 
         f"{((current_metrics['total_orders'] - prev_metrics.get('total_orders', 0)) / prev_metrics.get('total_orders', 1) * 100):.1f}%" if can_compare and prev_metrics.get('total_orders', 0) > 0 else 'N/A'],
        ['Total Customers', f"{current_metrics['total_customers']:,}", 
         f"{((current_metrics['total_customers'] - prev_metrics.get('total_customers', 0)) / prev_metrics.get('total_customers', 1) * 100):.1f}%" if can_compare and prev_metrics.get('total_customers', 0) > 0 else 'N/A'],
        ['Aov', f"{current_metrics['avg_order_value']:,.0f} BRL", 
         f"{((current_metrics['avg_order_value'] - prev_metrics.get('avg_order_value', 0)) / prev_metrics.get('avg_order_value', 1) * 100):.1f}%" if can_compare and prev_metrics.get('avg_order_value', 0) > 0 else 'N/A'],
        ['Total Products', f"{current_metrics['total_products']:,}", 
         f"{((current_metrics['total_products'] - prev_metrics.get('total_products', 0)) / prev_metrics.get('total_products', 1) * 100):.1f}%" if can_compare and prev_metrics.get('total_products', 0) > 0 else 'N/A']
    ]
    
    # KPI 테이블 생성
    kpi_table = Table(kpi_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    kpi_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
    ]))
    
    story.append(kpi_table)
    story.append(Spacer(1, 20))
    
    # 3. 운영 지표
    story.append(Paragraph("🚚 운영 성과 지표", heading_style))
    
    operational_data = [
        ['지표', '현재 값', '목표/기준'],
        ['On-time Delivery Rate', f"{current_metrics['on_time_delivery_rate']:.1f}%", f"95% or higher"],
        ['Average Shipping Time', f"{current_metrics['avg_shipping_time']:.1f}days", "Within 7 days"],
        ['Repeat Purchase Rate', f"{current_metrics['repeat_purchase_rate']:.2f}%", "Over 30%"],
        ['Average Review Score', f"{current_metrics['avg_review_score']:.2f}/5", "At least 4.0"]
    ]
    
    operational_table = Table(operational_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    operational_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
    ]))
    
    story.append(operational_table)
    story.append(Spacer(1, 20))

    # PDF 생성
    doc.build(story)
    
    # 버퍼에서 PDF 데이터 가져오기
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def generate_download_button(df, filtered_df, selected_month, selected_state, current_metrics, prev_metrics, can_compare):
    """
    Streamlit에서 사용할 PDF 다운로드 버튼 생성
    """
    try:
        # PDF 생성
        pdf_data = create_pdf_report(
            df, filtered_df, selected_month, selected_state, 
            current_metrics, prev_metrics, can_compare
        )
        
        # 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        month_str = selected_month if selected_month != 'All' else 'all'
        state_str = '_'.join(selected_state[:2]) if selected_state else 'all'
        filename = f"dashboard_report_{month_str}_{state_str}_{timestamp}.pdf"
        
        return pdf_data, filename
        
    except Exception as e:
        st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
        return None, None
