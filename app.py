
import streamlit as st
from deep_translator import GoogleTranslator
import random
import io

st.set_page_config(page_title="英単語支援ソフト（Web版）", layout="centered")

translator = GoogleTranslator(source="ja", target="en")

# セッション状態の初期化
if "ja_list" not in st.session_state:
    st.session_state.ja_list = []
if "en_list" not in st.session_state:
    st.session_state.en_list = []
if "pairs" not in st.session_state:
    st.session_state.pairs = []
if "test_index" not in st.session_state:
    st.session_state.test_index = 0
if "testing" not in st.session_state:
    st.session_state.testing = False
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

st.title("英単語支援ソフト（Web版）")

with st.sidebar:
    st.header("セーブ/ロード")
    # 保存（ダウンロード）
    if st.button("現在のデータをダウンロード"):
        buf = io.StringIO()
        buf.write("ja_list:\n")
        for ja in st.session_state.ja_list:
            buf.write(ja + "\n")
        buf.write("en_list:\n")
        for en in st.session_state.en_list:
            buf.write(en + "\n")
        st.download_button("tango_data.txt を保存", buf.getvalue(), file_name="tango_data.txt")

    # 読み込み（アップロード）
    up = st.file_uploader("tango_data.txt を読み込む", type=["txt"])
    if up is not None:
        text = up.read().decode("utf-8")
        lines = text.splitlines()
        try:
            ja_start = lines.index("ja_list:") + 1
            en_start = lines.index("en_list:") + 1
            ja_list = [l.strip() for l in lines[ja_start:en_start-1] if l.strip()]
            en_list = [l.strip() for l in lines[en_start:] if l.strip()]
            st.session_state.ja_list = ja_list
            st.session_state.en_list = en_list
            st.success(f"読み込み完了: {len(ja_list)}件")
        except Exception as e:
            st.error(f"読み込みエラー: {e}")

st.subheader("1) 単語を入力（日本語・改行区切り）")
ja_input = st.text_area("例：\n犬\n猫\n学校", height=150)

col1, col2 = st.columns(2)
with col1:
    if st.button("この入力を追加"):
        new_words = [w.strip() for w in ja_input.splitlines() if w.strip()]
        st.session_state.ja_list.extend(new_words)
        st.success(f"{len(new_words)}件を追加しました")
with col2:
    if st.button("リストをクリア"):
        st.session_state.ja_list = []
        st.session_state.en_list = []
        st.session_state.pairs = []
        st.session_state.testing = False
        st.session_state.test_index = 0
        st.session_state.show_answer = False
        st.info("リストを空にしました")

st.divider()

st.subheader("2) 一括翻訳（ja → en）")
if st.button("翻訳を実行"):
    try:
        st.session_state.en_list = translator.translate_batch(st.session_state.ja_list) if st.session_state.ja_list else []
        st.success("翻訳しました")
    except Exception as e:
        st.error(f"翻訳中にエラー: {e}")

if st.session_state.ja_list:
    st.write("現在のペア：")
    for ja, en in zip(st.session_state.ja_list, st.session_state.en_list or [""] * len(st.session_state.ja_list)):
        st.write(f"- {ja}  →  {en}")

st.divider()

st.subheader("3) 単語テスト")
col3, col4 = st.columns(2)
with col3:
    if st.button("シャッフルしてテスト開始/再開"):
        pairs = list(zip(st.session_state.ja_list, st.session_state.en_list))
        random.shuffle(pairs)
        st.session_state.pairs = pairs
        st.session_state.testing = True
        st.session_state.test_index = 0
        st.session_state.show_answer = False
        if not pairs:
            st.warning("テストするペアがありません。")
with col4:
    if st.button("テスト終了"):
        st.session_state.testing = False
        st.session_state.show_answer = False

if st.session_state.testing and st.session_state.pairs:
    i = st.session_state.test_index
    ja, en = st.session_state.pairs[i]

    st.markdown(f"**問題 {i+1} / {len(st.session_state.pairs)}**")
    st.markdown(f"**日本語:** {ja}")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("答えを見る"):
            st.session_state.show_answer = True
    with c2:
        if st.button("次へ"):
            if st.session_state.test_index < len(st.session_state.pairs) - 1:
                st.session_state.test_index += 1
                st.session_state.show_answer = False
            else:
                st.success("テストは最後まで終了しました")
                st.session_state.testing = False
    with c3:
        if st.button("最初に戻る"):
            st.session_state.test_index = 0
            st.session_state.show_answer = False

    if st.session_state.show_answer:
        st.markdown(f"**英語:** {en}")
