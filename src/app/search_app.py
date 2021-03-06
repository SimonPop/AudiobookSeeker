import streamlit as st
import sys, os

path2add = os.path.normpath(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
)
if not (path2add in sys.path):
    sys.path.append(path2add)

from search.search_engine import SearchEngine

engine = SearchEngine("../../embeddings.pt", "../../data.pt")

st.title("📚 Audible Book Search Engine")

options = st.multiselect(
    "What books did you like recently?",
    engine.all_titles(),
    [],
)

if st.button("🔎 Search"):
    recommendations, scores = engine.search(options)
    for i, (recommendation, score) in enumerate(zip(recommendations, scores)):
        c = st.container()
        c.write("{}. {}".format(i + 1, recommendation))
        c.progress(1 - float(score))
