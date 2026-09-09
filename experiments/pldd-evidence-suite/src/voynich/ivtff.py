"""A source-retaining structural parser for IVTFF 2.x files.

The parser retains the original input bytes unchanged. ``Document.emit()``
returns those retained bytes; it is not a semantic AST reserializer. Parsed
views expose page metadata, loci, and an explicitly conservative tokenization
for analysis.

Specification: https://www.voynich.nu/software/ivtt/IVTFF_format.pdf
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable, Iterator


class IVTFFParseError(ValueError):
    """Raised when a source cannot be represented without guessing."""


_HEADER_RE = re.compile(
    rb"^#=IVTFF (?P<alphabet>.{4}) (?P<version>\S+) (?P<origin>[MDA])"
    rb"(?P<extras>(?: \S+)*)$"
)
_LOCUS_RE = re.compile(
    r"^<(?P<page>[^.,>]+)\.(?P<number>\d+),(?P<locator>[@+*=\&~/!])"
    r"(?P<locus_type>[A-Z][a-z0-9])(?:;(?P<transcriber>.))?>"
    r"(?P<spacing>\s*)(?P<text>.*)$"
)
_ALT_LOCUS_RE = re.compile(
    r"^<(?P<page_code>[A-Z]{2})(?P<number>\d{3})(?:;(?P<transcriber>.))?>"
    r"(?P<spacing>\s*)(?P<text>.*)$"
)
_PAGE_RE = re.compile(
    r"^<(?P<page>[^>]+)>(?:\s*<!\s*(?P<variables>.*?)\s*>)?\s*$"
)
_VARIABLE_RE = re.compile(r"\$(?P<name>[A-Z])=(?P<value>[^\s>]+)")
_TEXT_TAG_RE = re.compile(r"<@(?P<name>[A-Z])=(?P<value>[^>]+)>")
_LIGATURE_RE = re.compile(r"\{([^{}]*)\}")
_INLINE_COMMENT_RE = re.compile(r"<[^>]*>")
_PAGE_NAME_RE = re.compile(r"^(?:fRos|f\d+[rv]\d*)$")
_VALID_LOCUS_TYPES = frozenset(
    {
        "P0", "P1", "Pb", "Pc", "Pr", "Pt",
        "L0", "La", "Lc", "Lf", "Ln", "Lp", "Ls", "Lt", "Lx", "Lz",
        "Ca", "Cc", "Ri", "Ro",
    }
)


@dataclass(frozen=True)
class Header:
    alphabet: str
    version: str
    origin: str
    extras: tuple[str, ...]
    raw: bytes


@dataclass(frozen=True)
class PhysicalLine:
    """A physical source line without its line ending."""

    number: int
    raw: bytes


@dataclass(frozen=True)
class Locus:
    identifier: str
    page_id: str
    number: int
    locator: str | None
    locus_type: str | None
    transcriber: str | None
    text: str
    effective_variables: dict[str, str]
    paragraph_index: int | None
    paragraph_start: bool
    paragraph_end: bool
    physical_lines: tuple[PhysicalLine, ...]

    @property
    def generic_type(self) -> str | None:
        return self.locus_type[0] if self.locus_type else None


@dataclass
class Page:
    page_id: str
    variables: dict[str, str]
    header_line: PhysicalLine | None
    alternative_identifiers: bool = False
    comments: list[str] = field(default_factory=list)
    loci: list[Locus] = field(default_factory=list)


@dataclass(frozen=True)
class Document:
    header: Header
    pages: tuple[Page, ...]
    preamble_comments: tuple[str, ...]
    source: bytes

    def emit(self) -> bytes:
        """Return the retained input bytes, not a structure-derived serialization."""

        return self.source

    @property
    def loci(self) -> tuple[Locus, ...]:
        return tuple(locus for page in self.pages for locus in page.loci)


@dataclass(frozen=True)
class ExcludedComponent:
    text: str
    reason: str


@dataclass(frozen=True)
class TokenComponent:
    """One candidate word delimited only by a certain IVTFF boundary."""

    source: str
    token: str | None
    exclusion_reason: str | None

    @property
    def accepted(self) -> bool:
        return self.token is not None


@dataclass(frozen=True)
class Tokenization:
    components: tuple[TokenComponent, ...]

    @property
    def tokens(self) -> tuple[str, ...]:
        return tuple(item.token for item in self.components if item.token is not None)

    @property
    def excluded(self) -> tuple[ExcludedComponent, ...]:
        return tuple(
            ExcludedComponent(item.source, item.exclusion_reason or "unknown")
            for item in self.components
            if item.token is None
        )


@dataclass(frozen=True)
class Paragraph:
    page_id: str
    index: int
    loci: tuple[Locus, ...]

    def components(self) -> tuple[TokenComponent, ...]:
        return tuple(
            component
            for locus in self.loci
            for component in tokenize_certain_basic_eva(locus.text).components
        )

    def tokens(self) -> tuple[str, ...]:
        return tuple(
            component.token
            for component in self.components()
            if component.token is not None
        )


def _physical_lines(source: bytes) -> list[PhysicalLine]:
    # splitlines() preserves all content except the separator; the original
    # bytes remain on Document.source and are therefore always re-emittable.
    return [
        PhysicalLine(number=index, raw=line)
        for index, line in enumerate(source.splitlines(), start=1)
    ]


def _logical_lines(lines: list[PhysicalLine]) -> Iterator[tuple[bytes, tuple[PhysicalLine, ...]]]:
    index = 0
    while index < len(lines):
        first = lines[index]
        raw = first.raw
        physical = [first]

        if not raw.startswith(b"#"):
            while raw.endswith(b"/"):
                index += 1
                if index >= len(lines) or not lines[index].raw.startswith(b"/"):
                    raise IVTFFParseError(
                        f"line {physical[-1].number}: continuation is not followed by '/'")
                continuation = lines[index]
                physical.append(continuation)
                raw = raw[:-1] + continuation.raw[1:]

        yield raw, tuple(physical)
        index += 1


def _decode(raw: bytes, line_number: int) -> str:
    try:
        return raw.decode("latin-1")
    except UnicodeDecodeError as exc:  # pragma: no cover - latin-1 is total
        raise IVTFFParseError(f"line {line_number}: cannot decode source") from exc


def _scan_inline_controls(text: str, line_number: int) -> tuple[str, list[str]]:
    """Remove free comments and return only syntactically active controls."""

    output: list[str] = []
    controls: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == ">":
            raise IVTFFParseError(f"line {line_number}: unmatched '>' in locus text")
        if char != "<":
            output.append(char)
            index += 1
            continue
        end = text.find(">", index + 1)
        if end < 0:
            raise IVTFFParseError(f"line {line_number}: unclosed inline comment")
        control = text[index : end + 1]
        if control.startswith("<!"):
            # Free comments are inert, including strings resembling controls.
            pass
        elif control in {"<->", "<~>", "<%>", "<$>"} or re.fullmatch(
            r"<@[A-Z]=[^>]+>", control
        ):
            controls.append(control)
            output.append(control)
        else:
            raise IVTFFParseError(
                f"line {line_number}: invalid inline control {control!r}")
        index = end + 1
    return "".join(output), controls


def _validate_delimited(
    text: str, opening: str, closing: str, line_number: int
) -> list[str]:
    contents: list[str] = []
    start: int | None = None
    for index, char in enumerate(text):
        if char == opening:
            if start is not None:
                raise IVTFFParseError(
                    f"line {line_number}: nested {opening}{closing} group")
            start = index + 1
        elif char == closing:
            if start is None:
                raise IVTFFParseError(
                    f"line {line_number}: unmatched {closing!r}")
            contents.append(text[start:index])
            start = None
    if start is not None:
        raise IVTFFParseError(f"line {line_number}: unclosed {opening!r} group")
    return contents


def _validate_locus_text(
    text: str, line_number: int, locus_type: str | None
) -> tuple[str, list[str]]:
    active_text, controls = _scan_inline_controls(text, line_number)
    if controls.count("<%>") > 1 or controls.count("<$>") > 1:
        raise IVTFFParseError(f"line {line_number}: repeated paragraph marker")
    if "<%>" in controls and not active_text.startswith("<%>"):
        raise IVTFFParseError(f"line {line_number}: paragraph start is not first")
    if "<$>" in controls and not active_text.endswith("<$>"):
        raise IVTFFParseError(f"line {line_number}: paragraph end is not last")
    if ("<%>" in controls or "<$>" in controls) and locus_type is not None:
        if not locus_type.startswith("P"):
            raise IVTFFParseError(
                f"line {line_number}: paragraph marker on non-paragraph locus")

    glyph_text = _INLINE_COMMENT_RE.sub("", active_text)
    alternatives = _validate_delimited(glyph_text, "[", "]", line_number)
    _validate_delimited(glyph_text, "{", "}", line_number)
    for alternative in alternatives:
        if ":" not in alternative:
            raise IVTFFParseError(
                f"line {line_number}: alternative reading has fewer than two options")

    index = 0
    while index < len(glyph_text):
        if glyph_text[index] != "@":
            index += 1
            continue
        match = re.match(r"@(\d{3});", glyph_text[index:])
        if not match or not 128 <= int(match.group(1)) <= 255:
            raise IVTFFParseError(
                f"line {line_number}: invalid Extended-EVA high-ASCII code")
        index += len(match.group(0))
    return active_text, controls


def parse_ivtff(source: bytes | str) -> Document:
    """Parse IVTFF while retaining a byte-identical source representation."""

    if isinstance(source, str):
        source_bytes = source.encode("latin-1")
    else:
        source_bytes = source

    physical_lines = _physical_lines(source_bytes)
    if not physical_lines:
        raise IVTFFParseError("empty IVTFF source")

    header_match = _HEADER_RE.fullmatch(physical_lines[0].raw)
    if not header_match:
        raise IVTFFParseError("line 1: invalid IVTFF header")

    header = Header(
        alphabet=header_match.group("alphabet").decode("ascii"),
        version=header_match.group("version").decode("ascii"),
        origin=header_match.group("origin").decode("ascii"),
        extras=tuple(header_match.group("extras").decode("ascii").split()),
        raw=physical_lines[0].raw,
    )

    pages: list[Page] = []
    preamble_comments: list[str] = []
    current_page: Page | None = None
    effective_variables: dict[str, str] = {}
    active_paragraph: int | None = None
    paragraph_counter = 0
    last_locus_number: int | None = None

    logical = list(_logical_lines(physical_lines))
    for raw, source_lines in logical[1:]:
        line_number = source_lines[0].number
        text_line = _decode(raw, line_number)

        if text_line == "":
            # IVTFF normally uses '#' for blank comments, but retain a literal
            # empty line as well for byte-faithful source retention.
            if current_page is None:
                preamble_comments.append("")
            else:
                current_page.comments.append("")
            continue

        if text_line.startswith("#"):
            comment = text_line[1:].lstrip(" ")
            if current_page is None:
                preamble_comments.append(comment)
            else:
                current_page.comments.append(comment)
            continue

        locus_match = _LOCUS_RE.fullmatch(text_line)
        alt_match = _ALT_LOCUS_RE.fullmatch(text_line) if locus_match is None else None
        if locus_match or alt_match:
            if locus_match:
                if current_page is None:
                    raise IVTFFParseError(f"line {line_number}: locus before page header")
                if current_page.alternative_identifiers:
                    raise IVTFFParseError(
                        f"line {line_number}: standard and alternative locus identifiers cannot be mixed")
                page_id = locus_match.group("page")
                if page_id != current_page.page_id:
                    raise IVTFFParseError(
                        f"line {line_number}: locus page {page_id!r} does not match "
                        f"current page {current_page.page_id!r}")
                number = int(locus_match.group("number"))
                locator = locus_match.group("locator")
                locus_type = locus_match.group("locus_type")
                if locus_type not in _VALID_LOCUS_TYPES:
                    raise IVTFFParseError(
                        f"line {line_number}: invalid locus type {locus_type!r}")
                transcriber = locus_match.group("transcriber")
                locus_text = locus_match.group("text")
                identifier = text_line.split(">", 1)[0] + ">"
            else:
                assert alt_match is not None
                page_id = alt_match.group("page_code")
                if current_page is None or current_page.page_id != page_id:
                    if current_page is not None and not current_page.alternative_identifiers:
                        raise IVTFFParseError(
                            f"line {line_number}: standard and alternative locus identifiers cannot be mixed")
                    if active_paragraph is not None:
                        raise IVTFFParseError(
                            f"line {line_number}: page code changes before paragraph "
                            f"{active_paragraph} ends")
                    current_page = Page(
                        page_id=page_id,
                        variables={},
                        header_line=None,
                        alternative_identifiers=True,
                    )
                    pages.append(current_page)
                    effective_variables = {}
                    paragraph_counter = 0
                    last_locus_number = None
                elif not current_page.alternative_identifiers:
                    raise IVTFFParseError(
                        f"line {line_number}: alternative identifier appears after a page header")
                number = int(alt_match.group("number"))
                locator = None
                locus_type = None
                transcriber = alt_match.group("transcriber")
                locus_text = alt_match.group("text")
                identifier = text_line.split(">", 1)[0] + ">"

            if last_locus_number is not None and number < last_locus_number:
                raise IVTFFParseError(
                    f"line {line_number}: locus number {number} follows {last_locus_number}")
            last_locus_number = number

            active_text, controls = _validate_locus_text(
                locus_text, line_number, locus_type
            )

            for tag in _TEXT_TAG_RE.finditer(active_text):
                name, value = tag.group("name"), tag.group("value")
                if value == "@":
                    effective_variables.pop(name, None)
                else:
                    effective_variables[name] = value

            paragraph_start = "<%>" in controls
            paragraph_end = "<$>" in controls
            if paragraph_start:
                if active_paragraph is not None:
                    raise IVTFFParseError(
                        f"line {line_number}: paragraph starts before previous paragraph ends")
                paragraph_counter += 1
                active_paragraph = paragraph_counter

            paragraph_index = active_paragraph
            locus = Locus(
                identifier=identifier,
                page_id=page_id,
                number=number,
                locator=locator,
                locus_type=locus_type,
                transcriber=transcriber,
                text=locus_text,
                effective_variables=dict(effective_variables),
                paragraph_index=paragraph_index,
                paragraph_start=paragraph_start,
                paragraph_end=paragraph_end,
                physical_lines=source_lines,
            )
            current_page.loci.append(locus)

            if paragraph_end:
                if active_paragraph is None:
                    raise IVTFFParseError(f"line {line_number}: paragraph ends without a start")
                active_paragraph = None
            continue

        page_match = _PAGE_RE.fullmatch(text_line)
        if page_match:
            if any(page.alternative_identifiers for page in pages):
                raise IVTFFParseError(
                    f"line {line_number}: page headers are forbidden with alternative locus identifiers")
            if active_paragraph is not None:
                raise IVTFFParseError(
                    f"line {line_number}: page changes before paragraph {active_paragraph} ends")
            page_id = page_match.group("page")
            if not _PAGE_NAME_RE.fullmatch(page_id):
                raise IVTFFParseError(f"line {line_number}: invalid page name {page_id!r}")
            variables = {
                item.group("name"): item.group("value")
                for item in _VARIABLE_RE.finditer(page_match.group("variables") or "")
            }
            current_page = Page(
                page_id=page_id,
                variables=variables,
                header_line=source_lines[0],
                alternative_identifiers=False,
            )
            pages.append(current_page)
            effective_variables = {
                name: value for name, value in variables.items() if value != "@"
            }
            paragraph_counter = 0
            last_locus_number = None
            continue

        raise IVTFFParseError(f"line {line_number}: unrecognized IVTFF record")

    if active_paragraph is not None:
        raise IVTFFParseError(f"end of file: paragraph {active_paragraph} is not closed")

    return Document(
        header=header,
        pages=tuple(pages),
        preamble_comments=tuple(preamble_comments),
        source=source_bytes,
    )


def tokenize_certain_basic_eva(text: str) -> Tokenization:
    """Return only unambiguous, ASCII EVA word candidates.

    This view is deliberately narrower than the diplomatic transcription:

    - ``.`` and drawing interruptions are certain word boundaries;
    - a comma marks an uncertain boundary, so the entire connected component
      is excluded rather than split or joined silently;
    - alternative readings, unreadable glyphs, and Extended-EVA codes are
      excluded;
    - ligature braces are removed but their contents are retained.

    The source text is never changed, and every rejected component carries a
    reason. This function must not be used as a claim about phonetic values.
    """

    normalized = text.replace("<->", ".").replace("<~>", ".")
    normalized = _INLINE_COMMENT_RE.sub("", normalized)
    while _LIGATURE_RE.search(normalized):
        normalized = _LIGATURE_RE.sub(r"\1", normalized)
    normalized = re.sub(r"\s+", "", normalized)

    components: list[TokenComponent] = []
    for component in normalized.split("."):
        if not component:
            continue
        reason: str | None = None
        if "," in component:
            reason = "uncertain_word_space"
        elif "[" in component or "]" in component or ":" in component:
            reason = "alternative_reading"
        elif "?" in component:
            reason = "unreadable_glyph"
        elif "@" in component or ";" in component:
            reason = "extended_eva"
        elif "{" in component or "}" in component:
            reason = "malformed_ligature"
        elif re.search(r"[A-Z]", component):
            reason = "joined_eva_form"
        elif not re.fullmatch(r"[a-z']+", component):
            reason = "unsupported_symbol"

        components.append(
            TokenComponent(
                source=component,
                token=None if reason else component,
                exclusion_reason=reason,
            )
        )

    return Tokenization(tuple(components))


def iter_paragraphs(document: Document) -> Iterable[Paragraph]:
    """Yield transcriber-marked paragraphs without inventing missing ones."""

    for page in document.pages:
        grouped: dict[int, list[Locus]] = {}
        for locus in page.loci:
            if locus.generic_type == "P" and locus.paragraph_index is not None:
                grouped.setdefault(locus.paragraph_index, []).append(locus)
        for index in sorted(grouped):
            yield Paragraph(page.page_id, index, tuple(grouped[index]))
