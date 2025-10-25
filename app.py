
import streamlit as st
from deep_translator import GoogleTranslator
import random
import io

st.set_page_config(page_title="英単語支援ソフト（Web版）", layout="centered")

translator = GoogleTranslator(source="ja", target="en")

# ======================== セッション状態の初期化 ========================
def _init_state():
    default_keys = {
        "ja_list": [],
        "en_list": [],
        "pairs": [],
        "test_index": 0,
        "testing": False,
        "show_answer": False,
        "direction": "ja→en",
        "correct": 0,
        "answered": False,
        "hide_sections": False,  # ★ (2)と(2.5)を自動で隠す
    }
    for k, v in default_keys.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

st.title("英単語支援ソフト（Web版）")

# ======================== サイドバー：セーブ/ロード ========================
with st.sidebar:
    st.header("セーブ/ロード")
    if st.button("現在のデータをダウンロード"):
        buf = io.StringIO()
        buf.write("ja_list:\n")
        for ja in st.session_state.ja_list:
            buf.write(ja + "\n")
        buf.write("en_list:\n")
        for en in st.session_state.en_list:
            buf.write(en + "\n")
        st.download_button("tango_data.txt を保存", buf.getvalue(), file_name="tango_data.txt")

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

# ======================== 1) 単語入力 ========================
st.subheader("(1) 単語を入力（日本語・改行区切り）")
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
        st.session_state.hide_sections = False
        st.session_state.test_index = 0
        st.session_state.correct = 0
        st.session_state.answered = False
        st.info("リストを空にしました")

st.divider()

# ======================== 2) 一括翻訳（ja → en） ========================
if not st.session_state.hide_sections:
    st.subheader("(2) 一括翻訳（ja → en）")
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

    # ======================== 2.5) 単語ペアの編集 ========================
    st.subheader("(2.5) 単語ペアの編集")
    editable_rows = [
        {"日本語": ja, "英語": st.session_state.en_list[i] if i < len(st.session_state.en_list) else ""}
        for i, ja in enumerate(st.session_state.ja_list)
    ]

    edited = st.data_editor(
        editable_rows,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_pairs",
        column_config={
            "日本語": st.column_config.TextColumn("日本語"),
            "英語": st.column_config.TextColumn("英語"),
        }
    )

    col_save, col_note = st.columns([1, 2])
    with col_save:
        if st.button("編集内容を保存（リストへ反映）"):
            new_ja, new_en = [], []
            for row in edited:
                ja = (row.get("日本語") or "").strip()
                en = (row.get("英語") or "").strip()
                if not ja and not en:
                    continue
                new_ja.append(ja)
                new_en.append(en)
            st.session_state.ja_list = new_ja
            st.session_state.en_list = new_en
            st.success(f"編集を反映しました（{len(new_ja)} 件）")
            st.session_state.testing = False
            st.session_state.pairs = []
            st.session_state.test_index = 0
            st.session_state.correct = 0
            st.session_state.answered = False

    with col_note:
        st.caption("※ 行の追加/削除・直接編集ができます。保存でリストに反映されます。")
else:
    st.info("テスト中のため『(2) 一括翻訳』と『(2.5) 編集』は非表示です。テストを終了すると再表示されます。")

st.divider()

# ======================== 3) 単語テスト ========================
st.subheader("3) 単語テスト")

col_dir, col_reset = st.columns([2, 1])
with col_dir:
    st.session_state.direction = st.radio("出題方向", ["ja→en", "en→ja"], horizontal=True)
with col_reset:
    if st.button("結果をリセット"):
        st.session_state.correct = 0
        st.session_state.test_index = 0
        st.session_state.answered = False
        st.session_state.testing = False
        st.session_state.hide_sections = False

col3, col4 = st.columns(2)
with col3:
    if st.button("シャッフルしてテスト開始"):
        pairs = list(zip(st.session_state.ja_list, st.session_state.en_list))
        random.shuffle(pairs)
        st.session_state.pairs = pairs
        st.session_state.testing = True
        st.session_state.hide_sections = True  # ★開始時に非表示に
        st.session_state.test_index = 0
        st.session_state.correct = 0
        st.session_state.answered = False
        if not pairs:
            st.warning("テストするペアがありません。")
with col4:
    if st.button("テスト終了"):
        st.session_state.testing = False
        st.session_state.hide_sections = False  # ★終了時に再表示
        st.success("テストを終了しました。")

# ===== 出題〜採点 =====
if st.session_state.testing and st.session_state.pairs:
    i = st.session_state.test_index
    total = len(st.session_state.pairs)
    ja, en = st.session_state.pairs[i]

    st.markdown(f"**問題 {i+1} / {total}**")
    st.progress((i + 1) / total)

    if st.session_state.direction == "ja→en":
        question, answer = ja, en
        q_label, a_label = "日本語", "英語"
    else:
        question, answer = en, ja
        q_label, a_label = "英語", "日本語"

    st.markdown(f"**{q_label}:** {question}")

    user_ans = st.text_input(f"{a_label} を入力", key=f"ans_{i}")
    cols = st.columns(3)
    with cols[0]:
        if st.button("判定"):
            norm = lambda s: (s or "").strip().lower()
            if norm(user_ans) == norm(answer):
                st.success("正解！")
                if not st.session_state.answered:
                    st.session_state.correct += 1
                st.session_state.answered = True
            else:
                st.error("不正解")
                st.info(f"正解: {answer}")
                st.session_state.answered = True
    with cols[1]:
        if st.button("次へ"):
            if i < total - 1:
                st.session_state.test_index += 1
                st.session_state.answered = False
            else:
                st.success("テストは最後まで終了しました")
                st.session_state.testing = False
                st.session_state.hide_sections = False
    with cols[2]:
        if st.button("最初に戻る"):
            st.session_state.test_index = 0
            st.session_state.answered = False

    st.caption(f"正答数: {st.session_state.correct} / {i + 1 if st.session_state.answered else i}")
