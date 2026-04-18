from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from enum import Enum
from pptx.enum.text import PP_ALIGN

def apply_blue_background(slide):
    """
    Applies a solid blue background to the slide. 
    """
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(0, 102, 204) # A professional blue

def set_font_times_new_roman(shape):
    """
    Recursively sets the font of all text in a shape to Times New Roman.
    """
    if shape.has_text_frame:
        for paragraph in shape.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.name = 'Times New Roman'
            # Also set it for the paragraph level if runs aren't created yet
            paragraph.font.name = 'Times New Roman'

def create_presentation():
    # Create a presentation object
    prs = Presentation()

    # --- SLIDE 1: Lionel Messi ---
    blank_slide_layout = prs.slide_layouts[6]
    slide1 = prs.slides.add_slide(blank_slide_layout)
    apply_blue_background(slide1)

    # Title 1
    txBox1 = slide1.shapes.add_textbox(Pt(50), Pt(50), Pt(600), Pt(100))
    tf1 = txBox1.text_frame
    p1 = tf1.paragraphs[0]
    p1.text = "Lionel Messi"
    p1.font.name = 'Times New Roman'
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    p1.alignment = PP_ALIGN.CENTER

    # Content 1
    contentBox1 = slide1.shapes.add_textbox(Pt(50), Pt(150), Pt(600), Pt(400))
    contentFrame1 = contentBox1.text_frame
    contentFrame1.word_wrap = True

    bullets1 = [
        "Widely regarded as one of the greatest football players of all time, Lionel Messi is known for his extraordinary dribbling, vision, and scoring ability.",
        "Born in Rosario, Argentina, he overcame a growth hormone deficiency as a child to join FC Barcelona's youth academy, La Masia, which shaped his legendary career.",
        "During his tenure at Barcelona, he won numerous La Liga titles and four UEFA Champions League trophies, becoming the club's all-time leading goalscorer.",
        "Messi has achieved a record-breaking number of Ballon d'Or awards, cementing his status as a dominant force in world football for nearly two decades.",
        "His career reached a pinnacle in 2022 when he captained Argentina to victory in the FIFA World Cup, winning the Golden Ball as the tournament's best player.",
        "Known for his humility and loyalty, he spent the majority of his professional life at one club before moving to Paris Saint-Germain and later Inter Miami CF.",
        "His playstyle is characterized by a low center of gravity, allowing him to change direction rapidly and weave through defenders with ease.",
        "Beyond scoring, his playmaking skills and ability to provide assists make him a complete offensive threat on the pitch."
    ]

    for point in bullets1:
        p = contentFrame1.add_paragraph()
        p.text = point
        p.font.name = 'Times New Roman'
        p.font.size = Pt(18)
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.level = 0

    # --- SLIDE 2: Sachin Tendulkar ---
    slide2 = prs.slides.add_slide(blank_slide_layout)
    apply_blue_background(slide2)

    # Title 2
    txBox2 = slide2.shapes.add_textbox(Pt(50), Pt(50), Pt(600), Pt(100))
    tf2 = txBox2.text_frame
    p2 = tf2.paragraphs[0]
    p2.text = "Sachin Tendulkar"
    p2.font.name = 'Times New Roman'
    p2.font.size = Pt(44)
    p2.font.bold = True
    p2.font.color.rgb = RGBColor(255, 255, 255)
    p2.alignment = PP_ALIGN.CENTER

    # Content 2
    contentBox2 = slide2.shapes.add_textbox(Pt(50), Pt(150), Pt(600), Pt(400))
    contentFrame2 = contentBox2.text_frame
    contentFrame2.word_wrap = True

    bullets2 = [
        "Sachin Tendulkar, often referred to as the 'God of Cricket', is widely considered one of the greatest batsmen in the history of the sport.",
        "Hailing from Mumbai, India, he made his international debut at the tender age of 16, showing maturity and skill far beyond his years.",
        "He holds the record for the most runs in both Test and One Day International (ODI) cricket, demonstrating unparalleled consistency over two decades.",
        "Tendulkar is the only player in the history of the game to have scored one hundred international centuries, a feat that remains a benchmark of excellence.",
        "His technical perfection, particularly his straight drive, became a symbol of classical batting and inspired millions of aspiring cricketers worldwide.",
        "Throughout his career, he carried the immense expectations of a billion people, maintaining a level of professionalism and humility that earned him global respect.",
        "He played a pivotal role in India's victory in the 2011 ICC Cricket World Cup, fulfilling a lifelong dream and bringing glory to his nation.",
        "His longevity in the sport is legendary, having played at the highest level from 1989 until his retirement in 2013, leaving an indelible mark on the game."
    ]

    for point in bullets2:
        p = contentFrame2.add_paragraph()
        p.text = point
        p.font.name = 'Times New Roman'
        p.font.size = Pt(18)
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.level = 0

    # Final pass to ensure all shapes in all slides are Times New Roman
    for slide in prs.slides:
        for shape in slide.shapes:
            set_font_times_new_roman(shape)

    # Save the presentation
    file_name = "greatest_players.pptx"
    prs.save(file_name)
    print(f"Presentation saved as {file_name}")

if __name__ == "__main__":
    create_presentation()
