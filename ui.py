import os
import tempfile
import logging

import gradio as gr
import httpx
import plotly.graph_objects as go

API_URL = os.getenv("API_URL", "https://reviewsanalyzer-986693471676.europe-west1.run.app")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

COUNTRIES = ["us", "ua", "gb", "de", "fr", "jp", "ca", "au", "pl", "nl"]
FONT = dict(family="Helvetica, Arial, sans-serif")


def _request_body(app_id: str, country: str, max_reviews: int, sample_size: int) -> dict:
    return {
        "app_id": app_id.strip(),
        "country": country,
        "max_reviews": int(max_reviews),
        "sample_size": int(sample_size),
    }


def _rating_chart(distribution: list[dict]) -> go.Figure:
    stars = [f"{d['star']} ★" for d in distribution]
    counts = [d["count"] for d in distribution]
    colors = ["#b91c1c", "#c2742e", "#a08a2e", "#6b8e3a", "#3a7d44"]

    fig = go.Figure(go.Bar(
        x=stars, y=counts,
        text=[f"{d['percentage']}%" for d in distribution],
        textposition="outside",
        textfont=FONT,
        marker_color=colors,
    ))
    fig.update_layout(
        title=dict(text="Rating Distribution", font={**FONT, "size": 16}),
        xaxis=dict(title="Rating", title_font=FONT, tickfont=FONT),
        yaxis=dict(title="Count", title_font=FONT, tickfont=FONT),
        template="plotly_white",
        height=450,
        margin=dict(t=60, b=50, l=50, r=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _sentiment_chart(sentiment_dist: dict[str, int]) -> go.Figure:
    labels = [k.capitalize() for k in sentiment_dist]
    values = list(sentiment_dist.values())
    colors = ["#b91c1c", "#a3a3a3", "#3a7d44"]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo="label+percent",
        textposition="outside",
        textfont=FONT,
    ))
    fig.update_layout(
        title=dict(text="Sentiment Distribution", font={**FONT, "size": 16}),
        template="plotly_white",
        height=450,
        margin=dict(t=60, b=50, l=30, r=30),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _format_insights(insights: dict) -> str:
    priority_badge = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
    lines = []
    for i, insight in enumerate(insights["insights"], 1):
        badge = priority_badge.get(insight["priority"], insight["priority"])
        keywords = ", ".join(f"`{k}`" for k in insight["keywords"])
        lines.append(
            f"### {i}. {insight['topic']}\n"
            f"**Priority:** {badge}\n\n"
            f"**Recommendation:** {insight['recommendation']}\n\n"
            f"**Keywords:** {keywords}\n\n---\n"
        )
    return "\n".join(lines)


def _format_keywords(keywords: list[str]) -> str:
    if not keywords:
        return "*No negative keywords detected.*"
    return " ".join(f"`{k}`" for k in keywords)


def _format_metrics_summary(metrics: dict) -> str:
    return (
        f"## Metrics Summary\n\n"
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Total reviews analysed | **{metrics['total_reviews']}** |\n"
        f"| Average rating | **{metrics['average_rating']} / 5** |\n"
    )


# ── Analyse ──────────────────────────────────────────────────────────

async def run_analysis(app_id, country, max_reviews, sample_size):
    if not app_id.strip():
        raise gr.Error("App ID is required")

    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(f"{API_URL}/analyse", json=_request_body(app_id, country, max_reviews, sample_size))

    if resp.status_code == 404:
        raise gr.Error(f"No reviews found for app {app_id}")
    if resp.status_code != 200:
        raise gr.Error(f"API error: {resp.json().get('detail', resp.text)}")

    data = resp.json()
    metrics = data["metrics"]
    insights = data["insights"]

    summary_md = _format_metrics_summary(metrics)
    rating_fig = _rating_chart(metrics["rating_distribution"])
    sentiment_fig = _sentiment_chart(metrics["sentiment_distribution"])
    keywords_md = _format_keywords(insights["negative_keywords"])
    insights_md = _format_insights(insights)

    return summary_md, rating_fig, sentiment_fig, keywords_md, insights_md


# ── Collect ──────────────────────────────────────────────────────────

async def run_collect(app_id, country, max_reviews, sample_size):
    if not app_id.strip():
        raise gr.Error("App ID is required")

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{API_URL}/collect", json=_request_body(app_id, country, max_reviews, sample_size))

    if resp.status_code == 404:
        raise gr.Error(f"No reviews found for app {app_id}")
    if resp.status_code != 200:
        raise gr.Error(f"API error: {resp.json().get('detail', resp.text)}")

    reviews = resp.json()["reviews"]
    rows = [[r["rating"], r["title"], r["content"]] for r in reviews]
    return gr.update(value=rows, visible=True)


# ── Download ─────────────────────────────────────────────────────────

async def run_download(app_id, country, max_reviews, sample_size):
    if not app_id.strip():
        raise gr.Error("App ID is required")

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{API_URL}/download", json=_request_body(app_id, country, max_reviews, sample_size))

    if resp.status_code == 404:
        raise gr.Error(f"No reviews found for app {app_id}")
    if resp.status_code != 200:
        raise gr.Error(f"API error: {resp.text}")

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, prefix="reviews_")
    tmp.write(resp.text)
    tmp.flush()
    return gr.update(value=tmp.name, visible=True)


# ── UI Layout ────────────────────────────────────────────────────────

theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.slate,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.gray,
    font=("Helvetica", "Arial", "sans-serif"),
    font_mono=("Helvetica", "Arial", "monospace"),
)

CUSTOM_CSS = """
* { font-family: Helvetica, Arial, sans-serif !important; }
.gradio-container { max-width: 960px !important; margin: auto; }
code { font-family: Helvetica, Arial, monospace !important;
       background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
input:focus, textarea:focus, select:focus,
.wrap input:focus, .wrap textarea:focus {
    outline: none !important;
    box-shadow: none !important;
    border-color: #d1d5db !important;
}
label span { color: inherit !important; }

#report { position: relative; min-height: 120px; }
#report-overlay {
    display: none;
    position: absolute;
    inset: 0;
    background: rgba(255, 255, 255, 0.88);
    z-index: 100;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 1.1rem;
    color: #64748b;
    backdrop-filter: blur(2px);
    border-radius: 8px;
}
#report-overlay .timer { font-size: 0.9rem; color: #94a3b8; }
#report .pending .wrap,
#report .pending .progress-bar,
#report .pending .eta-bar {
    display: none !important;
}
"""

OVERLAY_JS = """
() => {
    function init() {
        const report = document.getElementById('report');
        if (!report) { setTimeout(init, 200); return; }
        if (document.getElementById('report-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'report-overlay';
        overlay.innerHTML = '<span>Analysing…</span><span class="timer"></span>';
        report.appendChild(overlay);

        let timer = null;
        const obs = new MutationObserver(() => {
            const pending = report.querySelector('.pending');
            if (pending && !timer) {
                const start = Date.now();
                overlay.style.display = 'flex';
                const tick = () => {
                    const s = Math.floor((Date.now() - start) / 1000);
                    const m = Math.floor(s / 60);
                    overlay.querySelector('.timer').textContent =
                        m > 0 ? m + 'm ' + (s % 60) + 's' : s + 's';
                };
                tick();
                timer = setInterval(tick, 1000);
            } else if (!pending && timer) {
                clearInterval(timer);
                timer = null;
                overlay.style.display = 'none';
            }
        });
        obs.observe(report, { subtree: true, attributes: true, attributeFilter: ['class'] });
    }
    init();
}
"""

with gr.Blocks(
    theme=theme,
    title="Reviews Analyzer",
    css=CUSTOM_CSS,
    js=OVERLAY_JS,
) as demo:
    gr.Markdown("# Reviews Analyzer\nAnalyse Apple App Store reviews with LLM-powered insights.")

    with gr.Row():
        app_id = gr.Textbox(label="App ID", placeholder="e.g. 6455785300", scale=2)
        country = gr.Dropdown(COUNTRIES, value="us", label="Country", scale=1)
        max_reviews = gr.Slider(50, 500, value=500, step=50, label="Max reviews to scrape", scale=1)
        sample_size = gr.Slider(1, 500, value=100, step=1, label="Sample size", scale=1)

    with gr.Tabs():
        # ── Tab: Analyse ─────────────────────────────────────────
        with gr.TabItem("Analyse"):
            analyse_btn = gr.Button("Run Analysis", variant="primary")

            with gr.Column(elem_id="report"):
                summary_md = gr.Markdown()

                with gr.Row():
                    rating_plot = gr.Plot(label="Rating Distribution")
                    sentiment_plot = gr.Plot(label="Sentiment Distribution")

                gr.Markdown("## Negative Keywords")
                keywords_md = gr.Markdown()

                gr.Markdown("## Insights")
                insights_md = gr.Markdown()

            analyse_btn.click(
                fn=run_analysis,
                inputs=[app_id, country, max_reviews, sample_size],
                outputs=[summary_md, rating_plot, sentiment_plot, keywords_md, insights_md],
            )

        # ── Tab: Collect ─────────────────────────────────────────
        with gr.TabItem("Collect"):
            collect_btn = gr.Button("Collect Reviews", variant="secondary")
            reviews_table = gr.Dataframe(
                headers=["Rating", "Title", "Content"],
                datatype=["number", "str", "str"],
                column_widths=["8%", "30%", "62%"],
                visible=False,
                wrap=True,
            )
            collect_btn.click(
                fn=run_collect,
                inputs=[app_id, country, max_reviews, sample_size],
                outputs=[reviews_table],
            )

        # ── Tab: Download ────────────────────────────────────────
        with gr.TabItem("Download CSV"):
            download_btn = gr.Button("Download as CSV", variant="secondary")
            csv_file = gr.File(label="CSV File", visible=False)
            download_btn.click(
                fn=run_download,
                inputs=[app_id, country, max_reviews, sample_size],
                outputs=[csv_file],
            )


if __name__ == "__main__":
    demo.launch()