#!/usr/bin/env python3
"""Generate a PDF instruction guide for the 2026 Asia Demo Crawl voting system."""

from fpdf import FPDF

class InstructionPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, '2026 Asia Demo Crawl - Voting Instructions', align='C')
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


pdf = InstructionPDF()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# Title
pdf.set_font('Helvetica', 'B', 28)
pdf.set_text_color(30, 30, 50)
pdf.cell(0, 20, '2026 Asia Demo Crawl', ln=True, align='C')
pdf.set_font('Helvetica', '', 16)
pdf.set_text_color(108, 92, 231)
pdf.cell(0, 10, 'Judge Voting Instructions', ln=True, align='C')
pdf.ln(15)

# Divider
pdf.set_draw_color(108, 92, 231)
pdf.set_line_width(0.8)
pdf.line(30, pdf.get_y(), 180, pdf.get_y())
pdf.ln(12)

# Step 1
pdf.set_font('Helvetica', 'B', 18)
pdf.set_text_color(108, 92, 231)
pdf.cell(0, 12, 'Step 1: Log In', ln=True)
pdf.set_font('Helvetica', '', 12)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 7, (
    '1. Open the voting app on your tablet or phone.\n'
    '2. Select your name from the dropdown list.\n'
    '3. Tap "Start Voting" to enter the voting dashboard.\n'
    '4. A quick tutorial will appear on your first login.'
))
pdf.ln(8)

# Step 2
pdf.set_font('Helvetica', 'B', 18)
pdf.set_text_color(108, 92, 231)
pdf.cell(0, 12, 'Step 2: Visit a Booth', ln=True)
pdf.set_font('Helvetica', '', 12)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 7, (
    'You have two ways to open a group for voting:\n\n'
    '  Option A: Scan the QR code at the booth using the "Scan QR" button.\n\n'
    '  Option B: Tap the group card directly on your dashboard.\n\n'
    'Listen to the team\'s demo presentation before voting.'
))
pdf.ln(8)

# Step 3
pdf.set_font('Helvetica', 'B', 18)
pdf.set_text_color(108, 92, 231)
pdf.cell(0, 12, 'Step 3: Vote', ln=True)
pdf.set_font('Helvetica', '', 12)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 7, (
    'After the demo, a voting panel will appear with several options.\n\n'
    '  - Tap one or more options to select your vote.\n'
    '  - You can select multiple options per group.\n'
    '  - If the demo is not applicable, you can skip without selecting\n'
    '    any option. The button will show "Skip (Not Applicable)".\n\n'
    'NPI Groups vote options:\n'
    '  - PRFAQ (Product / Feature Maker)\n'
    '  - Customer Delight (Customer Pain Points / Customer Will Love)\n'
    '  - Some groups also have: PRE-ORDER\n\n'
    'NTI Groups vote options:\n'
    '  - Product Concept (Technology Enabler)\n'
    '  - Accelerator (Operational Excellence / AI / Sustainable Energy)\n'
    '  - Think Big (Design for Long Term & Scalable)'
))
pdf.ln(8)

# Step 4
pdf.set_font('Helvetica', 'B', 18)
pdf.set_text_color(108, 92, 231)
pdf.cell(0, 12, 'Step 4: Comment (Optional)', ln=True)
pdf.set_font('Helvetica', '', 12)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 7, (
    'Below the vote options, there is a comment box.\n'
    'You can optionally leave feedback or suggestions for the team.\n'
    'Comments are visible to admins in the dashboard.'
))
pdf.ln(8)

# Step 5
pdf.set_font('Helvetica', 'B', 18)
pdf.set_text_color(108, 92, 231)
pdf.cell(0, 12, 'Step 5: Submit', ln=True)
pdf.set_font('Helvetica', '', 12)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 7, (
    'Tap the green "Submit Vote" button (or "Skip (Not Applicable)").\n'
    'The group card on your dashboard will turn green with a checkmark.\n'
    'Your progress bar at the top will update accordingly.'
))
pdf.ln(8)

# Important Notes
pdf.set_font('Helvetica', 'B', 18)
pdf.set_text_color(225, 112, 85)
pdf.cell(0, 12, 'Important Notes', ln=True)
pdf.set_font('Helvetica', '', 12)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 7, (
    '- PRFAQ Limit: You can only select PRFAQ for up to 4 groups total.\n'
    '  The counter is shown at the top of your dashboard.\n\n'
    '- You can change your vote by tapping a group card again.\n\n'
    '- When you finish all 21 groups, a celebration animation will appear!\n\n'
    '- If you need to leave, tap "Logout" in the top-right corner.\n'
    '  Your votes are saved and you can log back in later.'
))

# Save
output_path = '/Volumes/workplace/VoteSystem/Judge_Voting_Instructions.pdf'
pdf.output(output_path)
print(f'PDF generated: {output_path}')
