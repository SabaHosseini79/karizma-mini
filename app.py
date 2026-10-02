"""صفحه‌ی چت:   streamlit run app.py"""
import streamlit as st

import rag

st.set_page_config(page_title="دستیار کارگزاری کاریزما", page_icon="💬")
st.markdown(
    "<style>.stApp,.stChatMessage,.stMarkdown,[data-testid='stChatInput']{direction:rtl;text-align:right}</style>",
    unsafe_allow_html=True,
)
st.title("💬 دستیار کارگزاری کاریزما")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("sources"):
            with st.expander("منابع"):
                for s in m["sources"]:
                    st.markdown(f"- **{s['heading']}** (`{s['doc']}`)")

if question := st.chat_input("سؤال خود را بنویسید…"):
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("در حال بررسی…"):
            try:
                answer, sources = rag.ask(question, history)
            except Exception as e:
                answer, sources = f"خطا: {e}", []
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
