import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def find_font():
    """Find a suitable Chinese font on macOS."""
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Arial Unicode.ttf" 
    ]
    for path in font_paths:
        if os.path.exists(path):
            return path
    return None

def create_pdf_from_txt(txt_path, pdf_path):
    """
    Converts a text file to a PDF, preserving layout and handling Chinese characters.
    """
    font_path = find_font()
    if not font_path:
        print("错误：在系统中找不到可用的中文字体。")
        return

    try:
        # Register the font. For .ttc, we need to specify the font index.
        # PingFang.ttc has several fonts, index 0 is usually the regular one.
        font_name = 'ChineseFont'
        pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=0))

        # Read content from the text file
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Create a document template
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        
        # Create a custom style using our registered font
        # Using Preformatted to preserve all whitespace and line breaks
        custom_style = ParagraphStyle(
            name='PreStyle',
            fontName=font_name,
            fontSize=9,
            leading=11
        )

        # Use Preformatted for the entire block of text to maintain the ASCII art and indentation
        story = [Preformatted(content, custom_style)]

        # Build the PDF
        doc.build(story)
        print(f"成功创建PDF文件: {pdf_path}")

    except Exception as e:
        print(f"创建PDF时发生错误: {e}")

if __name__ == "__main__":
    input_file = "Marketing/未来收益权交易平台演示设计方案第23版.txt"
    output_file = "Marketing/未来收益权交易平台演示设计方案第23版.pdf"
    create_pdf_from_txt(input_file, output_file)
