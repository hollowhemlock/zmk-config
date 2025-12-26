"""CSS generation for corner legend styling."""

from ..config import ThemeColors

# CSS template for corner legends
# Uses string formatting for color and size substitution
CORNER_CSS_TEMPLATE = """
/* Base colors - !important overrides keymap-drawer defaults */
rect.key {{ fill: {bg} !important; }}
rect.combo, rect.combo-separate {{ fill: {combo_bg} !important; }}
text, use {{ fill: {text}; }}
/* Corner legend styles for merged view */
text.tl {{
    text-anchor: start;
    dominant-baseline: hanging;
    font-size: {glyph_size}px;
    fill: {tl};
}}
text.tr {{
    text-anchor: end;
    dominant-baseline: hanging;
    font-size: {glyph_size}px;
    fill: {tr};
}}
text.bl {{
    text-anchor: start;
    dominant-baseline: text-after-edge;
    font-size: {glyph_size}px;
    fill: {bl};
}}
text.br {{
    text-anchor: end;
    dominant-baseline: text-after-edge;
    font-size: {glyph_size}px;
    fill: {br};
}}
/* Corner glyph/icon colors */
use.tl, .tl path {{ fill: {tl}; }}
use.tr, .tr path {{ fill: {tr}; }}
use.bl, .bl path {{ fill: {bl}; }}
use.br, .br path {{ fill: {br}; }}
/* Layer activator keys */
.layer-tl text, .layer-tl use {{ fill: {tl}; }}
.layer-tr text, .layer-tr use {{ fill: {tr}; }}
.layer-bl text, .layer-bl use {{ fill: {bl}; }}
.layer-br text, .layer-br use {{ fill: {br}; }}
/* Held key text */
text.held-tl {{ fill: {tl}; }}
text.held-tr {{ fill: {tr}; }}
text.held-bl {{ fill: {bl}; }}
text.held-br {{ fill: {br}; }}
/* Hidden corner elements (e.g., modifiers) */
.hidden {{ fill: transparent !important; }}
"""


def generate_corner_css(colors: ThemeColors, glyph_size: int = 11) -> str:
    """Generate CSS for corner legend styling.

    Args:
        colors: Theme colors for corners and backgrounds
        glyph_size: Font size in pixels for corner text/glyphs

    Returns:
        CSS string to inject into SVG
    """
    return CORNER_CSS_TEMPLATE.format(
        tl=colors.tl,
        tr=colors.tr,
        bl=colors.bl,
        br=colors.br,
        text=colors.text,
        bg=colors.bg,
        combo_bg=colors.get_combo_bg(),
        glyph_size=glyph_size,
    )
