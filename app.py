import streamlit as st
import openai
import json
import os
from pathlib import Path

st.set_page_config(
    page_title="Competitor Copy Decoder",
    page_icon="🔍",
    layout="wide"
)

# ── styles ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }
h1, h2, h3, .big-title { font-family: 'Syne', sans-serif !important; }

.stApp { background: #0d0d0d; color: #e8e4d9; }

.block-container { padding: 2rem 3rem; max-width: 1400px; }

.brand-card {
    background: #1a1a1a;
    border: 1px solid #2e2e2e;
    border-radius: 4px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.brand-card.highlight {
    border-color: #c8ff00;
    background: #141a00;
}
.score-pill {
    display: inline-block;
    background: #c8ff00;
    color: #0d0d0d;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.4rem;
    padding: 0.2rem 0.8rem;
    border-radius: 2px;
    margin-bottom: 0.5rem;
}
.score-pill.low { background: #ff4f4f; color: #fff; }
.score-pill.mid { background: #ffc94f; color: #0d0d0d; }
.tag {
    display: inline-block;
    border: 1px solid #444;
    color: #aaa;
    font-size: 0.72rem;
    padding: 0.1rem 0.5rem;
    border-radius: 2px;
    margin: 0.15rem;
}
.tag.own { border-color: #c8ff00; color: #c8ff00; }
.section-label {
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #666;
    margin-bottom: 0.4rem;
}
.gap-item {
    background: #1e1200;
    border-left: 3px solid #ffc94f;
    padding: 0.6rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.88rem;
}
.opp-item {
    background: #001a0a;
    border-left: 3px solid #c8ff00;
    padding: 0.6rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.88rem;
}
hr { border-color: #2e2e2e; }
</style>
""", unsafe_allow_html=True)

MEMORY_FILE = Path("brand_voice.json")

def load_brand_memory():
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {}

def save_brand_memory(data: dict):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_client(api_key):
    return openai.OpenAI(api_key=api_key)

def analyze_copy(client, brand_name, brand_copy, competitors: list[dict]) -> dict:
    competitors_block = "\n\n".join(
        f"COMPETITOR {i+1} — {c['name']}:\n{c['copy']}"
        for i, c in enumerate(competitors)
    )
    prompt = f"""You are a senior brand strategist. Analyze the following copy samples and return a JSON object.

YOUR BRAND — {brand_name}:
{brand_copy}

{competitors_block}

Return ONLY valid JSON (no markdown) with this exact structure:
{{
  "brands": [
    {{
      "name": "string",
      "is_own": true/false,
      "tone_score": 0-100,
      "clarity_score": 0-100,
      "emotional_pull_score": 0-100,
      "urgency_score": 0-100,
      "audience_fit_score": 0-100,
      "overall_score": 0-100,
      "tone_adjectives": ["list", "of", "3-5", "words"],
      "power_words": ["list", "of", "up", "to", "6", "words"],
      "cta_style": "one sentence description",
      "audience_signals": "one sentence",
      "emotional_register": "one sentence",
      "weakness": "one sentence on biggest gap vs competitors"
    }}
  ],
  "gaps": ["gap1", "gap2", "gap3"],
  "opportunities": ["opp1", "opp2", "opp3"],
  "summary": "2-3 sentence strategic summary"
}}"""

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        response_format={"type": "json_object"}
    )
    return json.loads(resp.choices[0].message.content)

def generate_brand_copy(client, brand_name, competitors: list[dict]) -> str:
    comp_block = "\n\n".join(
        f"COMPETITOR — {c['name']}:\n{c['copy']}"
        for c in competitors
    )
    prompt = f"""Based on these competitor copy samples, generate a short brand copy sample (2-3 paragraphs) for a brand called "{brand_name}". 
Make it distinct from the competitors but in the same market space. Be creative, punchy, and strategic.

{comp_block}

Return only the copy text, no explanations."""
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    return resp.choices[0].message.content.strip()

def score_color(s):
    if s >= 70: return ""
    if s >= 45: return "mid"
    return "low"

# ── sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-family:Syne,sans-serif;font-size:1.3rem;font-weight:800;color:#c8ff00;margin-bottom:0.2rem;'>COPY DECODER</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.75rem;color:#666;margin-bottom:1.5rem;letter-spacing:0.05em;'>Brand Intelligence Tool</div>", unsafe_allow_html=True)

    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.markdown("---")

    memory = load_brand_memory()
    brand_name = st.text_input("Your Brand Name", value=memory.get("brand_name", ""), placeholder="e.g. Acme Co.")

    st.markdown("---")
    st.markdown("<div class='section-label'>Brand Voice Memory</div>", unsafe_allow_html=True)
    if memory.get("brand_name"):
        st.success(f"✓ Voice saved for **{memory['brand_name']}**")
        if st.button("Clear memory", use_container_width=True):
            MEMORY_FILE.unlink(missing_ok=True)
            st.rerun()
    else:
        st.caption("No brand saved yet. Run an analysis to save.")

# ── main ─────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='font-family:Syne,sans-serif;font-size:2.6rem;font-weight:800;margin-bottom:0;'>Competitor Copy Decoder</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#666;font-size:0.85rem;margin-bottom:2rem;'>Paste your copy + up to 3 competitors. Get a strategic breakdown instantly.</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["⚡ Analyze", "📖 Saved Voice"])

with tab1:
    col_own, col_comp = st.columns([1, 1], gap="large")

    with col_own:
        st.markdown("<div class='section-label'>Your Brand</div>", unsafe_allow_html=True)
        own_copy = st.text_area(
            "Your copy",
            value=memory.get("brand_copy", ""),
            height=180,
            placeholder="Paste your homepage copy, tagline, or ad copy here...",
            label_visibility="collapsed"
        )
        if not own_copy.strip():
            st.caption("No copy yet? Add competitors first, then click Generate below.")

    with col_comp:
        st.markdown("<div class='section-label'>Competitors (up to 3)</div>", unsafe_allow_html=True)
        competitors = []
        for i in range(3):
            with st.expander(f"Competitor {i+1}", expanded=(i == 0)):
                cname = st.text_input(f"Name", key=f"cname_{i}", placeholder=f"e.g. Rival Brand {i+1}")
                ccopy = st.text_area(f"Copy", key=f"ccopy_{i}", height=100,
                                     placeholder="Paste their homepage/ad copy...", label_visibility="collapsed")
                if cname.strip() and ccopy.strip():
                    competitors.append({"name": cname.strip(), "copy": ccopy.strip()})

    st.markdown("<br>", unsafe_allow_html=True)
    gcol, acol = st.columns([1, 1])

    with gcol:
        gen_disabled = not (api_key and brand_name and competitors)
        if st.button("✨ Generate my copy from competitors", disabled=gen_disabled, use_container_width=True):
            with st.spinner("Generating your brand copy..."):
                client = get_client(api_key)
                own_copy = generate_brand_copy(client, brand_name, competitors)
                mem = load_brand_memory()
                mem["brand_name"] = brand_name
                mem["brand_copy"] = own_copy
                save_brand_memory(mem)
                st.rerun()

    with acol:
        run_disabled = not (api_key and brand_name and own_copy.strip() and competitors)
        run = st.button("🔍 Decode & Compare", disabled=run_disabled, use_container_width=True, type="primary")

    if run:
        with st.spinner("Analyzing copy across all brands..."):
            try:
                client = get_client(api_key)
                result = analyze_copy(client, brand_name, own_copy, competitors)

                # save brand voice memory
                mem = load_brand_memory()
                mem["brand_name"] = brand_name
                mem["brand_copy"] = own_copy
                own_brand_data = next((b for b in result["brands"] if b["is_own"]), None)
                if own_brand_data:
                    mem["last_analysis"] = own_brand_data
                save_brand_memory(mem)

                st.markdown("---")
                st.markdown("<h3 style='font-family:Syne,sans-serif;'>Results</h3>", unsafe_allow_html=True)

                # Score cards
                cols = st.columns(len(result["brands"]))
                for idx, brand in enumerate(result["brands"]):
                    with cols[idx]:
                        card_class = "brand-card highlight" if brand["is_own"] else "brand-card"
                        sc = brand["overall_score"]
                        pill_class = score_color(sc)
                        tags = "".join(
                            f'<span class="tag own">{t}</span>' if brand["is_own"] else f'<span class="tag">{t}</span>'
                            for t in brand.get("tone_adjectives", [])
                        )
                        power = "".join(f'<span class="tag">{w}</span>' for w in brand.get("power_words", []))
                        own_badge = " <span style='font-size:0.65rem;background:#c8ff00;color:#0d0d0d;padding:0.1rem 0.4rem;border-radius:2px;'>YOU</span>" if brand["is_own"] else ""
                        st.markdown(f"""
<div class="{card_class}">
  <div style='font-family:Syne,sans-serif;font-weight:700;font-size:1rem;margin-bottom:0.6rem;'>{brand['name']}{own_badge}</div>
  <div class='score-pill {pill_class}'>{sc}/100</div>
  <div class='section-label' style='margin-top:0.8rem;'>Tone</div>{tags}
  <div class='section-label' style='margin-top:0.8rem;'>Power Words</div>{power}
  <div class='section-label' style='margin-top:0.8rem;'>CTA Style</div>
  <div style='font-size:0.82rem;color:#bbb;'>{brand.get('cta_style','')}</div>
  <div class='section-label' style='margin-top:0.8rem;'>Audience</div>
  <div style='font-size:0.82rem;color:#bbb;'>{brand.get('audience_signals','')}</div>
  <div class='section-label' style='margin-top:0.8rem;'>Emotional Register</div>
  <div style='font-size:0.82rem;color:#bbb;'>{brand.get('emotional_register','')}</div>
  <div class='section-label' style='margin-top:0.8rem;'>Biggest Gap</div>
  <div style='font-size:0.82rem;color:#ff8080;'>{brand.get('weakness','')}</div>
</div>""", unsafe_allow_html=True)

                # Score breakdown table
                st.markdown("<br><div class='section-label'>Score Breakdown</div>", unsafe_allow_html=True)
                metrics = ["tone_score", "clarity_score", "emotional_pull_score", "urgency_score", "audience_fit_score"]
                metric_labels = ["Tone", "Clarity", "Emotional Pull", "Urgency", "Audience Fit"]
                header_cols = st.columns([2] + [1] * len(result["brands"]))
                header_cols[0].markdown("<div style='font-size:0.75rem;color:#555;'>Metric</div>", unsafe_allow_html=True)
                for i, b in enumerate(result["brands"]):
                    header_cols[i+1].markdown(f"<div style='font-size:0.75rem;color:#555;'>{b['name']}</div>", unsafe_allow_html=True)
                for m, label in zip(metrics, metric_labels):
                    row = st.columns([2] + [1] * len(result["brands"]))
                    row[0].markdown(f"<div style='font-size:0.8rem;padding:0.3rem 0;'>{label}</div>", unsafe_allow_html=True)
                    for i, b in enumerate(result["brands"]):
                        val = b.get(m, 0)
                        color = "#c8ff00" if val >= 70 else ("#ffc94f" if val >= 45 else "#ff4f4f")
                        row[i+1].markdown(f"<div style='font-size:0.85rem;font-weight:700;color:{color};padding:0.3rem 0;'>{val}</div>", unsafe_allow_html=True)

                # Gaps & Opportunities
                st.markdown("<br>", unsafe_allow_html=True)
                gcol2, ocol2 = st.columns(2, gap="large")
                with gcol2:
                    st.markdown("<div class='section-label'>Gaps to Address</div>", unsafe_allow_html=True)
                    for gap in result.get("gaps", []):
                        st.markdown(f"<div class='gap-item'>⚠ {gap}</div>", unsafe_allow_html=True)
                with ocol2:
                    st.markdown("<div class='section-label'>Opportunities</div>", unsafe_allow_html=True)
                    for opp in result.get("opportunities", []):
                        st.markdown(f"<div class='opp-item'>→ {opp}</div>", unsafe_allow_html=True)

                # Summary
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"""
<div class='brand-card'>
  <div class='section-label'>Strategic Summary</div>
  <div style='font-size:0.9rem;line-height:1.7;color:#ccc;'>{result.get('summary','')}</div>
</div>""", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    memory = load_brand_memory()
    if not memory.get("brand_name"):
        st.info("No brand voice saved yet. Run your first analysis to save it.")
    else:
        st.markdown(f"<h3 style='font-family:Syne,sans-serif;'>{memory['brand_name']}</h3>", unsafe_allow_html=True)
        if memory.get("brand_copy"):
            st.markdown("<div class='section-label'>Saved Copy</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='brand-card' style='font-size:0.87rem;line-height:1.7;color:#ccc;'>{memory['brand_copy']}</div>", unsafe_allow_html=True)
        if memory.get("last_analysis"):
            la = memory["last_analysis"]
            st.markdown("<div class='section-label' style='margin-top:1.5rem;'>Last Analysis Snapshot</div>", unsafe_allow_html=True)
            tags = "".join(f'<span class="tag own">{t}</span>' for t in la.get("tone_adjectives", []))
            power = "".join(f'<span class="tag">{w}</span>' for w in la.get("power_words", []))
            st.markdown(f"""
<div class='brand-card highlight'>
  <div class='score-pill'>{la.get('overall_score','?')}/100</div>
  <div class='section-label' style='margin-top:0.8rem;'>Tone</div>{tags}
  <div class='section-label' style='margin-top:0.8rem;'>Power Words</div>{power}
  <div class='section-label' style='margin-top:0.8rem;'>CTA Style</div>
  <div style='font-size:0.82rem;color:#bbb;'>{la.get('cta_style','')}</div>
</div>""", unsafe_allow_html=True)

