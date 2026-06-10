import pandas as pd
import json
import io
import base64
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors

def rows_to_df(rows):
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)

def export_excel(rows, file_stem):
    df = rows_to_df(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
        worksheet = writer.sheets['Sheet1']
        import openpyxl
        fill = openpyxl.styles.PatternFill(fgColor="C2571A", fill_type="solid")
        font = openpyxl.styles.Font(color="FFFFFF", bold=True)
        for cell in worksheet[1]:
            cell.fill = fill
            cell.font = font
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value or "")) > max_length:
                        max_length = len(str(cell.value or ""))
                except:
                    pass
            adjusted_width = min(max_length + 4, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
            
    buffer.seek(0)
    return buffer.getvalue(), f"{file_stem}_cleaned.xlsx"

def export_json(rows, file_stem):
    json_data = json.dumps(rows, default=str, indent=2)
    return json_data.encode('utf-8'), f"{file_stem}_cleaned.json"

def export_parquet(rows, file_stem):
    df = rows_to_df(rows)
    buffer = io.BytesIO()
    try:
        # PyArrow requires strict typing. Convert object columns to string to prevent ArrowInvalid errors.
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)
                
        df.to_parquet(buffer, index=False, engine="pyarrow")
    except ImportError as e:
        raise e
    buffer.seek(0)
    return buffer.getvalue(), f"{file_stem}_cleaned.parquet"

def export_pdf(rows, summary, ai_result, charts_b64, file_stem):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=40)
    story = []
    
    # Section 1: Cover Header
    header_style = ParagraphStyle(name="CoverHeader", fontSize=28, fontName="Helvetica-Bold", textColor=colors.HexColor("#C2571A"))
    story.append(Paragraph("DataLens AI", header_style))
    story.append(Spacer(1, 10))
    
    styles = getSampleStyleSheet()
    subtitle_style = styles["Heading2"]
    story.append(Paragraph(f"{file_stem}", subtitle_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y')}", styles["Normal"]))
    story.append(Spacer(1, 20))
    
    # Section 2: Dataset Overview Table
    overview_data = [
        ["Total Rows", str(summary.get("rows", 0))],
        ["Total Columns", str(summary.get("cols", 0))],
        ["Missing Values", str(summary.get("null_total", 0))],
        ["Duplicate Rows", str(summary.get("duplicate_rows", 0))],
        ["Memory (KB)", str(summary.get("memory_kb", 0))],
        ["Data Quality Score", str(ai_result.get("quality_score", "N/A"))]
    ]
    
    overview_table = Table(overview_data, colWidths=[200, 200])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor("#FAF7F2"), colors.white]),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E8DDD0")),
    ]))
    
    story.append(overview_table)
    story.append(Spacer(1, 20))
    
    # Section 3: AI insights
    if "key_insights" in ai_result and ai_result["key_insights"]:
        story.append(Paragraph("AI Insights", styles["Heading2"]))
        for insight in ai_result["key_insights"]:
            story.append(Paragraph(f"• {insight}", styles["Normal"]))
        story.append(Spacer(1, 10))
        
    if "cleaning_steps" in ai_result and ai_result["cleaning_steps"]:
        story.append(Paragraph("Recommended cleaning steps", styles["Heading3"]))
        for i, step in enumerate(ai_result["cleaning_steps"], 1):
            story.append(Paragraph(f"{i}. {step}", styles["Normal"]))
        story.append(Spacer(1, 20))
        
    # Section 4: Charts
    if charts_b64:
        story.append(Paragraph("Charts", styles["Heading2"]))
        for key, b64_string in charts_b64.items():
            if not b64_string:
                continue
            try:
                img_data = base64.b64decode(b64_string)
                img_buffer = io.BytesIO(img_data)
                img = Image(img_buffer, width=440, height=240)
                img.preserveAspectRatio = True
                story.append(img)
                story.append(Spacer(1, 5))
                story.append(Paragraph(key.capitalize(), styles["Italic"]))
                story.append(Spacer(1, 15))
            except Exception:
                pass
                
    # Section 5: Data sample table
    df = rows_to_df(rows)
    if not df.empty:
        story.append(Paragraph("Data Sample", styles["Heading2"]))
        df_head = df.head(20).copy()
        
        for col in df_head.columns:
            df_head[col] = df_head[col].astype(str).apply(lambda x: x[:30] + "..." if len(x) > 30 else x)
            
        sample_data = [df_head.columns.tolist()] + df_head.values.tolist()
        
        sample_table = Table(sample_data)
        sample_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#C2571A")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#FAF7F2"), colors.white]),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E8DDD0")),
        ]))
        story.append(sample_table)
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Showing first {len(df_head)} rows of {len(df)} total", styles["Italic"]))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue(), f"{file_stem}_report.pdf"
