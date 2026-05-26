"""Regenerate DIFF PDF for the sandbox paper.

Workflow:
1. Refresh sandbox copies in diff/ (sn-article.tex + sn-bibliography.bib from main/)
2. Run latexdiff-fast on v1.tex + diff/sn-article.tex -> raw INVISIBLE diff
3. Replace the latexdiff-default preamble block with our red-text override
   (xcolor + \DIFadd -> red!75!black, \DIFdel -> empty; no bold, layout-preserving)
4. Write diff/sn-article-DIFF.tex (UTF-8 no-BOM)
5. Caller compiles via pdflatex + bibtex + pdflatex x 2

Encoded patterns lifted from session 22-23 DIFF generation (red text avoids the
17-page widening that bold caused; \hl{} from soul breaks on \cite{}).
"""
import re
import subprocess
from pathlib import Path

V1 = r"c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-article.tex"
SANDBOX_DIR = Path(r"c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16")
SANDBOX_MAIN_TEX = SANDBOX_DIR / "main" / "sn-article.tex"
SANDBOX_MAIN_BIB = SANDBOX_DIR / "main" / "sn-bibliography.bib"
DIFF_TARGET_TEX = SANDBOX_DIR / "diff" / "sn-article.tex"
DIFF_TARGET_BIB = SANDBOX_DIR / "diff" / "sn-bibliography.bib"
DIFF_OUT = SANDBOX_DIR / "diff" / "sn-article-DIFF.tex"
LATEXDIFF = r"C:\Users\partha\AppData\Local\Programs\MiKTeX\miktex\bin\x64\latexdiff-fast.exe"

OVERRIDE = r"""%DIF PREAMBLE EXTENSION ADDED BY LATEXDIFF
%DIF INVISIBLE PREAMBLE (simplified: red text via xcolor; listings dropped --- DIFverbatim is unused in this paper's body)
\RequirePackage{xcolor}
\providecommand{\DIFadd}[1]{{\protect\color{red!75!black}#1}}
\providecommand{\DIFdel}[1]{}
\providecommand{\DIFaddbegin}{}
\providecommand{\DIFaddend}{}
\providecommand{\DIFdelbegin}{}
\providecommand{\DIFdelend}{}
\providecommand{\DIFmodbegin}{}
\providecommand{\DIFmodend}{}
\providecommand{\DIFaddFL}[1]{\DIFadd{#1}}
\providecommand{\DIFdelFL}[1]{\DIFdel{#1}}
\providecommand{\DIFaddbeginFL}{}
\providecommand{\DIFaddendFL}{}
\providecommand{\DIFdelbeginFL}{}
\providecommand{\DIFdelendFL}{}
\newenvironment{DIFverbatim}[1][]{}{}
\newenvironment{DIFverbatim*}[1][]{}{}
%DIF END PREAMBLE EXTENSION ADDED BY LATEXDIFF"""


def main() -> None:
    DIFF_TARGET_TEX.write_text(SANDBOX_MAIN_TEX.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    DIFF_TARGET_BIB.write_text(SANDBOX_MAIN_BIB.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    print(f"refreshed diff/sn-article.tex + sn-bibliography.bib")

    result = subprocess.run(
        [
            LATEXDIFF,
            "--type=INVISIBLE",
            "--graphics-markup=none",
            "--no-del",
            "--exclude-textcmd=emph,textbf,textit,texttt",
            V1,
            str(DIFF_TARGET_TEX),
        ],
        capture_output=True,
    )
    if result.returncode != 0:
        print("latexdiff-fast FAILED")
        print(result.stderr.decode("utf-8", errors="replace"))
        raise SystemExit(1)

    content = result.stdout.decode("utf-8")
    pattern = re.compile(
        r"%DIF PREAMBLE EXTENSION ADDED BY LATEXDIFF.*?%DIF END PREAMBLE EXTENSION ADDED BY LATEXDIFF",
        re.DOTALL,
    )
    new_content, n_sub = pattern.subn(lambda _m: OVERRIDE, content)
    if n_sub != 1:
        print(f"WARN: pattern matched {n_sub} times (expected 1)")

    # Strip stray latexdiff invisible markers that landed in the preamble
    # (before \begin{document}). The listings/DIFcode environment only hides
    # markers inside the body; in the preamble they trip LaTeX's parser when
    # they sit between a package directive and a macro definition.
    body_marker = r"\begin{document}"
    pre, sep, body = new_content.partition(body_marker)
    if sep:
        pre_lines = pre.split("\n")
        cleaned = [ln for ln in pre_lines if ln.strip() not in {"%DIF >", "%DIF <"}]
        n_stripped = len(pre_lines) - len(cleaned)
        if n_stripped:
            print(f"stripped {n_stripped} stray DIF marker line(s) from preamble")
        new_content = "\n".join(cleaned) + sep + body

    DIFF_OUT.write_text(new_content, encoding="utf-8", newline="\n")
    print(f"DIFF .tex written: {len(new_content)} bytes -> {DIFF_OUT}")


if __name__ == "__main__":
    main()
