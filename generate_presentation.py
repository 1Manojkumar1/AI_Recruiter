#!/usr/bin/env python3
"""
generate_presentation.py - Generates a technical presentation PDF
for the Redrob AI Challenge submission.

Usage:
    python generate_presentation.py
    python generate_presentation.py --out presentation.pdf
"""

import argparse
from pathlib import Path

try:
    from fpdf import FPDF
except ImportError:
    print("Installing fpdf2...")
    import subprocess
    subprocess.check_call(["pip", "install", "fpdf2"])
    from fpdf import FPDF


class PresentationPDF(FPDF):
    """Custom PDF class for the hackathon presentation."""

    SLIDE_W = 297  # A4 landscape width (mm)
    SLIDE_H = 210  # A4 landscape height (mm)

    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)
        self.slide_num = 0

    def new_slide(self):
        """Add a new blank slide."""
        self.slide_num += 1
        self.add_page()
        # Light background
        self.set_fill_color(255, 255, 255)
        self.rect(0, 0, self.SLIDE_W, self.SLIDE_H, "F")
        # Top accent bar
        self.set_fill_color(30, 64, 175)  # Blue-600
        self.rect(0, 0, self.SLIDE_W, 4, "F")
        # Bottom bar with page number
        self.set_fill_color(240, 240, 240)
        self.rect(0, self.SLIDE_H - 12, self.SLIDE_W, 12, "F")
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.set_xy(10, self.SLIDE_H - 10)
        self.cell(0, 8, f"AI Recruiter - Redrob Hackathon Submission  |  Slide {self.slide_num}", align="L")

    def slide_title(self, title, subtitle=None):
        """Add a title to the current slide."""
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(30, 64, 175)
        self.set_xy(20, 18)
        self.cell(0, 14, title)
        if subtitle:
            self.set_font("Helvetica", "", 14)
            self.set_text_color(80, 80, 80)
            self.set_xy(20, 36)
            self.cell(0, 8, subtitle)
        # Divider line
        self.set_draw_color(30, 64, 175)
        self.set_line_width(0.5)
        y_line = 48 if subtitle else 38
        self.line(20, y_line, self.SLIDE_W - 20, y_line)

    def body_text(self, x, y, w, h, text, size=11, bold=False, color=(40, 40, 40)):
        """Add body text block."""
        self.set_font("Helvetica", "B" if bold else "", size)
        self.set_text_color(*color)
        self.set_xy(x, y)
        self.multi_cell(w, h, text)

    def bullet_list(self, x, y, w, items, size=11, spacing=7):
        """Add a bulleted list."""
        self.set_font("Helvetica", "", size)
        self.set_text_color(40, 40, 40)
        for i, item in enumerate(items):
            self.set_xy(x, y + i * spacing)
            self.cell(5, spacing, "-")  # bullet char
            self.cell(w - 5, spacing, f"  {item}")

    def key_value_table(self, x, y, w, rows, col_widths=None, header=True, size=10):
        """Draw a simple table with variable columns."""
        if not rows:
            return

        num_cols = len(rows[0])
        if col_widths is None:
            col_w = w / num_cols
            col_widths = [col_w] * num_cols

        row_h = 8
        for i, row in enumerate(rows):
            curr_y = y + i * row_h
            # Alternating row colors
            if i % 2 == 0:
                self.set_fill_color(245, 247, 250)
            else:
                self.set_fill_color(255, 255, 255)
            self.rect(x, curr_y, w, row_h, "F")

            if header and i == 0:
                self.set_font("Helvetica", "B", size)
                self.set_fill_color(30, 64, 175)
                self.rect(x, curr_y, w, row_h, "F")
                self.set_text_color(255, 255, 255)
            else:
                self.set_font("Helvetica", "B" if i == 0 and header else "", size)
                self.set_text_color(40, 40, 40)

            # Draw each column
            x_offset = x + 2
            for j, cell_val in enumerate(row):
                col_w = col_widths[j] if j < len(col_widths) else col_widths[-1]
                self.set_xy(x_offset, curr_y)
                self.cell(col_w - 2, row_h, str(cell_val))
                x_offset += col_w

    def code_block(self, x, y, w, h, code, size=9):
        """Draw a code block with grey background."""
        self.set_fill_color(30, 30, 30)
        self.rect(x, y, w, h, "F")
        self.set_font("Courier", "", size)
        self.set_text_color(200, 220, 255)
        self.set_xy(x + 4, y + 3)
        self.multi_cell(w - 8, 4.5, code)


def build_presentation(out_path: str):
    """Build the full presentation."""
    pdf = PresentationPDF()

    # ================================================================
    # SLIDE 1: Title
    # ================================================================
    pdf.new_slide()
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(30, 64, 175)
    pdf.set_xy(20, 60)
    pdf.cell(0, 16, "AI Recruiter")
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(80, 80, 80)
    pdf.set_xy(20, 80)
    pdf.cell(0, 10, "Intelligent Candidate Discovery & Ranking System")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_xy(20, 100)
    pdf.cell(0, 8, "Redrob Hackathon Submission")
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(120, 120, 120)
    pdf.set_xy(20, 115)
    pdf.cell(0, 8, "Multi-factor scoring  |  Semantic embeddings  |  Explainable AI  |  Trap detection")

    # ================================================================
    # SLIDE 2: Problem Statement
    # ================================================================
    pdf.new_slide()
    pdf.slide_title("Problem Statement", "Why keyword matching fails in recruitment")

    problems = [
        "Recruiters miss good candidates because keyword filters can't see what matters",
        "A perfect-on-paper profile may be inactive (5% response rate, no login in 6 months)",
        "The dataset contains deliberate traps: keyword stuffers, non-tech roles with AI skills listed,",
        "  honeypots with impossible career timelines, consulting-only backgrounds",
        "The right answer is NOT 'find candidates with the most AI keywords'",
        "We need to understand WHO FITS, not just who matches words",
    ]
    pdf.bullet_list(20, 55, 250, problems, size=12, spacing=10)

    # Key insight box
    pdf.set_fill_color(239, 246, 255)  # Blue-50
    pdf.rect(20, 125, 257, 30, "F")
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 64, 175)
    pdf.set_xy(25, 128)
    pdf.cell(0, 8, "Key Insight:")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)
    pdf.set_xy(25, 138)
    pdf.multi_cell(247, 6,
        "A Tier 5 candidate who built a recommendation system at a product company is a better fit "
        "than a Marketing Manager who lists 'RAG' as a skill. Behavioral signals matter more than profile keywords.")

    # ================================================================
    # SLIDE 3: Architecture
    # ================================================================
    pdf.new_slide()
    pdf.slide_title("Architecture Overview", "Two-stage ranking pipeline with multi-factor scoring")

    # Draw architecture boxes
    boxes = [
        (20, 55, 50, 18, "candidates.jsonl\n100K profiles", (220, 237, 255)),
        (85, 55, 55, 18, "Candidate Processing\nPipeline (Part 1)", (220, 245, 220)),
        (155, 55, 55, 18, "processed_candidates\n.jsonl (enriched)", (220, 237, 255)),
        (20, 85, 50, 18, "Job Description\nText", (255, 243, 224)),
        (85, 85, 55, 18, "JD Parser +\nEmbedding Service", (255, 243, 224)),
        (155, 85, 55, 18, "Stage 1: Fast Filter\nMetadata (Top 500)", (255, 228, 225)),
        (20, 115, 55, 18, "Stage 2: Re-rank\nSemantic (Top 100)", (225, 245, 225)),
        (90, 115, 55, 18, "Multi-Factor Scoring\n6 dimensions", (239, 246, 255)),
        (160, 115, 55, 18, "submission.csv\n100 ranked", (220, 237, 255)),
        (230, 85, 48, 18, "Explainable AI\n(Part 4)", (245, 237, 255)),
    ]

    for x, y, w, h, text, color in boxes:
        pdf.set_fill_color(*color)
        pdf.rect(x, y, w, h, "F")
        pdf.set_draw_color(180, 180, 180)
        pdf.rect(x, y, w, h, "D")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(40, 40, 40)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            pdf.set_xy(x + 2, y + 2 + i * 5)
            pdf.cell(w - 4, 5, line, align="C")

    # Arrows (simplified)
    pdf.set_draw_color(100, 100, 100)
    pdf.set_line_width(0.4)
    arrows = [
        (70, 64, 85, 64),   # candidates -> processing
        (140, 64, 155, 64),  # processing -> processed
        (45, 73, 45, 85),    # candidates -> jd
        (112, 73, 112, 85),  # processing -> jd parser
        (210, 73, 210, 85),  # processed -> stage 1
        (183, 94, 183, 115), # stage 1 -> stage 2
        (112, 133, 90, 133), # stage 2 -> multi-factor
        (145, 133, 160, 133), # multi-factor -> submission
        (190, 94, 230, 94),  # processed -> explainable
    ]
    for x1, y1, x2, y2 in arrows:
        pdf.line(x1, y1, x2, y2)

    # Description
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.set_xy(20, 145)
    pdf.multi_cell(257, 5,
        "Two-stage design: Stage 1 uses fast metadata signals (skills, experience, seniority) to filter "
        "100K candidates down to 500. Stage 2 generates sentence-transformer embeddings ONLY for those "
        "500 candidates and re-ranks using semantic similarity. This fits within the 5-minute CPU budget.")

    # ================================================================
    # SLIDE 4: Scoring Dimensions
    # ================================================================
    pdf.new_slide()
    pdf.slide_title("Scoring Dimensions", "6-factor weighted composite score")

    rows = [
        ["Dimension", "Weight", "What It Measures"],
        ["Skill Match", "30%", "Exact + related skill coverage with fuzzy matching (60+ aliases, 30+ synonym groups)"],
        ["Semantic Similarity", "22%", "Cosine similarity of sentence-transformer embeddings (384-dim MiniLM-L6-v2)"],
        ["Experience Alignment", "18%", "Years vs requirement, seniority trajectory, leadership depth"],
        ["Platform Activity", "12%", "Redrob behavioral signals: response rate, open-to-work, recruiter engagement"],
        ["Achievement Score", "10%", "Leadership keywords, impact metrics, promotions, patents, publications"],
        ["Education Score", "8%", "Institution tier (1-4), degree level bonus, field relevance"],
    ]
    pdf.key_value_table(20, 55, 257, rows, col_widths=[60, 25, 172], size=10)

    # Formula
    pdf.set_fill_color(245, 247, 250)
    pdf.rect(20, 130, 257, 25, "F")
    pdf.set_font("Courier", "B", 10)
    pdf.set_text_color(30, 64, 175)
    pdf.set_xy(25, 133)
    pdf.cell(0, 6, "final_score = (skill x 0.30 + semantic x 0.22 + experience x 0.18 +")
    pdf.set_xy(25, 141)
    pdf.cell(0, 6, "                 platform x 0.12 + achievement x 0.10 + education x 0.08) x 100")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.set_xy(20, 160)
    pdf.cell(0, 6, "Weights are configurable via API. All weights validated to sum to 1.0 at runtime.")

    # ================================================================
    # SLIDE 5: Skill Matching
    # ================================================================
    pdf.new_slide()
    pdf.slide_title("Skill Matching Intelligence", "Beyond exact string matching")

    features = [
        "60+ alias mappings: 'py' -> Python, 'k8s' -> Kubernetes, 'tf' -> TensorFlow",
        "30+ synonym groups: Flask~FastAPI~Django, React~Angular~Vue, AWS~GCP~Azure",
        "Fuzzy matching with strength scoring: exact=1.0, related=0.5, none=0.0",
        "Proficiency weighting: expert=1.0, advanced=0.85, intermediate=0.65, beginner=0.4",
        "Endorsement scaling (capped at 50) + duration weighting (months used)",
        "Required skills weighted 70%, preferred skills weighted 30%",
    ]
    pdf.bullet_list(20, 55, 257, features, size=11, spacing=9)

    # Example
    pdf.set_fill_color(245, 247, 250)
    pdf.rect(20, 120, 257, 45, "F")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 64, 175)
    pdf.set_xy(25, 123)
    pdf.cell(0, 6, "Example: JD requires 'RAG' + 'vector database'")
    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(40, 40, 40)
    examples = [
        'Candidate A: skills=[{"name":"RAG","prof":"expert","endor":45,"dur":36}]',
        '  -> exact match on RAG, expert level, high endorsements -> score 1.0',
        'Candidate B: skills=[{"name":"Pinecone","prof":"advanced","endor":20,"dur":24}]',
        '  -> related match (vector DB group), advanced level -> score 0.5',
        'Candidate C: skills=[{"name":"Photoshop","prof":"intermediate"}]',
        '  -> no match in any synonym group -> score 0.0',
    ]
    for i, line in enumerate(examples):
        pdf.set_xy(25, 133 + i * 5)
        pdf.cell(247, 5, line)

    # ================================================================
    # SLIDE 6: Semantic Similarity
    # ================================================================
    pdf.new_slide()
    pdf.slide_title("Semantic Similarity", "Understanding meaning, not just keywords")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)
    pdf.set_xy(20, 55)
    pdf.multi_cell(257, 6,
        "Uses sentence-transformers (all-MiniLM-L6-v2) to generate 384-dimensional embeddings "
        "for both the job description and candidate profiles. Cosine similarity captures semantic "
        "meaning beyond keyword matching.")

    features = [
        "Model: all-MiniLM-L6-v2 (384-dim, fast, high quality)",
        "Candidate text: concatenates headline, summary, titles, descriptions, skills, domains",
        "Text truncated to 2000 chars to control embedding quality",
        "Fallback: If sentence-transformers unavailable, uses random-projection of bag-of-words",
        "  (same 384-dim output, deterministic, compatible scoring)",
        "Batch processing for efficiency (128 candidates per batch)",
    ]
    pdf.bullet_list(20, 80, 257, features, size=10, spacing=8)

    # Why it matters box
    pdf.set_fill_color(239, 246, 255)
    pdf.rect(20, 140, 257, 30, "F")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 64, 175)
    pdf.set_xy(25, 143)
    pdf.cell(0, 6, "Why it matters:")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.set_xy(25, 151)
    pdf.multi_cell(247, 5,
        "A candidate who describes 'building a recommendation system with embeddings and vector search' "
        "will have high semantic similarity to a JD asking for 'RAG + vector DB experience', even if "
        "they never use the exact words 'RAG' or 'Pinecone'.")

    # ================================================================
    # SLIDE 7: Trap Detection
    # ================================================================
    pdf.new_slide()
    pdf.slide_title("Trap & Honeypot Detection", "Defending against dataset traps")

    # Three columns
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 64, 175)
    pdf.set_xy(20, 55)
    pdf.cell(80, 8, "Non-Tech Penalty (-80pts)")

    pdf.set_xy(110, 55)
    pdf.cell(80, 8, "Consulting Penalty (-50pts)")

    pdf.set_xy(200, 55)
    pdf.cell(80, 8, "Honeypot Detection (-100pts)")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)

    non_tech = [
        "Title contains: marketing,",
        "sales, HR, accountant, civil",
        "engineer, mechanical, support,",
        "writer, scrum master, analyst",
    ]
    for i, t in enumerate(non_tech):
        pdf.set_xy(20, 65 + i * 5)
        pdf.cell(80, 5, t)

    consulting = [
        "All career history at:",
        "TCS, Infosys, Wipro, Accenture,",
        "Cognizant, Capgemini",
        "(product company exp required)",
    ]
    for i, t in enumerate(consulting):
        pdf.set_xy(110, 65 + i * 5)
        pdf.cell(80, 5, t)

    honeypot = [
        "Expert proficiency in 3+ skills",
        "with 0 months duration",
        "OR single role duration >",
        "total years of experience",
    ]
    for i, t in enumerate(honeypot):
        pdf.set_xy(200, 65 + i * 5)
        pdf.cell(80, 5, t)

    # Detection flow
    pdf.set_fill_color(254, 226, 226)  # Red-50
    pdf.rect(20, 90, 257, 60, "F")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(185, 28, 28)
    pdf.set_xy(25, 93)
    pdf.cell(0, 6, "Detection Flow:")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    flow = [
        "1. Title scan: Extract current_title, check against non-tech keyword list",
        "2. Career history scan: Check if ALL roles are at consulting firms (no product company)",
        "3. Honeypot scan: Parse skills for expert+0 duration combos, check career timeline consistency",
        "4. Penalty application: Non-tech=-80, Consulting=-50, Honeypot=-100 (clamped to 0)",
        "5. Verification scan: run_verification.py checks top-100 for traps before submission",
    ]
    for i, line in enumerate(flow):
        pdf.set_xy(25, 103 + i * 8)
        pdf.cell(247, 8, line)

    # ================================================================
    # SLIDE 8: Platform Signals
    # ================================================================
    pdf.new_slide()
    pdf.slide_title("Platform Behavioral Signals", "Redrob's 23 behavioral signals")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)
    pdf.set_xy(20, 55)
    pdf.multi_cell(257, 6,
        "Beyond static profile data, Redrob provides 23 behavioral signals that capture "
        "real candidate engagement. These are extracted and normalized into 4 sub-scores.")

    rows = [
        ["Sub-Score", "Weight", "Signals Used"],
        ["Engagement", "25%", "Response rate, response time, interview completion, application volume"],
        ["Visibility", "25%", "Profile completeness, recruiter saves, search appearances"],
        ["Credibility", "25%", "Email/phone verification, GitHub activity, endorsements, connections"],
        ["Availability", "25%", "Open-to-work flag, notice period, offer acceptance rate"],
    ]
    pdf.key_value_table(20, 75, 257, rows, col_widths=[50, 25, 182], size=10)

    # Why it matters
    pdf.set_fill_color(254, 243, 199)  # Yellow-50
    pdf.rect(20, 130, 257, 35, "F")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(180, 130, 0)
    pdf.set_xy(25, 133)
    pdf.cell(0, 6, "Why this matters:")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.set_xy(25, 142)
    pdf.multi_cell(247, 6,
        "A perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% recruiter "
        "response rate is, for hiring purposes, not actually available. Platform signals capture "
        "this reality and down-weight inactive candidates regardless of profile quality.")

    # ================================================================
    # SLIDE 9: Results
    # ================================================================
    pdf.new_slide()
    pdf.slide_title("Results & Validation", "Submission quality metrics")

    rows = [
        ["Metric", "Status"],
        ["Submission format", "PASS - 100 rows, ranks 1-100, scores non-increasing"],
        ["Official validator", "PASS - validate_submission.py returns 'Submission is valid'"],
        ["Ranking pipeline", "PASS - rank.py runs end-to-end, produces valid CSV"],
        ["Unit tests", "PASS - pytest backend/tests"],
        ["Honeypot scan", "PASS - run_verification.py scans top-100 for traps"],
        ["Compute budget", "PASS - ~2-3 min on CPU, <8GB RAM, no GPU, no network"],
        ["Traps in dataset", "Handled - non-tech penalties, honeypot detection, consulting filter"],
    ]
    pdf.key_value_table(20, 55, 257, rows, col_widths=[70, 187], size=10)

    # Key stats
    pdf.set_fill_color(239, 246, 255)
    pdf.rect(20, 135, 257, 35, "F")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 64, 175)
    pdf.set_xy(25, 138)
    pdf.cell(0, 6, "Key Stats:")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    stats = [
        "Candidates processed: 100,000 | Embedding model: all-MiniLM-L6-v2 (384-dim)",
        "Skill aliases: 60+ | Synonym groups: 30+ | Scoring dimensions: 6 | Weights: configurable",
        "Explanation engine: Template-based NLG (no external API calls, fully offline)",
    ]
    for i, s in enumerate(stats):
        pdf.set_xy(25, 148 + i * 6)
        pdf.cell(247, 6, s)

    # ================================================================
    # SLIDE 10: Compute & Design Decisions
    # ================================================================
    pdf.new_slide()
    pdf.slide_title("Compute Compliance & Design Decisions", "Meeting hackathon constraints")

    # Compute table
    rows = [
        ["Constraint", "Required", "Our Implementation"],
        ["Time", "<= 5 min", "~2-3 min (two-stage filtering reduces embedding computation)"],
        ["Memory", "<= 16 GB", "~4-8 GB (lazy loading, embeddings computed on-demand)"],
        ["CPU only", "No GPU", "All scoring is numpy-vectorized, no GPU needed"],
        ["No network", "No API calls", "sentence-transformers runs locally, no external LLM calls"],
    ]
    pdf.key_value_table(20, 50, 257, rows, col_widths=[50, 40, 167], size=9)

    # Design decisions
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 64, 175)
    pdf.set_xy(20, 100)
    pdf.cell(0, 8, "Key Design Decisions:")

    decisions = [
        "Multi-factor > pure embeddings: Embeddings alone can't distinguish keyword stuffers from real builders",
        "Two-stage ranking: Metadata filter (fast) + semantic re-rank (accurate) = within budget",
        "Template NLG > LLM API: Deterministic, auditable, works offline, no compute penalty",
        "Platform signals: Behavioral data captures availability that static profiles miss",
        "FAISS + numpy fallback: Works everywhere, identical results, just slower for large-scale retrieval",
    ]
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    for i, d in enumerate(decisions):
        pdf.set_xy(25, 110 + i * 9)
        pdf.cell(5, 9, "-")
        pdf.cell(247, 9, f"  {d}")

    # ================================================================
    # Save
    # ================================================================
    pdf.output(out_path)
    print(f"Presentation saved to: {out_path}")
    print(f"Total slides: {pdf.slide_num}")


def main():
    parser = argparse.ArgumentParser(description="Generate hackathon presentation PDF")
    parser.add_argument("--out", default="presentation.pdf", help="Output PDF path")
    args = parser.parse_args()
    build_presentation(args.out)


if __name__ == "__main__":
    main()
