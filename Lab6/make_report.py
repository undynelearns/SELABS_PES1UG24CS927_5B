"""Build the consolidated Lab 5 PDF from the real reports and screenshots.

Run from the ROOT of your repo:
    python ~/Downloads/make_report.py
"""
import os
import re
import subprocess
import sys
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                Preformatted, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

SHOTS = os.path.expanduser("~/Desktop/lab5_screens")
REPO_URL = "https://github.com/undynelearns/L5_65_auction-bidding"

if not os.path.isfile("auction_system.py") or not os.path.isdir("reports"):
    sys.exit("Run this from the repo folder (cd ~/Desktop/L5_65_auction-bidding)")

NAME = input("Your full name: ").strip()
SRN = input("Your SRN: ").strip()
SECTION = input("Your section (e.g. B): ").strip()
OUT = os.path.expanduser(f"~/Desktop/Lab5_{SRN or 'report'}.pdf")

# ---------- styles ----------
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15,
                    textColor=colors.HexColor("#1F3A5F"), spaceBefore=6,
                    spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12,
                    textColor=colors.HexColor("#1F3A5F"), spaceBefore=10,
                    spaceAfter=4)
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontSize=10, leading=14,
                      spaceAfter=6)
CELL = ParagraphStyle("C", parent=BODY, fontSize=8, leading=10, spaceAfter=0)
CELLB = ParagraphStyle("CB", parent=CELL, fontName="Helvetica-Bold",
                       textColor=colors.white)
CODE = ParagraphStyle("Code", fontName="Courier", fontSize=7, leading=8.6,
                      backColor=colors.HexColor("#F4F4F4"), borderPadding=4)
CAP = ParagraphStyle("Cap", parent=BODY, fontSize=8.5, alignment=TA_CENTER,
                     textColor=colors.HexColor("#555555"))
WARN = ParagraphStyle("W", parent=BODY, textColor=colors.red)

story = []
missing = []


def p(text, style=BODY):
    story.append(Paragraph(text, style))


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except FileNotFoundError:
        missing.append(path)
        return None


def code_block(text):
    clean = text.expandtabs(4).encode("latin-1", "replace").decode("latin-1")
    story.append(Preformatted(clean.rstrip() or " ", CODE,
                              maxLineLength=118, newLineChars=""))
    story.append(Spacer(1, 6))


def shot(name, caption):
    path = os.path.join(SHOTS, name)
    if not os.path.isfile(path):
        missing.append(path)
        p(f"[Screenshot missing: {name}]", WARN)
        return
    img_w, img_h = ImageReader(path).getSize()
    max_w, max_h = 17 * cm, 19 * cm
    scale = min(max_w / img_w, max_h / img_h)
    story.append(KeepTogether([
        Image(path, width=img_w * scale, height=img_h * scale),
        Spacer(1, 3), Paragraph(caption, CAP), Spacer(1, 8)]))


def table(rows, widths):
    data = [[Paragraph(c, CELLB) for c in rows[0]]]
    data += [[Paragraph(c, CELL) for c in r] for r in rows[1:]]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#AAAAAA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F2F6FA")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))


# ---------- data from the real reports ----------
R = {k: read(f"reports/{k}.txt") for k in (
    "pylint_report_before", "pylint_report_after",
    "bandit_report_before", "bandit_report_after",
    "flake8_report_before", "flake8_report_after")}


def score(txt):
    m = re.search(r"rated at ([\d.]+)/10", txt or "")
    return m.group(1) + "/10" if m else "n/a"


def pylint_count(txt):
    return len(re.findall(r"^auction_system\.py:\d+:", txt or "", re.M))


def bandit_count(txt):
    return len(re.findall(r">> Issue:", txt or ""))


def flake8_count(txt):
    return len([ln for ln in (txt or "").splitlines() if ln.strip()])


try:
    GITLOG = subprocess.run(["git", "log", "--oneline", "--reverse"],
                            capture_output=True, text=True,
                            check=True).stdout
except (OSError, subprocess.CalledProcessError):
    GITLOG = "(git log unavailable)"

# ---------- cover ----------
story.append(Spacer(1, 4 * cm))
p("Lab 5: Static Code Analysis", ParagraphStyle(
    "T", parent=ss["Title"], fontSize=24, textColor=colors.HexColor("#1F3A5F")))
p("Online Auction and Bidding System (auction_system.py)",
  ParagraphStyle("ST", parent=BODY, fontSize=13, alignment=TA_CENTER))
story.append(Spacer(1, 2 * cm))
table([["Field", "Details"],
       ["Name", escape(NAME)], ["SRN", escape(SRN)],
       ["Section", escape(SECTION)],
       ["Course", "Software Engineering - Lab 5"],
       ["Repository", f'<link href="{REPO_URL}" color="blue">{REPO_URL}</link>'],
       ["Tools", "Pylint, Bandit, Flake8 (Python 3)"],
       ["Date", date.today().strftime("%d %B %Y")]], [4, 12])
story.append(PageBreak())

# ---------- 1. intro ----------
p("1. Introduction to Static Code Analysis", H1)
p("Static code analysis examines source code <b>without executing it</b> to "
  "find bugs, security vulnerabilities and style violations early, when "
  "they are cheapest to fix. It complements testing: tools catch whole "
  "classes of problems automatically and consistently, while tests and "
  "code review check that the program behaves correctly.")
p("1.1 The three tools", H2)
table([["Tool", "Role", "What it checks"],
       ["Pylint", "Strict code reviewer",
        "Code quality and logical errors: unused variables, broad "
        "exceptions, naming conventions, missing docstrings, attributes "
        "defined outside __init__, design smells. Gives a score out of 10."],
       ["Flake8", "Grammar checker",
        "PEP 8 style: whitespace, blank lines, line length, plus syntax "
        "errors and unused imports (pycodestyle + pyflakes + mccabe)."],
       ["Bandit", "Security guard",
        "Common security issues: dangerous functions, injection, XSS via "
        "disabled autoescaping, insecure XML parsing, hard-coded secrets. "
        "Rates each issue by severity and confidence."]], [2.5, 3.5, 11])
p("1.2 Commands used", H2)
code_block("python -m pylint auction_system.py > pylint_report.txt\n"
           "python -m bandit -r auction_system.py > bandit_report.txt\n"
           "python -m flake8 auction_system.py > flake8_report.txt")
p("Reports were saved as <i>*_before.txt</i> (original code) and "
  "<i>*_after.txt</i> (fixed code) in the <i>reports/</i> folder.")

p("1.3 Results summary", H2)
pb, pa = R["pylint_report_before"], R["pylint_report_after"]
bb, ba = R["bandit_report_before"], R["bandit_report_after"]
fb, fa = R["flake8_report_before"], R["flake8_report_after"]
table([["Tool", "Before fixing", "After fixing"],
       ["Pylint", f"Score {score(pb)}, {pylint_count(pb)} messages",
        f"Score {score(pa)}, {pylint_count(pa)} messages"],
       ["Bandit", f"{bandit_count(bb)} issues", f"{bandit_count(ba)} issues"],
       ["Flake8", f"{flake8_count(fb)} violations",
        f"{flake8_count(fa)} violations"]], [4, 6, 6])
story.append(PageBreak())

# ---------- 2. before screenshots ----------
p("2. Issues Identified Before Fixing (Screenshots)", H1)
shot("program_before.png", "Figure 1: Original program output - note the "
     "wrong results (equal bid accepted, seller bidding, Rs.0 winner, raw "
     "&lt;script&gt; tag).")
shot("pylint_before.png", "Figure 2: Pylint on the original code.")
shot("bandit_before.png", "Figure 3: Bandit on the original code.")
shot("flake8_before.png", "Figure 4: Flake8 on the original code.")
story.append(PageBreak())

# ---------- 3. issue table ----------
p("3. Issue Identification Table", H1)
p("Line numbers refer to the original file. High and medium severity "
  "issues are listed first.")
table([
    ["#", "Issue (tool / code)", "Type", "Line(s)", "Description",
     "Fix approach"],
    ["1", "Jinja2 autoescape disabled (Bandit B701, High)", "Security / XSS",
     "65", "autoescape=False renders the lot title raw, so the "
     "&lt;script&gt; title is injected into the HTML.",
     "Environment(autoescape=True); template compiled once."],
    ["2", "Markup from string concatenation (Bandit B704, Medium)",
     "Security / XSS", "70", "Markup(... + name + ...) marks untrusted "
     "input as safe, so &lt;img onerror&gt; executes.",
     "Markup(\"&lt;span ...&gt;{}&lt;/span&gt;\").format(name) - escapes "
     "the argument."],
    ["3", "Insecure xmlrpc import (Bandit B411, High)", "Security / XML",
     "5", "xmlrpc.client is vulnerable to XML-bomb / entity-expansion "
     "attacks from the payment server.",
     "defusedxml.xmlrpc.monkey_patch(); import marked # nosec B411."],
    ["4", "Broad exception raised / caught (Pylint W0719, W0718)",
     "Error handling", "23, 50", "raise/except Exception hides real bugs "
     "as 'bid rejected'.", "Custom BidRejected(ValueError); catch only "
     "(KeyError, BidRejected)."],
    ["5", "Attribute defined outside __init__ (Pylint W0201)", "Bug risk",
     "27", "self.leader exists only after the first bid.",
     "highest/leader became properties derived from the bid list."],
    ["6", "Times compared as strings (found by running)", "Logic bug",
     "22", "'9:30' &gt; '18:00' alphabetically, so a valid 9:30 AM bid "
     "was rejected.", "Parse with datetime.strptime and compare datetimes."],
    ["7", "Equal / under-increment bids accepted (found by running)",
     "Logic bug", "9, 24", "amount &gt;= highest accepted equal bids; "
     "MIN_INCREMENT never used.",
     "Require amount &gt;= highest + MIN_INCREMENT."],
    ["8", "Seller bids on own item; Rs.0 bid (found by running)",
     "Logic bug", "21-30", "Shill bidding and zero bids were accepted.",
     "Reject bidder == seller and amount &lt;= 0."],
    ["9", "Reserve price ignored (found by running)", "Logic bug",
     "32-38", "Winner/final price returned below the reserve.",
     "reserve_met(); winner()/final_price() return None if not met."],
    ["10", "Non-snake_case names, missing docstrings (Pylint C0103, "
     "C0114-C0116)", "Convention", "many", "placeBid, createAuction, ...; "
     "no docstrings.", "Renamed to snake_case; docstrings added."],
    ["11", "Useless object inheritance, len()==0, no-else-return "
     "(R0205, C1802, R1705, R1724)", "Refactor", "11, 29, 33, 60",
     "Python 2 style and redundant branches.",
     "@dataclass; truthiness checks; removed else branches."],
    ["12", "Wrong import order (Pylint C0411)", "Convention", "1-6",
     "Third-party imports before standard library.",
     "Stdlib first, then third-party."],
    ["13", "Expected 2 blank lines (Flake8 E302, E305)", "Style",
     "11, 43-107", "Top-level definitions separated by one blank line.",
     "Two blank lines around top-level defs."],
    ["14", "Line too long (Flake8 E501)", "Style", "66, 89-101",
     "Lines over 79 characters.", "Wrapped inside parentheses."],
], [0.8, 3.3, 1.9, 1.5, 4.7, 4.8])

p("3.1 Commits", H2)
p("Each tool's fixes were committed separately (oldest first):")
code_block(GITLOG)
story.append(PageBreak())

# ---------- 4. reports ----------
p("4. Before-and-After Outputs of All Three Tools", H1)
for tool in ("pylint", "bandit", "flake8"):
    for when in ("before", "after"):
        key = f"{tool}_report_{when}"
        p(f"{tool.capitalize()} report - {when} fixing ({key}.txt)", H2)
        txt = R[key]
        if txt is None:
            p(f"[{key}.txt not found]", WARN)
        elif not txt.strip():
            code_block("(empty file - Flake8 reported no violations)")
        else:
            code_block(txt)
story.append(PageBreak())

# ---------- 5. after screenshots ----------
p("5. Results After Fixing (Screenshots)", H1)
shot("pylint_after.png", f"Figure 5: Pylint on the fixed code - {score(pa)}.")
shot("bandit_after.png", "Figure 6: Bandit on the fixed code - no issues.")
shot("flake8_after.png", "Figure 7: Flake8 on the fixed code - no output "
     "means no violations.")
shot("program_after.png", "Figure 8: Fixed program output - invalid bids "
     "rejected, reserve respected, HTML escaped.")
shot("github_commits.png", "Figure 9: Commit history on GitHub.")
story.append(PageBreak())

# ---------- 6. reflection ----------
p("6. Reflection", H1)
REFLECTION = [
    ("Which issues were the easiest to fix, and which were the hardest? Why?",
     "The easiest were Flake8's formatting issues (blank lines, long lines) "
     "and Pylint's naming and docstring messages: the tool names the exact "
     "line, the fix is mechanical, and behaviour does not change. The "
     "hardest were the logic bugs that no tool reported: equal and +50 "
     "bids replacing the leader, the seller bidding on his own item, a Rs.0 "
     "bid winning, and a winner below the reserve price. The trickiest was "
     "the 9:30 AM bid being rejected because times were compared as "
     "strings ('9:30' &gt; '18:00' alphabetically). These needed an "
     "understanding of the auction rules, not just the code. Bandit B411 "
     "was also harder, because fixing it meant learning about XML "
     "entity-expansion attacks and using defusedxml."),
    ("Did the static analysis tools report any false positives? If so, "
     "describe one example.",
     "Partly. Bandit B411 flags every import of xmlrpc.client, even after "
     "defusedxml.xmlrpc.monkey_patch() has hardened it, because Bandit only "
     "looks at the import line. I suppressed it with a targeted "
     "'# nosec B411' and a comment explaining the mitigation, rather than "
     "a blanket suppression. The bigger problem was false <i>negatives</i>: "
     "every business-logic bug passed all three tools, which shows static "
     "analysis complements testing but cannot replace it."),
    ("How would you integrate static analysis tools into your actual "
     "software development workflow?",
     "Locally, a pre-commit hook running Flake8, Pylint and Bandit so "
     "problems are caught before committing, plus editor integration for "
     "instant feedback. In CI (e.g. GitHub Actions), run all three on every "
     "pull request and fail the build if Bandit reports a medium/high "
     "issue, Flake8 reports anything, or the Pylint score drops below 9.5. "
     "A shared configuration file keeps the rules consistent, and unit "
     "tests cover the business rules the tools cannot check."),
    ("What tangible improvements did you observe in the code quality, "
     "readability, or potential robustness after applying the fixes?",
     f"Pylint rose from {score(pb)} to {score(pa)}; Bandit went from "
     f"{bandit_count(bb)} issues to {bandit_count(ba)}; Flake8 from "
     f"{flake8_count(fb)} violations to {flake8_count(fa)}. Both XSS "
     "payloads are now escaped and XML-RPC is hardened. The program now "
     "behaves like a real auction: invalid bids are rejected, the 9:30 AM "
     "bid is accepted, no winner is declared below the reserve, and the "
     "gateway is never charged without a winner. Specific exceptions "
     "replace 'except Exception', and snake_case names, docstrings, a "
     "dataclass and named constants make the code easier to read."),
]
for i, (q, a) in enumerate(REFLECTION, 1):
    p(f"Q{i}. {q}", H2)
    p(a)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1.2 * cm, f"Lab 5 - Static Code Analysis | "
                      f"{NAME} | {SRN}")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                  topMargin=1.8 * cm, bottomMargin=2 * cm,
                  title="Lab 5 Static Code Analysis", author=NAME
                  ).build(story, onFirstPage=footer, onLaterPages=footer)

print(f"\nPDF created: {OUT}")
if missing:
    print("\nWARNING - these were missing (placeholder added):")
    for m in missing:
        print("  ", m)
else:
    print("All screenshots and reports included.")
