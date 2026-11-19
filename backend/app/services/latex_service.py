"""
LaTeX Generation, Escaping, Syntax Validation, and PDF Compilation Service.
Uses Jinja2 with custom LaTeX delimiters to produce deterministic, professional LaTeX source code.
"""
import io
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import jinja2

logger = logging.getLogger(__name__)

# Template directory
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "latex"

# Allowed templates
RESUME_TEMPLATES = {
    "modern": "Modern clean layout with clean section dividers and high readability",
    "classic": "Traditional Harvard/Wall Street serif style, elegant and ATS-optimized",
    "minimal": "Minimalist single-column sans-serif style for technical clarity",
}

COVER_LETTER_TEMPLATES = {
    "formal": "Classic corporate letterhead with full recipient and salutation formatting",
    "modern": "Contemporary design matching the modern resume header style",
}


_LATEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_LATEX_REGEX = re.compile(r"([\\&%$#_{}~^])")


def escape_latex(val: Any) -> str:
    """Safely escape special LaTeX reserved characters in a single pass.

    Reserved characters: & % $ # _ { } ~ ^ \\
    """
    if val is None:
        return ""
    if not isinstance(val, str):
        val = str(val)

    return _LATEX_REGEX.sub(lambda m: _LATEX_ESCAPES[m.group(1)], val)


def create_latex_jinja_env() -> jinja2.Environment:
    """Create a Jinja2 environment configured for LaTeX syntax without delimiter collisions."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        block_start_string=r"\BLOCK{",
        block_end_string=r"}",
        variable_start_string=r"\VAR{",
        variable_end_string=r"}",
        comment_start_string=r"\#{",
        comment_end_string=r"}",
        line_statement_prefix=r"%%",
        line_comment_prefix=r"%#",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    env.filters["latex_escape"] = escape_latex
    env.filters["escape_latex"] = escape_latex
    return env


# Singleton Jinja2 environment
_jinja_env: Optional[jinja2.Environment] = None


def get_jinja_env() -> jinja2.Environment:
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = create_latex_jinja_env()
    return _jinja_env


def validate_latex_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Perform security and structural syntax validation on LaTeX source code.

    Returns:
        (is_valid, error_message)
    """
    if not code or not code.strip():
        return False, "LaTeX source code cannot be empty."

    # 1. Security Check: Block dangerous low-level execution macros
    dangerous_commands = [
        r"\write18",
        r"\input",
        r"\include",
        r"\openin",
        r"\openout",
        r"\catcode",
        r"\csname",
        r"\endinput",
        r"\immediate\write",
    ]
    for cmd in dangerous_commands:
        if re.search(re.escape(cmd), code, re.IGNORECASE):
            return False, f"Potentially unsafe LaTeX command detected: '{cmd}' is prohibited."

    # 2. Structural Requirements
    if r"\documentclass" not in code:
        return False, "Missing mandatory \\documentclass declaration."
    if r"\begin{document}" not in code:
        return False, "Missing \\begin{document} block."
    if r"\end{document}" not in code:
        return False, "Missing \\end{document} block."

    # 3. Matching Braces Check (ignoring escaped \{ and \})
    cleaned = code.replace(r"\{", "").replace(r"\}", "")
    open_braces = cleaned.count("{")
    close_braces = cleaned.count("}")
    if open_braces != close_braces:
        return False, f"Mismatched curly braces in document (found {open_braces} '{{' and {close_braces} '}}')."

    # 4. Matching Environments Check
    env_stack: List[str] = []
    # Find all \begin{...} and \end{...}
    pattern = re.compile(r"\\(begin|end)\{([a-zA-Z0-9*]+)\}")
    for match in pattern.finditer(code):
        action, env_name = match.groups()
        if action == "begin":
            env_stack.append(env_name)
        elif action == "end":
            if not env_stack:
                return False, f"Unexpected \\end{{{env_name}}} with no matching \\begin."
            last_env = env_stack.pop()
            if last_env != env_name:
                return False, f"Environment mismatch: expected \\end{{{last_env}}}, but found \\end{{{env_name}}}."

    if env_stack:
        return False, f"Unclosed LaTeX environment: \\begin{{{env_stack[-1]}}} was never closed with \\end."

    return True, None


def render_resume_latex(resume_data: Dict[str, Any], template_name: str = "modern") -> str:
    """Render a tailored resume dictionary to LaTeX source code using the chosen template."""
    template_name = template_name.lower().strip()
    if template_name not in RESUME_TEMPLATES:
        template_name = "modern"

    template_file = f"{template_name}_resume.tex.j2"
    env = get_jinja_env()
    template = env.get_template(template_file)

    # Normalize fields
    context = {
        "header": resume_data.get("header") or {},
        "professional_summary": resume_data.get("professional_summary") or "",
        "skills": resume_data.get("skills") or {},
        "work_experience": resume_data.get("work_experience") or [],
        "selected_projects": resume_data.get("selected_projects") or [],
        "education": resume_data.get("education") or [],
    }

    rendered = template.render(**context)

    # Validate output
    is_valid, err = validate_latex_syntax(rendered)
    if not is_valid:
        logger.error(f"Rendered LaTeX failed validation: {err}")
        raise ValueError(f"LaTeX rendering validation failed: {err}")

    return rendered


def render_cover_letter_latex(
    cover_letter_data: Dict[str, Any],
    contact_info: Optional[Dict[str, Any]] = None,
    template_name: str = "formal",
) -> str:
    """Render a tailored cover letter dictionary to LaTeX source code using the chosen template."""
    template_name = template_name.lower().strip()
    if template_name not in COVER_LETTER_TEMPLATES:
        template_name = "formal"

    template_file = f"{template_name}_cover_letter.tex.j2"
    env = get_jinja_env()
    template = env.get_template(template_file)

    context = {
        "candidate_name": cover_letter_data.get("candidate_name") or (contact_info.get("full_name") if contact_info else "Candidate"),
        "contact": contact_info or {},
        "company_name": cover_letter_data.get("company_name"),
        "target_role": cover_letter_data.get("target_role") or "Target Role",
        "salutation": cover_letter_data.get("salutation") or "Dear Hiring Team,",
        "opening_paragraph": cover_letter_data.get("opening_paragraph") or "",
        "body_paragraphs": cover_letter_data.get("body_paragraphs") or [],
        "closing_paragraph": cover_letter_data.get("closing_paragraph") or "",
        "sign_off": cover_letter_data.get("sign_off") or "Sincerely,",
    }

    rendered = template.render(**context)

    is_valid, err = validate_latex_syntax(rendered)
    if not is_valid:
        logger.error(f"Rendered Cover Letter LaTeX failed validation: {err}")
        raise ValueError(f"Cover letter LaTeX validation failed: {err}")

    return rendered


def _compile_with_reportlab_fallback(latex_code: str) -> bytes:
    """Offline fallback: constructs a clean PDF document when no TeX engine is reachable."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
        alignment=1,  # Center
    )
    section_style = ParagraphStyle(
        "DocSection",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )

    story = []

    # Simple parser to turn plain text extracted from LaTeX into styled PDF paragraphs
    clean_text = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?(\{[^\}]*\})?", " ", latex_code)
    clean_text = clean_text.replace("{", "").replace("}", "").replace("\\", "")

    lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
    first_line = True
    for line in lines:
        if first_line:
            story.append(Paragraph(line, title_style))
            story.append(Spacer(1, 12))
            first_line = False
        elif line.isupper() and len(line) < 40:
            story.append(Spacer(1, 6))
            story.append(Paragraph(line, section_style))
            story.append(Spacer(1, 3))
        else:
            story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 3))

    doc.build(story)
    return buffer.getvalue()


def compile_latex_to_pdf(latex_code: str) -> bytes:
    """Compile LaTeX source code into binary PDF content.

    Execution Pipeline:
    1. Local pdflatex or xelatex (if installed locally on the system)
    2. Cloud compilation service (latexonline.cc)
    3. Offline ReportLab fallback
    """
    # 1. Check local TeX engines
    local_engine = shutil.which("pdflatex") or shutil.which("xelatex")
    if local_engine:
        logger.info(f"Compiling LaTeX using local engine: {local_engine}")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tex_file = os.path.join(tmpdir, "document.tex")
                with open(tex_file, "w", encoding="utf-8") as f:
                    f.write(latex_code)

                cmd = [
                    local_engine,
                    "-interaction=nonstopmode",
                    "-no-shell-escape",
                    "document.tex",
                ]
                proc = subprocess.run(
                    cmd,
                    cwd=tmpdir,
                    capture_output=True,
                    timeout=25,
                )
                pdf_file = os.path.join(tmpdir, "document.pdf")
                if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 0:
                    with open(pdf_file, "rb") as f:
                        return f.read()
                logger.warning(f"Local compilation failed: {proc.stderr.decode('utf-8', errors='ignore')[:300]}")
        except Exception as e:
            logger.warning(f"Local engine compilation error: {e}. Falling back to cloud service.")

    # 2. Cloud compilation service
    logger.info("Compiling LaTeX via cloud compilation service (latexonline.cc)...")
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(
                "https://latexonline.cc/compile",
                params={"text": latex_code},
            )
            if resp.status_code == 200 and "application/pdf" in resp.headers.get("content-type", ""):
                if len(resp.content) > 500:
                    logger.info("Successfully compiled PDF via latexonline.cc")
                    return resp.content
            logger.warning(f"latexonline.cc returned status {resp.status_code}. Falling back.")
    except Exception as e:
        logger.warning(f"Cloud LaTeX compilation service error: {e}. Falling back to ReportLab.")

    # 3. Offline ReportLab Fallback
    logger.info("Compiling document via offline ReportLab engine...")
    return _compile_with_reportlab_fallback(latex_code)
