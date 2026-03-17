import os
from dataclasses import dataclass
from typing import Optional

import streamlit as st

from notes_grader.ocr import OcrConfig, extract_text_from_image
from notes_grader.scoring import grade_notes, GradingInput
from notes_grader.llm import LlmConfig, maybe_llm_feedback


@dataclass
class AppState:
    ocr_text: str = ""


def _set_page_style() -> None:
    st.set_page_config(
        page_title="AI Notes Grader",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def main() -> None:
    _set_page_style()

    st.title("AI Notes Grader (Handwritten Notes)")
    st.caption(
        "Upload a photo of handwritten notes → OCR extracts text → we score accuracy vs a reference (optional) and generate feedback."
    )

    with st.sidebar:
        st.header("Input")
        uploaded = st.file_uploader(
            "Upload handwritten notes photo",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=False,
        )

        st.divider()
        st.subheader("OCR settings")
        tesseract_cmd = st.text_input(
            "Tesseract executable path (Windows)",
            value=os.environ.get("TESSERACT_CMD", ""),
            help=r'Example: C:\Program Files\Tesseract-OCR\tesseract.exe (leave empty if on PATH)',
        )
        lang = st.text_input("Language", value="eng", help="Tesseract language code, e.g. eng")
        psm = st.selectbox(
            "Page segmentation mode (PSM)",
            options=[3, 4, 6, 11],
            index=2,
            help="6 is a good default for blocks of text.",
        )
        preprocess = st.selectbox(
            "Preprocessing",
            options=["auto", "none", "threshold", "adaptive_threshold"],
            index=0,
        )

        st.divider()
        st.subheader("Accuracy check")
        reference_text = st.text_area(
            "Reference / correct notes (optional)",
            placeholder="Paste the correct/expected text here to compute accuracy vs your handwritten notes.",
            height=160,
        )

        st.divider()
        st.subheader("AI feedback (optional)")
        enable_llm = st.checkbox("Enable LLM feedback", value=False)
        llm_provider = st.selectbox("Provider", options=["ollama"], index=0, disabled=not enable_llm)
        ollama_model = st.text_input(
            "Ollama model",
            value=os.environ.get("OLLAMA_MODEL", "llama3.1:8b"),
            disabled=not (enable_llm and llm_provider == "ollama"),
        )

    col1, col2 = st.columns([1, 1], gap="large")

    if not uploaded:
        with col1:
            st.info("Upload a handwritten notes image to begin.")
        with col2:
            st.markdown(
                """
                ### Tips for best OCR results
                - Use **good lighting** (no shadows)
                - Keep the page **flat** and in focus
                - Crop to the page (avoid background clutter)
                - Write with a **dark pen** on light paper
                """
            )
        return

    with col1:
        st.subheader("Uploaded image")
        st.image(uploaded, use_container_width=True)

    ocr_cfg = OcrConfig(
        tesseract_cmd=tesseract_cmd.strip() or None,
        lang=lang.strip() or "eng",
        psm=int(psm),
        preprocess=preprocess,
    )

    with st.spinner("Extracting text (OCR)…"):
        ocr_text = extract_text_from_image(uploaded.getvalue(), ocr_cfg)

    with col2:
        st.subheader("Extracted text (OCR)")
        st.text_area("OCR output", value=ocr_text, height=320)

    st.divider()
    st.subheader("Score")

    ginput = GradingInput(ocr_text=ocr_text, reference_text=reference_text.strip() or None)
    result = grade_notes(ginput)

    m1, m2, m3 = st.columns(3)
    m1.metric("Overall score", f"{result.overall_score:.0f}/100")
    m2.metric("Rating", result.rating)
    if result.accuracy_score is None:
        m3.metric("Accuracy vs reference", "—")
    else:
        m3.metric("Accuracy vs reference", f"{result.accuracy_score:.0f}/100")

    with st.expander("Details", expanded=True):
        st.write(result.summary)
        if result.warnings:
            st.warning("\n".join(f"- {w}" for w in result.warnings))

    if enable_llm:
        st.divider()
        st.subheader("AI feedback")
        llm_cfg = LlmConfig(provider=llm_provider, ollama_model=ollama_model.strip() or "llama3.1:8b")
        with st.spinner("Generating feedback with LLM…"):
            feedback = maybe_llm_feedback(
                ocr_text=ocr_text,
                reference_text=reference_text.strip() or None,
                cfg=llm_cfg,
            )
        if feedback:
            st.markdown(feedback)
        else:
            st.info("LLM feedback not available (check Ollama is running and model is installed).")


if __name__ == "__main__":
    main()
