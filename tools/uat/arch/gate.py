"""Public-content gate for the architecture videos and posts (AA-1021). Any hit FAILS the build.

  python -I gate.py text <file>...                 # layer 1: deny-list + built-in identifiers + repo n-gram check
  python -I gate.py patterns-json <out.json>       # the layer 1 deny + identifier patterns for capture.cjs (layer 2)
  python -I gate.py dom <dom-dump.json>...         # layer 2 audit of the DOM text capture.cjs saved per keyframe
  python -I gate.py ocr <image>...                 # layer 3: OCR (local tesseract) on frames
  python -I gate.py artifacts <dir>                # layer 4: file names, SRT/VTT, descriptions, MP4 metadata
  common options: --private DIR (deny.txt, ngram_allow.txt), --no-ngram, --workspace DIR (the n-gram corpus root)

Five layers (plan docs/audits/2026-11-01-S262-arch-video-plan, security section):
  1 text      every string we author: narration, slide text, public labels, descriptions, hashtags, the blog post.
              The private deny-list (gitignored) + built-in identifier shapes (account IDs, ARNs, network and pool IDs,
              hostnames, URLs, e-mails, regions, issue / migration / ADR / session numbers, money amounts) + an n-gram
              check: any 5-word phrase with 2+ content words, or any internal-looking token (snake_case, dotted,
              hyphenated, CamelCase, ALLCAPS), that appears verbatim in a public repo is a hit (pasting it into a
              search would lead to the company); an identity check: the series name and series tag (and any
              "identity" phrase of the episode) must not appear in any public file at all; and a label-set check: one
              public file holding 4+ of the multi-word labels shown on screen is a hit (the combination would find the
              repo even when each label is generic; cloud product names such as "Amazon ..." do not count).
  2 dom       capture.cjs checks the rendered page (body text, SVG text/title/desc, alt/aria/title/data-*, href/src)
              with the same patterns BEFORE every screenshot and refuses to capture on a hit; `gate.py dom` re-audits
              the saved dumps.
  3 pixels    OCR on every keyframe and on one frame every 2 s of each final MP4. Second layer only: OCR misses text,
              so layer 2 stays the primary guard. Without tesseract the layer reports SKIPPED with a warning.
  4 artifacts file names, SRT/VTT, chapter titles, description files and ffprobe metadata (only neutral tags allowed).
  5 human     an independent review agent reads the script, then the tech lead watches every cut (REVIEW.md checklist).
Stdlib only (no venv needed). Cost $0, nothing leaves the machine. Hits are printed to stderr; logs keep counts only.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
NGRAM_N = 5
LABEL_SET_K = 4
MIN_CONTENT_WORDS = 2
TEXT_SUFFIXES = {".md", ".txt", ".py", ".ts", ".tsx", ".js", ".cjs", ".mjs", ".jsx", ".json", ".yml", ".yaml",
                 ".sql", ".tf", ".hcl", ".html", ".css", ".svg", ".sh", ".toml", ".ini", ".cfg", ".csv", ".j2", ".mdx"}
MAX_CORPUS_FILE = 2_000_000
INLINE_DATA = re.compile(r"data:[a-z/+.-]+;base64,[A-Za-z0-9+/=\s]*", re.I)

# Built-in identifier shapes. Each is (category, source, flags) where flags is "" (case-sensitive) or "i"; the sources
# use only syntax that Python `re` and JavaScript RegExp read the same way (capture.cjs compiles them as given).
_B = r"(?<![A-Za-z0-9])"   # word start that also works next to '-', '.', '_' etc.
_E = r"(?![A-Za-z0-9])"
_TLDS = ("com|net|org|io|dev|app|ai|co|it|vn|asia|cloud|xyz|me|info|biz|travel|tech|site|online|us|uk|sg|th|la|kh|"
         "mm|id|my|ph|jp|cn|de|fr|eu|tours|holiday|guide|guides|link|page|run|so|ly|to|tv|gg")
BUILTIN: list[tuple[str, str, str]] = [
    ("identifier:access-key", r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])", ""),
    ("identifier:network-id",
     r"(?<![\w-])(?:sg|subnet|vpc|vpce|rtb|igw|nat|eni|acl|eipalloc|tgw)-[0-9a-f]{8}(?:[0-9a-f]{9})?(?![\w-])", "i"),
    ("identifier:user-pool-id", r"(?<![\w-])[a-z]{2}-[a-z]+-\d_[A-Za-z0-9]{9}(?![\w-])", ""),
    ("identifier:api-host", r"[a-z0-9]{10}\.execute-api\.", "i"),
    ("identifier:account-id", r"(?<!\d)\d{12}(?!\d)", ""),
    ("identifier:account-id", r"(?<!\d)\d{4}[- ]\d{4}[- ]\d{4}(?!\d)", ""),
    ("identifier:arn", r"arn:aws[a-z-]*:", "i"),
    ("identifier:region",
     r"(?<![A-Za-z])(?:us|eu|ap|sa|ca|me|af|il|mx)-(?:north|south|east|west|central|northeast|southeast|northwest|"
     r"southwest)-\d(?!\d)", "i"),
    ("identifier:url", r"(?:https?|s3|ftp)://", "i"),
    ("identifier:url", r"(?<![A-Za-z0-9])www\.", "i"),
    ("identifier:hostname", rf"(?<![\w.-])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:{_TLDS})(?![\w-])", "i"),
    ("identifier:email", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}", ""),
    ("identifier:ip-address", r"(?<![\d.])\d{1,3}(?:\.\d{1,3}){3}(?![\d.])", ""),
    ("identifier:issue-id", _B + r"[A-Z]{2,6}-\d{1,5}" + _E, ""),
    ("identifier:migration-id", _B + r"(?:tp|bk|crm)-\d{3}" + _E, "i"),
    ("identifier:adr-number", _B + r"ADR[ -]?\d{2,4}", "i"),
    ("identifier:session-number", _B + r"S\d{3}" + _E, ""),
    ("money:amount", r"[$€£¥₫]\s?\d", ""),
    ("money:amount", r"(?<![A-Za-z])\d[\d,.]*\s?(?:usd|vnd|eur|dollars?|cents?)" + _E, "i"),
]

# Tokens that look internal but are generic (cloud and web vocabulary); never an n-gram "rare token" hit.
GENERIC_TOKENS = {
    "ai", "api", "apis", "aws", "cdn", "ci", "cd", "crm", "css", "dns", "ec2", "ecr", "ecs", "eks", "faq", "gpu",
    "html",
    "http", "https", "iam", "id", "ids", "json", "kms", "llm", "llms", "mfa", "nat", "oidc", "ou", "ous", "pdf", "pii",
    "pwa", "rds", "rest", "s3", "scp", "scps", "sdk", "seo", "ses", "sms", "sns", "sql", "sqs", "sso", "tls", "ui",
    "url", "urls", "vpc", "waf", "b2b", "b2c", "ux", "qa", "kpi", "rls", "otp", "jwt", "ssl", "sla", "etl", "csv",
    "postgresql", "postgres", "javascript", "typescript", "nextjs", "next.js", "node.js", "fastapi", "cloudfront",
    "elasticache", "cloudtrail", "cloudwatch", "eventbridge", "github", "devops", "saas", "mvp", "ok", "e.g.", "i.e.",
}
# Ordinary hyphenated English words narration uses; any other hyphenated token counts as internal-looking. Extend it per
# series with the private ngram_allow.txt (a token line there is allowed as is).
GENERIC_HYPHENATED = {
    "add-on", "all-in-one", "built-in", "cross-account", "day-to-day", "end-to-end", "event-driven", "follow-up",
    "full-text", "high-level", "in-house", "least-privilege", "long-running", "low-cost", "multi-account",
    "multi-tenant", "one-off", "open-source", "per-app", "read-only", "real-time", "right-sized", "self-hosted",
    "self-service", "single-tenant", "sign-in", "sign-on", "step-by-step", "third-party", "time-boxed",
    "two-factor", "up-to-date", "well-known", "write-ahead", "zero-trust", "pay-as-you-go", "short-lived",
    "long-lived", "back-end", "front-end", "back-office", "e-mail", "re-run", "co-founder", "small-team",
    "cloud-native", "plain-text", "rate-limit", "rate-limited", "fail-safe", "first-class", "general-purpose",
}
CLOUD_PRODUCT_PREFIXES = ("amazon ", "aws ")
IDENTITY_MIN_CHARS = 6
STOPWORDS = set("""
a about above after again against all also am an and any are as at be because been before being below between both but
by can could did do does doing down during each few for from further had has have having he her here hers him his how
i if in into is it its itself just me more most my no nor not now of off on once one only or other our ours out over
own same she should so some such than that the their theirs them then there these they this those through to too
under until up very was we were what when where which while who whom why will with would you your yours yourself
every each per via let lets get gets got make makes made way ways thing things also many much new next first last
two three four five six seven eight nine ten its it's that's there's here's don't doesn't isn't can't won't
""".split())
WORD = re.compile(r"[a-z0-9]+(?:[._'][a-z0-9]+)*")
TOKEN_EDGE = "a-z0-9"      # a rare token matches in the corpus between characters outside this set ("x_y" in "x_y_z")


@dataclass
class Pattern:
    category: str
    source: str
    flags: str            # "" or "i"
    regex: re.Pattern = field(init=False, repr=False)

    def __post_init__(self):
        self.regex = re.compile(self.source, re.I if "i" in self.flags else 0)


@dataclass
class Hit:
    layer: str
    category: str
    where: str
    match: str

    def line(self) -> str:
        return f"[{self.layer}] {self.category} in {self.where}: {self.match!r}"


# ---------------------------------------------------------------------------------------------------------------- setup
def private_dir(arg: str | None = None) -> Path:
    """Where the gitignored deny-list and allow-list live: --private, env ARCH_VIDEO_PRIVATE, else ./private."""
    return Path(arg or os.environ.get("ARCH_VIDEO_PRIVATE") or HERE / "private").resolve()


def literal_source(term: str) -> str:
    """A word-bounded literal: whitespace inside the term matches any run of whitespace (line breaks, OCR)."""
    parts = [re.sub(r"([.^$*+?()\[\]{}|\\/])", r"\\\1", p) for p in term.split()]
    return _B + r"\s+".join(parts) + _E


def parse_deny(text: str) -> list[Pattern]:
    """Deny-list lines: `term` (case-insensitive literal), `cs:Term` (case-sensitive literal), `re:regex`
    (case-insensitive), `csre:regex` (case-sensitive); `## name` starts a category; `#` starts a comment."""
    out, cat = [], "deny"
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("##"):
            cat = "deny:" + line.lstrip("#").strip().split()[0].lower()
            continue
        if line.startswith("#"):
            continue
        if line.startswith("csre:"):
            out.append(Pattern(cat, line[5:], ""))
        elif line.startswith("re:"):
            out.append(Pattern(cat, line[3:], "i"))
        elif line.startswith("cs:"):
            out.append(Pattern(cat, literal_source(line[3:]), ""))
        else:
            out.append(Pattern(cat, literal_source(line), "i"))
    return out


def load_patterns(priv: Path | None, require_deny: bool = True) -> list[Pattern]:
    pats = [Pattern(c, s, f) for c, s, f in BUILTIN]
    deny = priv / "deny.txt" if priv else None
    if deny and deny.exists():
        pats += parse_deny(deny.read_text(encoding="utf-8"))
    elif require_deny:
        raise SystemExit(f"gate: no deny-list at {deny} (copy deny.example.txt there and fill it); refusing to pass")
    return pats


def literal_terms(priv: Path | None) -> list[str]:
    """The plain deny terms (for fuzzy OCR matching)."""
    deny = priv / "deny.txt" if priv else None
    if not deny or not deny.exists():
        return []
    terms = []
    for raw in deny.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(("re:", "csre:")):
            continue
        terms.append(line[3:] if line.startswith("cs:") else line)
    return terms


# ---------------------------------------------------------------------------------------------------------- layer 1/2
def scan_text(text: str, where: str, patterns: list[Pattern], layer: str = "L1") -> list[Hit]:
    text = INLINE_DATA.sub("data:;base64,", text)
    hits = []
    for p in patterns:
        for m in p.regex.finditer(text):
            hits.append(Hit(layer, p.category, where, m.group(0)))
    return hits


def tokens(text: str) -> list[str]:
    return WORD.findall(text.lower())


def internal_looking(tok_raw: str, allow: set[str] | frozenset = frozenset()) -> bool:
    """A token shaped like code or a coined name: snake_case, dotted, hyphenated (2+ parts, unless an ordinary English
    compound), CamelCase inside, ALLCAPS, letters+digits."""
    t = re.sub(r"['’]s$", "", tok_raw.strip(".,;:!?()[]\"'"))
    low = t.lower()
    if not t or low in GENERIC_TOKENS or low in allow:
        return False
    if "_" in t or re.search(r"[a-z]\.[a-z]", t, re.I):
        return True
    if re.search(r"[a-z][A-Z]", t):
        return True
    if re.fullmatch(r"[A-Z]{2,8}s?", t):
        return True
    if re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+", t) and low not in GENERIC_HYPHENATED:
        return True
    return bool(re.fullmatch(r"(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9-]{3,}", t))


def rare_regex(rare: set[str]) -> re.Pattern | None:
    """One pattern for every internal-looking token, matched whole in the lower-cased corpus text. It does not go
    through WORD, which splits on '-' and would never rebuild a hyphenated token such as 'xx-thing2'."""
    if not rare:
        return None
    alts = "|".join(re.escape(t) for t in sorted(rare, key=len, reverse=True))
    return re.compile(rf"(?<![{TOKEN_EDGE}])(?:{alts})(?![{TOKEN_EDGE}])")


def script_shingles(text: str, allow: set[str]) -> set[str]:
    toks = tokens(text)
    out = set()
    for i in range(len(toks) - NGRAM_N + 1):
        gram = toks[i:i + NGRAM_N]
        if sum(1 for w in gram if w not in STOPWORDS and not w.isdigit()) < MIN_CONTENT_WORDS:
            continue
        phrase = " ".join(gram)
        if phrase not in allow:
            out.add(phrase)
    return out


def corpus_files(workspace: Path) -> list[Path]:
    """Every tracked text file of the public repos: the workspace root repo and each child repo under apps/ and infra/.
    ARCH_VIDEO_ROOT_REPO points the root repo at another checkout (a worktree holding a not yet merged change)."""
    root = Path(os.environ.get("ARCH_VIDEO_ROOT_REPO") or workspace)
    repos = [root] + sorted(p.parent for p in workspace.glob("apps/*/.git")) + \
        sorted(p.parent for p in workspace.glob("infra/*/.git"))
    files = []
    for repo in repos:
        try:
            out = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"], check=True, capture_output=True).stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        for rel in out.decode("utf-8", "replace").split("\0"):
            p = repo / rel
            if rel and p.suffix.lower() in TEXT_SUFFIXES and p.is_file():
                files.append(p)
    return files


def rel_name(path: Path, workspace: Path) -> str:
    try:
        return str(path.relative_to(workspace))
    except ValueError:
        return path.name


def label_set_candidates(public_labels: list[str]) -> list[str]:
    """The multi-word labels the label-set check counts: cloud product names ("Amazon ...", "AWS ...") are left out,
    they sit together in every architecture page on the web."""
    out = set()
    for lab in public_labels:
        low = " ".join((lab or "").lower().split())
        if len(low.split()) >= 2 and not low.startswith(CLOUD_PRODUCT_PREFIXES):
            out.add(low)
    return sorted(out)


def label_set_scan(public_labels: list[str], workspace: Path, k: int = LABEL_SET_K) -> list[Hit]:
    """Layer 1: a public file that holds k or more of the multi-word labels shown on screen (case-insensitive)."""
    labs = label_set_candidates(public_labels)
    if len(labs) < k:
        return []
    hits = []
    for path in corpus_files(workspace):
        try:
            if path.stat().st_size > MAX_CORPUS_FILE:
                continue
            body = " ".join(INLINE_DATA.sub(" ", path.read_text(encoding="utf-8", errors="ignore")).lower().split())
        except OSError:
            continue
        found = [lab for lab in labs if lab in body]
        if len(found) >= k:
            hits.append(Hit("L1", "ngram:label-set", rel_name(path, workspace), f"{len(found)} public labels together"))
    return hits


def ngram_scan(texts: dict[str, str], workspace: Path, allow: set[str]) -> list[Hit]:
    """Layer 1 searchability check: script phrases and internal-looking tokens found verbatim in a public repo."""
    shingles: dict[str, str] = {}
    rare: dict[str, str] = {}
    for where, text in texts.items():
        for s in script_shingles(text, allow):
            shingles.setdefault(s, where)
        for raw in text.split():
            if internal_looking(raw, allow):
                rare.setdefault(re.sub(r"['’]s$", "", raw.strip(".,;:!?()[]\"'")).lower(), where)
    if not shingles and not rare:
        return []
    first = {}
    for s in shingles:
        first.setdefault(s.split(" ", 1)[0], []).append(s)
    rare_rx = rare_regex(set(rare))
    found: dict[str, str] = {}
    for path in corpus_files(workspace):
        try:
            if path.stat().st_size > MAX_CORPUS_FILE:
                continue
            body = INLINE_DATA.sub(" ", path.read_text(encoding="utf-8", errors="ignore")).lower()
        except OSError:
            continue
        if rare_rx is not None:
            for m in rare_rx.finditer(body):
                found.setdefault(m.group(0), rel_name(path, workspace))
        toks = tokens(body)
        for i, tok in enumerate(toks):
            cands = first.get(tok)
            if cands:
                phrase = " ".join(toks[i:i + NGRAM_N])
                if phrase in shingles and phrase not in found:
                    found[phrase] = rel_name(path, workspace)
    hits = []
    for key, src in sorted(found.items()):
        where = shingles.get(key) or rare.get(key)
        kind = "ngram:phrase" if key in shingles else "ngram:token"
        hits.append(Hit("L1", kind, where, f"{key}  (also in {src})"))
    return hits


def identity_scan(phrases: dict[str, str], workspace: Path) -> list[Hit]:
    """Layer 1: the series name, the series tag and any listed identity phrase are what a viewer would search for, so
    none of them may appear in any public file (case- and whitespace-insensitive), however short or generic."""
    want: dict[str, str] = {}
    for where, phrase in phrases.items():
        norm = " ".join(re.sub(r"[^a-z0-9]+", " ", (phrase or "").lower()).split())
        if len(norm) >= IDENTITY_MIN_CHARS:
            want.setdefault(norm, where)
    if not want:
        return []
    found: dict[str, str] = {}
    for path in corpus_files(workspace):
        try:
            if path.stat().st_size > MAX_CORPUS_FILE:
                continue
            body = " " + " ".join(re.sub(r"[^a-z0-9]+", " ",
                                         INLINE_DATA.sub(" ", path.read_text(encoding="utf-8", errors="ignore"))
                                         .lower()).split()) + " "
        except OSError:
            continue
        for norm in want:
            if norm not in found and f" {norm} " in body:
                found[norm] = rel_name(path, workspace)
    return [Hit("L1", "ngram:identity", want[n], f"{n}  (in {src})") for n, src in sorted(found.items())]


def strip_episode_marker(tag: str) -> str:
    """'Series name · Ep 3' -> 'Series name' (the identity check looks for the series part of an on-screen tag)."""
    return re.sub(r"[\s·|:,-]*\b(?:ep|episode|part|no)\.?\s*\d+\s*$", "", tag or "", flags=re.I).strip(" ·|:-")


def load_allow(priv: Path | None) -> set[str]:
    """Allowed phrases (normalised to WORD tokens) and allowed single tokens (lower-cased as written)."""
    allow = set()
    for f in (HERE / "ngram_allow.txt", (priv / "ngram_allow.txt") if priv else None):
        if f and f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    allow.add(" ".join(tokens(line)))
                    if len(line.split()) == 1:
                        allow.add(line.lower())
    return allow


def default_workspace() -> Path:
    env = os.environ.get("ARCH_VIDEO_WORKSPACE")
    if env:
        return Path(env).resolve()
    try:
        common = subprocess.run(["git", "-C", str(HERE), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                check=True, capture_output=True, text=True).stdout.strip()
        return Path(common).parent
    except (subprocess.CalledProcessError, FileNotFoundError):
        return HERE.parents[2]


def check_texts(texts: dict[str, str], patterns: list[Pattern], workspace: Path | None, allow: set[str],
                ngram: bool = True) -> list[Hit]:
    hits = []
    for where, text in texts.items():
        hits += scan_text(text, where, patterns)
    if ngram and workspace is not None:
        hits += ngram_scan(texts, workspace, allow)
    return hits


def patterns_json(patterns: list[Pattern]) -> list[dict]:
    return [{"category": p.category, "source": p.source, "flags": p.flags} for p in patterns]


def dom_dump_texts(dump: dict) -> str:
    """The strings capture.cjs collected for one frame, as one text (layer 2 audit)."""
    parts = [dump.get("title", ""), dump.get("body", "")]
    parts += dump.get("svg", []) + dump.get("attrs", []) + dump.get("refs", [])
    return "\n".join(str(p) for p in parts if p)


# ---------------------------------------------------------------------------------------------------------- layer 3
def tesseract_cmd() -> tuple[list[str], dict] | None:
    """The local tesseract (setup.sh unpacks it without root into <cache>/ocr/root), else one on PATH."""
    cache = Path(os.environ.get("ARCH_VIDEO_CACHE") or HERE / ".cache")
    root = cache / "ocr" / "root"
    exe = root / "usr" / "bin" / "tesseract"
    if exe.exists():
        env = {**os.environ, "LD_LIBRARY_PATH": str(root / "usr/lib/x86_64-linux-gnu"),
               "TESSDATA_PREFIX": str(root / "usr/share/tesseract-ocr/5/tessdata"), "OMP_THREAD_LIMIT": "2"}
        return [str(exe)], env
    found = shutil.which("tesseract")
    return ([found], {**os.environ, "OMP_THREAD_LIMIT": "2"}) if found else None


def tool_version(cmd: list[str], env: dict | None = None) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        return "unavailable"


MIN_OCR_WORD_PX = 5     # a "word" lower than this in the frame is a dashed line or an arrowhead, not readable text


def tsv_text(tsv: str, min_px: int = MIN_OCR_WORD_PX) -> str:
    """Rebuild OCR text from tesseract TSV, one line per OCR line, dropping words lower than min_px pixels: a dashed
    edge reads as '£6 eee' at 2 px high, which no viewer can read and which tripped the money pattern."""
    lines: dict[tuple, list[str]] = {}
    for row in tsv.splitlines()[1:]:
        f = row.split("\t")
        if len(f) < 12 or not f[11].strip():
            continue
        try:
            height = int(f[9])
        except ValueError:
            continue
        if height < min_px:
            continue
        lines.setdefault((f[2], f[3], f[4]), []).append(f[11])
    return "\n".join(" ".join(words) for words in lines.values())


def ocr_image(path: Path, tess: tuple[list[str], dict]) -> str:
    cmd, env = tess
    out = subprocess.run(cmd + [str(path), "stdout", "--psm", "11", "-l", "eng", "tsv"], capture_output=True,
                         text=True, env=env, timeout=300)
    return tsv_text(out.stdout)


def edit1(a: str, b: str) -> bool:
    """True when a and b differ by at most one insert, delete or substitution."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = j = diff = 0
    while i < len(a) and j < len(b):
        if a[i] != b[j]:
            diff += 1
            if diff > 1:
                return False
            if len(a) == len(b):
                i += 1
            j += 1
            continue
        i += 1
        j += 1
    return diff + (len(b) - j) <= 1


def fuzzy_hits(text: str, terms: list[str], where: str) -> list[Hit]:
    """OCR misreads one letter now and then: a single-word deny term of 6+ letters also matches at edit distance 1."""
    words = set(re.findall(r"[a-z0-9]+", text.lower()))
    joined = re.sub(r"[^a-z0-9]", "", text.lower())
    hits = []
    for term in terms:
        t = re.sub(r"[^a-z0-9]", "", term.lower())
        if len(t) < 6:
            continue
        if " " in term.strip():
            if t in joined:
                hits.append(Hit("L3", "deny:fuzzy", where, term[:2] + "…"))
            continue
        if any(edit1(t, w) for w in words if abs(len(w) - len(t)) <= 1):
            hits.append(Hit("L3", "deny:fuzzy", where, term[:2] + "…"))
    return hits


def check_ocr(images: list[Path], patterns: list[Pattern], terms: list[str], ocr=None) -> tuple[list[Hit], str]:
    """Layer 3. `ocr` (path -> text) is injectable for tests; by default the local tesseract. Returns (hits, status)."""
    if ocr is None:
        tess = tesseract_cmd()
        if tess is None:
            return [], "SKIPPED (no tesseract: run setup.sh); layer 2 DOM check is the only pixel-level guard"
        ocr = lambda p: ocr_image(p, tess)  # noqa: E731
    hits = []
    for img in images:
        text = ocr(img)
        hits += scan_text(text, img.name, patterns, layer="L3")
        hits += fuzzy_hits(text, terms, img.name)
    return hits, f"ran on {len(images)} images"


# ---------------------------------------------------------------------------------------------------------- layer 4
ALLOWED_TAGS = {"major_brand", "minor_version", "compatible_brands", "language", "handler_name", "vendor_id", "title",
                "encoder"}
NEUTRAL_HANDLERS = {"VideoHandler", "SoundHandler", "SubtitleHandler", ""}


def ffprobe_tags(mp4: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-show_chapters", "-of", "json",
                          str(mp4)], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def metadata_hits(info: dict, where: str, patterns: list[Pattern]) -> list[Hit]:
    hits = []
    blocks = [("format", info.get("format", {}).get("tags", {}))]
    blocks += [(f"stream{s.get('index')}", s.get("tags", {})) for s in info.get("streams", [])]
    blocks += [(f"chapter{c.get('id')}", c.get("tags", {})) for c in info.get("chapters", [])]
    for name, tags in blocks:
        for k, v in (tags or {}).items():
            if k not in ALLOWED_TAGS:
                hits.append(Hit("L4", "metadata:tag", f"{where}:{name}", k))
            if k == "encoder" and not str(v).startswith("Lavf") and not str(v).startswith("Lavc"):
                hits.append(Hit("L4", "metadata:encoder", f"{where}:{name}", str(v)))
            if k == "handler_name" and v not in NEUTRAL_HANDLERS:
                hits.append(Hit("L4", "metadata:handler", f"{where}:{name}", str(v)))
            hits += scan_text(f"{k}={v}", f"{where}:{name}", patterns, layer="L4")
    return hits


ARTIFACT_TEXT = {".srt", ".vtt", ".txt", ".md", ".json", ".ass"}


def check_artifacts(folder: Path, patterns: list[Pattern], probe=ffprobe_tags,
                    skip_names: tuple[str, ...] = ()) -> list[Hit]:
    """Layer 4 over a delivery folder: every file and folder name, every text artifact, every MP4's metadata."""
    hits = []
    for p in sorted(folder.rglob("*")):
        rel = str(p.relative_to(folder))
        if p.name in skip_names:
            continue
        hits += scan_text(rel.replace("/", " / "), f"name:{rel}", patterns, layer="L4")
        if p.is_file() and p.suffix.lower() in ARTIFACT_TEXT:
            hits += scan_text(p.read_text(encoding="utf-8", errors="replace"), rel, patterns, layer="L4")
        if p.is_file() and p.suffix.lower() in {".mp4", ".m4a", ".mp3"}:
            hits += metadata_hits(probe(p), rel, patterns)
    return hits


# ----------------------------------------------------------------------------------------------------------- report
def report(hits: list[Hit], label: str) -> int:
    for h in hits:
        print("GATE HIT " + h.line(), file=sys.stderr)
    print(f"{label}: {'FAIL' if hits else 'PASS'} ({len(hits)} hits)")
    return 1 if hits else 0


def counts(hits: list[Hit]) -> dict:
    out: dict[str, int] = {}
    for h in hits:
        out[h.category] = out.get(h.category, 0) + 1
    return out


def main(argv: list[str]) -> int:
    def opt(name):
        if name in argv:
            i = argv.index(name)
            val = argv[i + 1]
            del argv[i:i + 2]
            return val
        return None
    priv = private_dir(opt("--private"))
    ws = opt("--workspace")
    no_ngram = "--no-ngram" in argv
    argv = [a for a in argv if a != "--no-ngram"]
    if not argv:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    patterns = load_patterns(priv)
    if cmd == "text":
        texts = {a: Path(a).read_text(encoding="utf-8") for a in args}
        workspace = Path(ws).resolve() if ws else default_workspace()
        return report(check_texts(texts, patterns, workspace, load_allow(priv), ngram=not no_ngram), "L1 text")
    if cmd == "patterns-json":
        Path(args[0]).write_text(json.dumps(patterns_json(patterns)), encoding="utf-8")
        return 0
    if cmd == "dom":
        hits = []
        for a in args:
            hits += scan_text(dom_dump_texts(json.loads(Path(a).read_text(encoding="utf-8"))), Path(a).name,
                              patterns, layer="L2")
        return report(hits, "L2 dom")
    if cmd == "ocr":
        hits, status = check_ocr([Path(a) for a in args], patterns, literal_terms(priv))
        print(f"L3 ocr: {status}")
        return report(hits, "L3 ocr")
    if cmd == "artifacts":
        return report(check_artifacts(Path(args[0]), patterns), "L4 artifacts")
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
