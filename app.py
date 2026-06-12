"""Milestone 5 — Gradio query interface.

Run:  python app.py   then open http://localhost:7860

Thin UI layer over query.ask(): question in, grounded answer + the
programmatically-built source list out. No retrieval or generation logic
lives here.
"""

import gradio as gr

from query import ask

EXAMPLE_QUESTIONS = [
    "What do students say about living at 26 West?",
    "Is it cheaper to live in Riverside with a car or West Campus without one?",
    "When should I sign a lease for the fall semester?",
    "What parking scams should students watch out for near West Campus?",
    "Is the Castilian a good housing option for sophomores?",
]


def handle_query(question: str):
    question = (question or "").strip()
    if not question:
        return "Type a question first.", ""
    result = ask(question)
    if result["sources"]:
        sources = "\n".join(f"• {s}" for s in result["sources"])
    else:
        sources = "(none — the collected threads don't cover this question)"
    return result["answer"], sources


with gr.Blocks(title="UT Austin Housing — Unofficial Guide") as demo:
    gr.Markdown(
        "# The Unofficial Guide: UT Austin Off-Campus Housing\n"
        "Answers come **only** from 13 collected r/UTAustin threads "
        "(student experiences, 2021–2024) — not from the model's general "
        "knowledge. If the threads don't cover your question, the system "
        "says so instead of guessing."
    )

    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. Is the Castilian a good housing option for sophomores?",
    )
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    gr.Examples(examples=EXAMPLE_QUESTIONS, inputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

if __name__ == "__main__":
    demo.launch()
