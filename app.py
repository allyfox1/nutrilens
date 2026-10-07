import html
import re
import streamlit as st
from build_index import get_collection

st.set_page_config(page_title="NutriLens", page_icon="🌿")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Quicksand', sans-serif; }
.result-card { background:#F1F7EF; border:1px solid #B5CDB1; border-radius:16px;
  padding:16px 20px; margin-bottom:14px; box-shadow:0 2px 8px rgba(31,81,48,0.10); }
.result-card h4 { color:#1F5130; margin:0 0 8px 0; font-weight:700; }
.result-card p { color:#25382B; margin:10px 0; line-height:1.55; font-size:0.95rem; }
.result-card a { color:#1F5130; font-weight:700; text-decoration:none; }
.match-track { background:#C9DCC6; border-radius:8px; height:8px; width:100%; }
.match-fill { background:#1F5130; border-radius:8px; height:8px; }
.match-label { color:#3C5A44; font-size:0.8rem; margin-top:3px; }
.pill { display:inline-block; background:#C9DCC6; color:#1F5130; border-radius:10px;
  padding:2px 10px; font-size:0.72rem; font-weight:700; margin-left:8px;
  vertical-align:middle; }
</style>
""", unsafe_allow_html=True)

LOGO = (
    '<svg width="46" height="46" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="32" cy="32" r="30" fill="#1F5130"/>'
    '<path d="M18 44c0-14 10-24 28-26-1 17-9 27-23 27-2 0-4 0-5-1z" fill="#A9D3A0"/>'
    '<path d="M20 44c8-6 14-12 20-20" stroke="#1F5130" stroke-width="2.5" '
    'fill="none" stroke-linecap="round"/>'
    "</svg>"
)


def pretty(name):
    special = {
        "Omega3FattyAcids": "Omega-3 Fatty Acids",
        "MVMS": "Multivitamin/mineral Supplements",
        "WYNTK": "Dietary Supplements: What You Need to Know",
        "ExerciseAndAthleticPerformance": "Exercise and Athletic Performance",
        "ImmuneFunction": "Immune Function",
        "WeightLoss": "Weight Loss",
        "PantothenicAcid": "Pantothenic Acid",
    }
    return special.get(name, re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name))


@st.cache_resource
def load():
    collection = get_collection()
    metas = collection.get(include=["metadatas"])["metadatas"]
    return collection, sorted({m["source"] for m in metas})


collection, all_sources = load()


def search(query, n, sources, levels, min_match, per_source=2):
    conds = []
    if sources:
        conds.append({"source": {"$in": sources}})
    if levels:
        conds.append({"level": {"$in": levels}})
    where = None
    if len(conds) == 1:
        where = conds[0]
    elif len(conds) > 1:
        where = {"$and": conds}
    res = collection.query(query_texts=[query], n_results=n * 4, where=where)
    hits, counts = [], {}
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        match = max(0.0, 1 - dist / 2)  # approximate similarity, 0 to 1
        src = meta["source"]
        if match < min_match or counts.get(src, 0) >= per_source:
            continue
        counts[src] = counts.get(src, 0) + 1
        hits.append((doc, meta, match))
        if len(hits) == n:
            break
    return hits


EXAMPLES = [
    "What foods are high in iron?",
    "What is the upper limit for zinc?",
    "Which nutrients support bone health?",
    "What are signs of low vitamin B12?",
]
if "query" not in st.session_state:
    st.session_state["query"] = ""


def use_example(q):
    st.session_state["query"] = q


with st.sidebar:
    st.header("Filters")
    chosen = st.multiselect("Limit to nutrients", all_sources, format_func=pretty)
    levels = st.multiselect(
        "Reading level", ["Consumer", "Health Professional"],
        help="Leave empty to search both.",
    )
    n_results = st.slider("Number of results", 1, 8, 4)
    min_match = st.slider("Minimum match (%)", 0, 60, 25) / 100

st.markdown(
    '<div style="display:flex;align-items:center;gap:12px;">'
    f"{LOGO}"
    '<h1 style="margin:0;color:#1F5130;font-weight:700;">NutriLens</h1>'
    "</div>",
    unsafe_allow_html=True,
)
st.caption("Search NIH nutrient fact sheets by meaning, not just keywords.")

query = st.text_input(
    "Ask a nutrition question", key="query", placeholder="What foods are high in iron?"
)
st.write("Or try one:")
cols = st.columns(2)
for i, ex in enumerate(EXAMPLES):
    cols[i % 2].button(
        ex, key=f"ex{i}", on_click=use_example, args=(ex,), use_container_width=True
    )

if query:
    hits = search(query, n_results, chosen, levels, min_match)
    if not hits:
        st.info(
            "No strong matches. Try rewording your question, "
            "or lower the minimum match in the sidebar."
        )
    for doc, meta, match in hits:
        src = meta["source"]
        text = doc[len(src) + 2:] if doc.startswith(src + ": ") else doc
        text = " ".join(text.split())
        url = meta.get("url", f"https://ods.od.nih.gov/factsheets/{src}-Consumer/")
        pill = (
            '<span class="pill">Health professional</span>'
            if meta.get("level") == "Health Professional"
            else ""
        )
        pct = int(match * 100)
        card = (
            '<div class="result-card">'
            f"<h4>{html.escape(pretty(src))}{pill}</h4>"
            f'<div class="match-track"><div class="match-fill" style="width:{pct}%"></div></div>'
            f'<div class="match-label">{pct}% match</div>'
            f"<p>{html.escape(text)}</p>"
            f'<a href="{html.escape(url)}" target="_blank">Read the full fact sheet →</a>'
            "</div>"
        )
        st.markdown(card, unsafe_allow_html=True)

st.divider()
st.caption(
    "Educational information only, not medical advice. "
    "Source: NIH Office of Dietary Supplements fact sheets."
)