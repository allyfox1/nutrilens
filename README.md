# NutriLens: Semantic Search over NIH Nutrition Fact Sheets

Search NIH nutrient fact sheets by meaning, not just keywords. Ask "which nutrients support bone health?" and get the most relevant passages, even when the exact words don't match.

https://nutrilens-search.streamlit.app

## What it does

- Searches 60+ NIH Office of Dietary Supplements fact sheets covering vitamins, minerals, and supplement topics
- Returns the best-matching passages with a match score and a link to the full fact sheet
- Filters by nutrient and by reading level (consumer vs. health professional)

## How it works

1. **Collect:** fact sheets are downloaded through the official NIH ODS API (`download_docs.py`)
2. **Chunk:** each sheet is split into passages along line boundaries so nothing is cut mid-sentence
3. **Embed and store:** passages are converted to vector embeddings and stored in a ChromaDB vector database (`build_index.py`)
4. **Search:** a question is embedded the same way, and the closest passages are returned, with at most two per fact sheet so results stay varied (`app.py`)

## Limitations

- This is retrieval only. It shows source passages rather than generating answers, so there is no LLM and no paid API.
- Passages can include glossary text or table fragments from the original sheets.
- The match percentage is an approximate similarity score, not a calibrated probability.
- Educational information only, not medical advice.

## Running locally

```bash
pip install -r requirements.txt
python download_docs.py
python build_index.py
streamlit run app.py
```

## Tech stack

Python · ChromaDB · Streamlit · BeautifulSoup · NIH ODS API