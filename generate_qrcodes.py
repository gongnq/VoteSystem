#!/usr/bin/env python3
"""Generate a PDF with one QR code per A4 page for each group."""

import qrcode
import os
from fpdf import FPDF

# Import groups from app.py
GROUPS = [
    ("G-1",  "1. Echo Frames Reimagined: Your Private AI Assistant for Work, Life & Shopping", "NPI", "Echo Frames Reimagined"),
    ("G-2",  "2. Alexa UI Plus - Fire TV Smart Scene Analysis", "NPI", "Alexa UI Plus"),
    ("G-3",  "3. Pulse ID", "NPI_PRE", "Pulse ID badge"),
    ("G-4",  "4. Re-imagined Wireless Charging for Metal Cover Devices", "NPI", "Re-imagined Wireless Charging"),
    ("G-5",  "5. Story Pal: The AI-Plush That Brings Multilingual Stories to Life", "NPI_PRE", "Amazon Unveils Story Pal"),
    ("G-6",  "6. AI Powered Multimodal E-commerce Product Shooting Camera", "NPI_PRE", "AI Powered Multimodal Camera"),
    ("G-7",  "7. AI Vision Mate Glasses - Second Sight for the Visually Impaired", "NPI", "AI Vision Mate Glasses"),
    ("G-8",  "8. Detachable Flip Camera Module with 360-degree Field for Echo Show Devices", "NPI", "Detachable Flip 360 Camera"),
    ("G-9",  "9. Smart Necklace Transforms Daily Life With AI-Powered Personal Assistant", "NPI_PRE", "Smart Necklace"),
    ("G-10", "10. Chroma Mirror: The AI Stylist That Unlocks Your Most Confident Look", "NPI", "Chroma Mirror"),
    ("G-11", "11. An Inner Spider Speaker Construction for Full Range", "NTI", "Inner Spider Design"),
    ("G-12", "12. Edge to Edge Display Cover Lens", "NTI", "Edge to Edge display cover lens"),
    ("G-13", "13. BOBArtender - AI-Powered Bubble Tea Generation", "NTI", "BOBArtender"),
    ("G-14", "14. The Family AI Cinema Butler: A TV That Knows You and Brings You Together", "NTI", "The Family AI Cinema Butler"),
    ("G-15", "15. Stratos", "NTI", "Stratos: AI Platform"),
    ("G-16", "16. Multi-Modal Competitive Intelligence AI Agent", "NTI", "Multi-Modal AI Agent"),
    ("G-17", "17. Hercules: A Cloud-based AI/ML Platform", "NTI", "Hercules: A Cloud-based AI/ML Platform"),
    ("G-18", "18. Manufacturing Smart Assistant", "NTI", "Manufacturing Smart Assistant"),
    ("G-19", "19. Intelligent Quality: AI-Powered Battery Manufacturing at Scale", "NTI", "Intelligent Quality: AI-Powered"),
    ("G-20", "20. Green Design 1", "NTI", "Green Technology for Sustainablity"),
    ("G-21", "21. Green Design 2: New-to-Industry PCB Technologies of Recyclable Substrate & Additive Manufacturing", "NTI", "Recyclable Substrate PCB Technologies"),
    ("G-22", "22. Echo Holo Assistant", "NPI", "Echo Holo Assistant"),
    ("G-23", "23. Beany: Palm-Sized AI Companion", "NPI_PRE", "Beany: Palm-Sized AI Companion"),
]

DISPLAY_CATEGORY = {"NPI": "NPI", "NPI_PRE": "NPI", "NTI": "NTI"}

# Create temp directory for QR images
tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp_qr')
os.makedirs(tmp_dir, exist_ok=True)

# Generate QR code images
for gid, name, cat, card_name in GROUPS:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=20, border=2)
    qr.add_data(gid)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(os.path.join(tmp_dir, f'{gid}.png'))

# Build PDF - A4: 210 x 297 mm
pdf = FPDF(orientation='P', unit='mm', format='A4')
pdf.set_auto_page_break(auto=False)

for gid, name, cat, card_name in GROUPS:
    pdf.add_page()

    # Category badge at top
    dcat = DISPLAY_CATEGORY[cat]
    pdf.set_font('Helvetica', 'B', 16)
    if dcat == 'NPI':
        pdf.set_text_color(9, 132, 227)
    else:
        pdf.set_text_color(225, 112, 85)
    pdf.cell(0, 12, dcat, align='C')
    pdf.ln(16)

    # Group name - use full voting title, strip leading number
    import re
    display_name = re.sub(r'^\d+\.\s*', '', name)
    # Smaller font for long titles
    font_size = 18 if len(display_name) > 50 else 20
    pdf.set_font('Helvetica', 'B', font_size)
    pdf.set_text_color(30, 30, 50)
    x_margin = 20
    pdf.set_x(x_margin)
    pdf.multi_cell(210 - 2 * x_margin, 9, display_name, align='C')
    pdf.ln(6)

    # QR Code - centered, large (auto-size to fit remaining space)
    remaining = 297 - pdf.get_y() - 40  # leave room for footer
    qr_size = min(150, remaining)
    qr_x = (210 - qr_size) / 2
    qr_path = os.path.join(tmp_dir, f'{gid}.png')
    pdf.image(qr_path, x=qr_x, y=pdf.get_y(), w=qr_size)
    pdf.ln(qr_size + 8)

    # Group ID below QR
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(140, 140, 140)
    pdf.cell(0, 8, f'Scan to vote  |  {gid}', align='C')
    pdf.ln(12)

    # Footer text
    pdf.set_font('Helvetica', 'I', 11)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(0, 8, '2026 Asia Demo Crawl', align='C')

# Save PDF
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'QR_Codes_A4.pdf')
pdf.output(output_path)

# Clean up temp files
import shutil
shutil.rmtree(tmp_dir, ignore_errors=True)

print(f'PDF generated: {output_path}')
print(f'Total pages: {len(GROUPS)}')
