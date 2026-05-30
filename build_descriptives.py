#!/usr/bin/env python3
"""
Build a self-contained HTML companion for the
DESCRIPTIVE STATISTICS & DISTRIBUTIONS lecture.

Teaching philosophy (per Dr Atuhairwe's brief):
  * ILLUSTRATE the concepts on a genuinely CLINICAL dataset, so the points
    land on their own instead of being forced onto car data.
  * Every number and every chart below is REALLY COMPUTED from a simulated
    200-patient cohort (clinical_cohort.csv, written by this script) - not
    typed in by hand. Re-run and the page rebuilds from the data.
  * For every step we also show the exact STATA command, plus a
    "in the hands-on" box mapping it onto Stata's built-in `auto` dataset
    (mpg / price / foreign), which loads with one command for practice.

Run:  python3 build_descriptives.py
Out:  descriptives_distributions_companion.html   (open in any browser)
      clinical_cohort.csv                          (the underlying data)
"""

import base64
import html
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

OUT = "descriptives_distributions_companion.html"
DATA = "clinical_cohort.csv"

# ---------------------------------------------------------------------------
# 1. BUILD THE COHORT  (seeded -> identical every run, so outputs are stable)
#    Each variable is shaped to teach a specific idea:
#      age, sbp  -> roughly Normal (mean ~ median, passes normality)
#      bmi       -> Normal-ish, mild right tail
#      crp       -> strongly RIGHT-SKEWED  (the classic "report the median")
#      los       -> right-skewed count days (skew + outliers for the boxplot)
#      sex, ward, diabetes -> categorical (frequencies, grouped summaries)
# ---------------------------------------------------------------------------
rng = np.random.default_rng(20260530)
N = 200

age = np.clip(rng.normal(58, 15, N), 18, 95).round(0)
sex = rng.choice(["Female", "Male"], N, p=[0.48, 0.52])
sbp = np.clip(rng.normal(132, 18, N), 85, 205).round(0)
bmi = np.clip(rng.normal(27.5, 5.0, N), 15, 52).round(1)
crp = np.clip(rng.lognormal(1.4, 1.0, N), 0.2, 300).round(1)          # mg/L, skewed
los = np.clip(rng.gamma(2.0, 2.2, N) + 0.5, 1, None).round(0).astype(int)  # days
ward = rng.choice(["Medical", "Surgical", "ICU"], N, p=[0.50, 0.35, 0.15])
diabetes = rng.choice(["No", "Yes"], N, p=[0.70, 0.30])

df = pd.DataFrame({
    "patient_id": np.arange(1, N + 1),
    "age": age.astype(int),
    "sex": sex,
    "ward": ward,
    "diabetes": diabetes,
    "sbp": sbp.astype(int),
    "bmi": bmi,
    "crp": crp,
    "los": los,
})
df.to_csv(DATA, index=False)

CONT = ["age", "sbp", "bmi", "crp", "los"]
LABELS = {
    "age": "Age (years)", "sbp": "Systolic BP (mmHg)", "bmi": "BMI (kg/m²)",
    "crp": "CRP (mg/L)", "los": "Length of stay (days)",
}

# ---------------------------------------------------------------------------
# 2. HELPERS
# ---------------------------------------------------------------------------
def esc(s):
    return html.escape(str(s))


def f(x, d=1):
    """Format a number to d decimals, trimming a trailing .0 for whole values."""
    if x == int(x):
        return f"{int(x)}"
    return f"{x:.{d}f}"


def fixed_table(headers, rows, aligns=None):
    """Build a clean fixed-width monospace table (Stata-results feel)."""
    cols = list(zip(*([headers] + rows))) if rows else [[h] for h in headers]
    widths = [max(len(str(c)) for c in col) for col in cols]
    aligns = aligns or ["<"] + [">"] * (len(headers) - 1)

    def line(cells):
        return "  ".join(f"{str(c):{a}{w}}" for c, w, a in zip(cells, widths, aligns))

    sep = "  ".join("-" * w for w in widths)
    return "\n".join([line(headers), sep] + [line(r) for r in rows])


def fig_uri(fig):
    """Render a matplotlib figure to a base64 PNG data-URI and close it."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 12, "axes.grid": True,
    "grid.alpha": 0.25, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white",
})
BLUE, RED, GREEN, AMBER = "#2a6fb3", "#c0392b", "#1a7f37", "#d68910"

# ---------------------------------------------------------------------------
# 3. PLOTS  (all computed from df)
# ---------------------------------------------------------------------------
def hist_normal(col, color=BLUE):
    s = df[col]
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    counts, bins, _ = ax.hist(s, bins=20, color=color, alpha=0.75, edgecolor="white")
    x = np.linspace(s.min(), s.max(), 200)
    bw = bins[1] - bins[0]
    ax.plot(x, stats.norm.pdf(x, s.mean(), s.std()) * len(s) * bw, color=RED, lw=2,
            label="Normal curve (same mean & SD)")
    ax.axvline(s.mean(), color=RED, ls="--", lw=1.3, label=f"Mean = {f(s.mean())}")
    ax.axvline(s.median(), color=GREEN, ls=":", lw=1.6, label=f"Median = {f(s.median())}")
    ax.set(xlabel=LABELS[col], ylabel="Number of patients", title=f"Distribution of {LABELS[col]}")
    ax.legend(fontsize=9)
    return fig_uri(fig)


def hist_skew_fix():
    s = df["crp"]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
    axes[0].hist(s, bins=25, color=AMBER, alpha=0.8, edgecolor="white")
    axes[0].axvline(s.mean(), color=RED, ls="--", lw=1.3, label=f"Mean = {f(s.mean())}")
    axes[0].axvline(s.median(), color=GREEN, ls=":", lw=1.6, label=f"Median = {f(s.median())}")
    axes[0].set(xlabel="CRP (mg/L)", ylabel="Number of patients", title="Raw CRP — right-skewed")
    axes[0].legend(fontsize=9)
    ls = np.log(s)
    axes[1].hist(ls, bins=25, color=BLUE, alpha=0.8, edgecolor="white")
    axes[1].set(xlabel="ln(CRP)", title="log(CRP) — now ~symmetric")
    fig.tight_layout()
    return fig_uri(fig)


def boxplot_los():
    s = df["los"]
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    bp = ax.boxplot(s, vert=False, widths=0.5, patch_artist=True,
                    flierprops=dict(marker="o", markerfacecolor=RED, markersize=5, alpha=0.6))
    bp["boxes"][0].set(facecolor=BLUE, alpha=0.55)
    for med in bp["medians"]:
        med.set(color=RED, linewidth=2)
    q1, q2, q3 = s.quantile([.25, .5, .75])
    # median above the box; Q1/Q3 below — keeps close-together labels from colliding
    ax.annotate(f"median = {f(q2)}", (q2, 1.30), ha="center", fontsize=9, color=RED, weight="bold")
    ax.annotate(f"Q1 = {f(q1)}", (q1, 0.66), ha="center", fontsize=8.5, color="#333")
    ax.annotate(f"Q3 = {f(q3)}", (q3, 0.66), ha="center", fontsize=8.5, color="#333")
    ax.annotate("outliers →", (s.max(), 1.0), ha="right", va="bottom", fontsize=8, color=RED,
                xytext=(0, 8), textcoords="offset points")
    ax.set(xlabel="Length of stay (days)", yticks=[], ylim=(0.5, 1.6),
           title="Box-and-whisker — length of stay")
    return fig_uri(fig)


def qq_pair():
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
    for ax, col, ttl in [(axes[0], "age", "Age — points hug the line ⇒ Normal"),
                         (axes[1], "crp", "CRP — points bend off ⇒ skewed")]:
        stats.probplot(df[col], dist="norm", plot=ax)
        ax.get_lines()[0].set(marker="o", markersize=4, alpha=0.6, color=BLUE)
        ax.get_lines()[1].set(color=RED, lw=1.8)
        ax.set_title(ttl)
    fig.tight_layout()
    return fig_uri(fig)


def bar_ward():
    vc = df["ward"].value_counts().reindex(["Medical", "Surgical", "ICU"])
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    bars = ax.bar(vc.index, vc.values, color=[BLUE, GREEN, AMBER], alpha=0.85, edgecolor="white")
    for b, v in zip(bars, vc.values):
        ax.annotate(f"{v}\n({v / N * 100:.0f}%)", (b.get_x() + b.get_width() / 2, v),
                    ha="center", va="bottom", fontsize=9.5)
    ax.set(ylabel="Number of patients", title="Patients by ward", ylim=(0, vc.max() * 1.2))
    return fig_uri(fig)


def grouped_sbp():
    g = df.groupby("ward")["sbp"].agg(["mean", "std"]).reindex(["Medical", "Surgical", "ICU"])
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    ax.bar(g.index, g["mean"], yerr=g["std"], capsize=6, color=BLUE, alpha=0.8,
           edgecolor="white")
    for i, (m, sd) in enumerate(zip(g["mean"], g["std"])):
        ax.annotate(f"{f(m)}", (i, m), ha="center", va="bottom", fontsize=9.5, xytext=(0, 3),
                    textcoords="offset points")
    ax.set(ylabel="Systolic BP (mmHg)", title="Mean SBP by ward (bars = SD)")
    return fig_uri(fig)


IMG_AGE_HIST = hist_normal("age")
IMG_SKEW = hist_skew_fix()
IMG_BOX = boxplot_los()
IMG_QQ = qq_pair()
IMG_WARD = bar_ward()
IMG_GROUP = grouped_sbp()

# ---------------------------------------------------------------------------
# 4. COMPUTED OUTPUTS  (real, formatted as monospace tables)
# ---------------------------------------------------------------------------
def preview_html():
    head = df.head(8)
    th = "".join(f"<th>{esc(c)}</th>" for c in head.columns)
    trs = ""
    for _, row in head.iterrows():
        trs += "<tr>" + "".join(f"<td>{esc(v)}</td>" for v in row) + "</tr>"
    return f'<table class="grid data"><tr>{th}</tr>{trs}</table>'


def describe_block(col):
    s = df[col]
    rows = [
        ["Obs", f(s.count())], ["Mean", f(s.mean(), 2)], ["Std. dev.", f(s.std(), 2)],
        ["Min", f(s.min())], ["25%", f(s.quantile(.25))], ["Median (50%)", f(s.median())],
        ["75%", f(s.quantile(.75))], ["Max", f(s.max())], ["Skewness", f(s.skew(), 2)],
    ]
    return fixed_table([col, ""], rows)


def table1():
    rows = []
    for c in CONT:
        s = df[c]
        rows.append([c, f(s.count()), f(s.mean(), 1), f(s.std(), 1), f(s.min()),
                     f(s.quantile(.25)), f(s.median()), f(s.quantile(.75)), f(s.max())])
    return fixed_table(
        ["Variable", "N", "Mean", "SD", "Min", "p25", "Median", "p75", "Max"], rows)


def freq_table(col):
    vc = df[col].value_counts()
    order = ["Medical", "Surgical", "ICU"] if col == "ward" else vc.index.tolist()
    rows, cum = [], 0
    for k in order:
        n = int(vc[k]); pct = n / N * 100; cum += pct
        rows.append([k, f(n), f"{pct:.1f}", f"{cum:.1f}"])
    rows.append(["Total", f(N), "100.0", ""])
    return fixed_table([col, "Freq.", "Percent", "Cum."], rows)


def grouped_table():
    g = df.groupby("ward")["sbp"].agg(["count", "mean", "std", "min", "max"])
    g = g.reindex(["Medical", "Surgical", "ICU"])
    rows = [[w, f(r["count"]), f(r["mean"], 1), f(r["std"], 1), f(r["min"]), f(r["max"])]
            for w, r in g.iterrows()]
    return fixed_table(["ward", "N", "Mean SBP", "SD", "Min", "Max"], rows)


# Pull a few live numbers for the prose ------------------------------------
m_age, md_age, sd_age = df.age.mean(), df.age.median(), df.age.std()
m_crp, md_crp = df.crp.mean(), df.crp.median()
sw_age = stats.shapiro(df.age); sw_crp = stats.shapiro(df.crp)
lo2, hi2 = m_age - 2 * sd_age, m_age + 2 * sd_age

# ---------------------------------------------------------------------------
# 5. SECTIONS
# ---------------------------------------------------------------------------
SECTIONS = [
    {
        "id": "orient", "title": "1 · Meet the data — a 200-patient cohort",
        "lead": "Before any statistic, look at the raw data. Think of each <b>row as a patient</b> "
                "and each <b>column as something we measured</b>. This cohort is simulated, but "
                "shaped to behave like real ward data.",
        "blocks": [{
            "stata": "import delimited clinical_cohort.csv, clear\ndescribe\nlist in 1/8",
            "preview": True,
            "means": f"We have <b>{N} patients</b> and 9 columns. Some are <b>numbers you can "
                     f"average</b> (age, SBP, BMI, CRP, length-of-stay) and some are <b>labels you "
                     f"can only count</b> (sex, ward, diabetes). That split decides everything "
                     f"that follows. <code>describe</code> lists the variables; "
                     f"<code>list in 1/8</code> prints the first 8 rows so you can eyeball them.",
            "say": "Always eyeball the raw data first. Rows are patients, columns are measurements "
                   "— and notice some columns are numbers, others are categories.",
            "practice": "In the hands-on we swap one line: <code>sysuse auto, clear</code> loads "
                        "Stata's 74-car demo. Same <code>describe</code>, same <code>list in 1/8</code>.",
        }],
    },
    {
        "id": "types", "title": "2 · Two kinds of variable (this choice drives the rest)",
        "lead": "Pick the wrong summary for the variable type and the whole table is wrong. "
                "There are really just two families.",
        "blocks": [{
            "stata": "codebook, compact",
            "output": fixed_table(
                ["Variable", "Type", "Summarise with", "Picture with"],
                [["age, sbp, bmi, crp, los", "Continuous", "mean/median, SD/IQR", "histogram, boxplot"],
                 ["sex, ward, diabetes", "Categorical", "counts & percentages", "bar chart"]],
                aligns=["<", "<", "<", "<"]),
            "means": "<b>Continuous</b> variables are measured on a scale where the gaps mean "
                     "something (61 mmHg really is 2 more than 59). You summarise them with a "
                     "<b>centre</b> and a <b>spread</b>. <b>Categorical</b> variables are just "
                     "labels — averaging \"ward\" is meaningless — so you summarise them with "
                     "<b>counts and percentages</b>.",
            "say": "First question for every column: can I sensibly average it? Yes → continuous. "
                   "No → categorical. The answer picks your summary and your plot.",
            "practice": "In <code>auto</code>: <code>mpg, price, weight</code> are continuous; "
                        "<code>foreign</code> (domestic/foreign) and <code>rep78</code> are categorical.",
        }],
    },
    {
        "id": "center", "title": "3 · The centre — mean, median, mode",
        "lead": "Three ways to answer \"what's a typical patient?\" — and the gap between them is "
                "itself information.",
        "blocks": [
            {
                "stata": "summarize age, detail",
                "output": describe_block("age"),
                "means": f"For <b>age</b> the <b>mean ({f(m_age,1)})</b> and <b>median "
                         f"({f(md_age)})</b> sit almost on top of each other. That near-match is "
                         f"the signature of a <b>symmetric</b> distribution — for age, either number "
                         f"is a fair 'typical patient'.",
                "say": "Mean and median agree here, so age is symmetric — quote whichever you like.",
            },
            {
                "stata": "summarize crp, detail",
                "output": describe_block("crp"),
                "means": f"Now look at <b>CRP</b>: the <b>mean ({f(m_crp,1)})</b> is far above the "
                         f"<b>median ({f(md_crp)})</b>. A handful of very sick patients with huge "
                         f"CRP drag the mean upward, but the <b>median is unmoved</b> — half the "
                         f"patients are still below {f(md_crp)}. When mean ≫ median, the data are "
                         f"<b>right-skewed</b> and the <b>median is the honest centre</b>.",
                "say": "Mean way above median = skew. One septic patient can't move the median, but "
                       "it drags the mean — so for CRP, length-of-stay, cost, we report the median.",
                "warn": "The <b>mode</b> (most common value) is only useful for categories or "
                        "counts. For continuous measurements it's rarely worth reporting.",
                "practice": "Car <code>price</code> behaves exactly like CRP — a few expensive "
                            "cars pull the mean above the median. Try <code>summarize price, detail</code>.",
            },
        ],
    },
    {
        "id": "spread", "title": "4 · The spread — range, IQR, variance, SD",
        "lead": "Two wards can share the same mean BP yet be utterly different. Spread is the "
                "other half of the story.",
        "blocks": [{
            "stata": "tabstat age, stats(min p25 median p75 max range iqr sd variance)",
            "output": fixed_table(
                ["Statistic", "Value", "Plain meaning"],
                [["Range", f(df.age.max() - df.age.min()), "max − min (sensitive to one extreme)"],
                 ["IQR", f(df.age.quantile(.75) - df.age.quantile(.25)), "middle 50% width (robust)"],
                 ["Variance", f(df.age.var(), 1), "average squared distance from mean"],
                 ["SD", f(sd_age, 1), "typical distance from the mean (same units)"]],
                aligns=["<", ">", "<"]),
            "means": f"<b>SD</b> is the one to internalise: it's the typical distance of a patient "
                     f"from the mean, in the <b>original units</b> (years here). With roughly-Normal "
                     f"data, about <b>95% of patients fall within mean ± 2 SD</b> — here that's "
                     f"<b>{f(lo2)} to {f(hi2)} years</b>. That is exactly how clinical "
                     f"<b>reference ranges</b> are built. <b>IQR</b> (the middle-50% width) is the "
                     f"spread you quote alongside a median for skewed data.",
            "say": "SD is the typical gap from the mean. Mean ± 2 SD captures about 95% of people — "
                   "that's where lab reference ranges come from.",
            "practice": "<code>tabstat mpg, stats(sd iqr range)</code> on the auto data.",
        }],
    },
    {
        "id": "table1", "title": "5 · The descriptive table — your paper's \"Table 1\"",
        "lead": "Every clinical paper opens with this: one row per variable, the centre and the "
                "spread side by side. Here it is, computed for all five continuous variables.",
        "blocks": [{
            "stata": "tabstat age sbp bmi crp los, ///\n"
                     "    stats(n mean sd min p25 median p75 max) columns(statistics)",
            "output": table1(),
            "means": "Read across each row. For the <b>symmetric</b> variables (age, SBP, BMI) the "
                     "<b>mean ≈ median</b>, so report <b>mean (SD)</b>. For <b>crp</b> and "
                     "<b>los</b> the mean sits well above the median — <b>skewed</b> — so report "
                     "<b>median (p25–p75)</b> instead. The same table tells you both the numbers "
                     "<i>and</i> which numbers to quote.",
            "say": "This single table is Table 1 of your paper. The trick is choosing mean-or-median "
                   "per row — and the median/p25/p75 columns make that obvious.",
            "practice": "<code>tabstat mpg price weight, stats(n mean sd median p25 p75)</code> "
                        "gives the identical layout for the cars.",
        }],
    },
    {
        "id": "hist", "title": "6 · The shape of the data — histograms",
        "lead": "A table gives numbers; a histogram gives <i>shape</i>. It's the single most useful "
                "plot in descriptive statistics.",
        "blocks": [{
            "stata": "histogram age, normal",
            "img": IMG_AGE_HIST,
            "means": "Each bar counts how many patients fall in that slice of age. The red curve is "
                     "the <b>Normal (\"bell\") curve</b> with the same mean and SD. Here the bars "
                     "<b>track the bell closely</b> and the mean (dashed) and median (dotted) "
                     "almost coincide — a textbook symmetric, roughly-Normal variable. "
                     "<code>, normal</code> overlays that reference bell for you.",
            "say": "The histogram is the data's fingerprint. Age fills the bell evenly — symmetric, "
                   "centred, no long tail.",
            "practice": "<code>histogram mpg, normal</code> — mileage is fairly bell-shaped too.",
        }],
    },
    {
        "id": "skew", "title": "7 · When the mean lies — skew, and the fix",
        "lead": "Right-skew is the norm in medicine: CRP, troponin, viral load, cost, length of "
                "stay. Here's what it looks like and what to do about it.",
        "blocks": [{
            "stata": "histogram crp, normal\ngenerate ln_crp = ln(crp)\nhistogram ln_crp, normal",
            "img": IMG_SKEW,
            "means": f"<b>Left:</b> raw CRP piles up at low values with a long tail of very sick "
                     f"patients to the right. The mean ({f(m_crp,1)}) is dragged into that tail, "
                     f"well past the median ({f(md_crp)}) — so the mean over-states the 'typical' "
                     f"patient. <b>Right:</b> taking the <b>natural log</b> pulls the tail in and "
                     f"the distribution becomes roughly symmetric. That's why skewed labs are often "
                     f"<b>log-transformed</b> before analysis, and reported as <b>median (IQR)</b>.",
            "say": "Right-skew means a few extreme patients stretch the tail. Don't average it raw — "
                   "report the median, and log-transform if you need to model it.",
            "warn": "A positive <b>skewness</b> value (see the summarize output) confirms a right "
                    "tail. 0 ≈ symmetric; above ~1 is clearly skewed.",
            "practice": "Car <code>price</code> is the skewed one: <code>histogram price, normal</code> "
                        "then <code>gen lnprice = ln(price)</code> and re-plot.",
        }],
    },
    {
        "id": "box", "title": "8 · The box-and-whisker plot — five numbers at a glance",
        "lead": "The boxplot is a histogram's compact cousin: it draws the five-number summary and "
                "flags outliers automatically.",
        "blocks": [{
            "stata": "graph box los",
            "img": IMG_BOX,
            "means": "The <b>box</b> spans Q1 to Q3 (the middle 50% — the IQR), the line inside is "
                     "the <b>median</b>, and the <b>whiskers</b> reach to the most extreme "
                     "non-outlier values. The red dots beyond the whiskers are <b>statistical "
                     "outliers</b> (here, the long-stay patients). A box pushed to the left with a "
                     "long right whisker is the boxplot's way of showing <b>right-skew</b>.",
            "say": "Box = middle half, line = median, dots = outliers. One glance tells you centre, "
                   "spread, and who the unusual patients are.",
            "practice": "<code>graph box price</code>, or split by group with "
                        "<code>graph box mpg, over(foreign)</code>.",
        }],
    },
    {
        "id": "normal", "title": "9 · Is it Normal? Q–Q plot + Shapiro–Wilk",
        "lead": "Many later tests assume a variable is roughly Normal. Two ways to check — one "
                "visual, one a formal test.",
        "blocks": [{
            "stata": "qnorm age\nswilk age\nqnorm crp\nswilk crp",
            "img": IMG_QQ,
            "output": fixed_table(
                ["Variable", "W", "p-value", "Verdict (p>0.05 = Normal)"],
                [["age", f(sw_age.statistic, 3), f(sw_age.pvalue, 3),
                  "Normal" if sw_age.pvalue > .05 else "not Normal"],
                 ["crp", f(sw_crp.statistic, 3),
                  f(sw_crp.pvalue, 3) if sw_crp.pvalue >= .001 else "<0.001",
                  "Normal" if sw_crp.pvalue > .05 else "not Normal"]],
                aligns=["<", ">", ">", "<"]),
            "means": f"In a <b>Q–Q plot</b> the dots are your data, the red line is perfect "
                     f"Normality. <b>Age</b> hugs the line; <b>CRP</b> bends away at the top — its "
                     f"heavy tail. The <b>Shapiro–Wilk</b> test puts a number on it. The rule is "
                     f"counter-intuitive: <b>p &gt; 0.05 means Normal enough</b>. Age passes "
                     f"(p = {f(sw_age.pvalue,3)}); CRP fails decisively, matching its skew.",
            "say": "Q–Q plot first — points on the line means Normal. Shapiro–Wilk confirms it, but "
                   "remember: here a BIG p-value is the good news.",
            "warn": "In big samples Shapiro–Wilk flags trivial deviations as 'significant'. Always "
                    "trust the <b>plot and the histogram</b> over the p-value alone.",
            "practice": "<code>qnorm mpg</code> and <code>swilk mpg</code>; then try "
                        "<code>swilk price</code> to see a skewed variable fail.",
        }],
    },
    {
        "id": "freq", "title": "10 · Counting categories — frequencies & proportions",
        "lead": "For categorical variables there's no mean — just how many, and what share.",
        "blocks": [{
            "stata": "tabulate ward",
            "output": freq_table("ward"),
            "img": IMG_WARD,
            "means": "A <b>frequency table</b> gives the count, the <b>percent</b> of the cohort, "
                     "and the running <b>cumulative</b> percent. The bar chart is its picture. These "
                     "percentages are the building blocks of risk, prevalence and proportions — and "
                     "the numerators/denominators behind every rate you'll quote.",
            "say": "Categories get counted, not averaged. The percent column is what ends up in your "
                   "results: '50% were medical admissions'.",
            "practice": "<code>tabulate foreign</code> (domestic vs foreign cars) or "
                        "<code>tabulate rep78</code>.",
        }],
    },
    {
        "id": "grouped", "title": "11 · Describing by group — the seed of every comparison",
        "lead": "The moment you summarise an outcome <i>within each group</i>, you've set up the "
                "comparison that the next lecture (t-tests, ANOVA) will test formally.",
        "blocks": [{
            "stata": "tabstat sbp, by(ward) stats(n mean sd min max)\ngraph bar (mean) sbp, over(ward)",
            "output": grouped_table(),
            "img": IMG_GROUP,
            "means": "We split the cohort by <b>ward</b> and describe SBP within each. Now you can "
                     "see whether ICU patients run higher than medical patients — <b>descriptively</b>. "
                     "This is the right-hand side of every Table 1 (outcome by group), and the "
                     "honest first step before any p-value: <i>look at the group means and spreads "
                     "first.</i>",
            "say": "Summarise the outcome inside each group first. The difference you see here is "
                   "exactly what a t-test or ANOVA will later tell you is real or not.",
            "warn": "A difference in means is <b>not yet a significant difference</b> — that needs a "
                    "test, and a test needs the assumptions we checked above. Describe first, test "
                    "later.",
            "practice": "<code>tabstat mpg, by(foreign) stats(n mean sd)</code> — do foreign cars "
                        "really get better mileage? Describe it here, test it next lecture.",
        }],
    },
]

GUIDE = [
    ("Continuous & symmetric", "age, SBP, BMI", "Mean (SD)", "histogram + normal, Q–Q",
     "Quote the mean; reference range = mean ± 2 SD"),
    ("Continuous & skewed", "CRP, length of stay, cost", "Median (p25–p75 / IQR)", "histogram, boxplot",
     "Mean misleads — report the median; consider log"),
    ("Categorical", "sex, ward, diabetes", "Count (percent)", "bar chart",
     "Proportions feed prevalence, risk, rates"),
]

GLOSSARY = [
    ("Mean", "The arithmetic average. Best for symmetric data; pulled toward the tail by skew."),
    ("Median", "The middle value (50th percentile). Half the patients lie below it. Unaffected by "
               "outliers — the honest centre for skewed data."),
    ("Mode", "The most common value. Mainly useful for categories or counts."),
    ("Range", "Max − min. Simple, but moves with a single extreme value."),
    ("IQR (interquartile range)", "p75 − p25: the width of the middle 50% of patients. Robust to "
                                  "outliers; the spread you pair with a median."),
    ("Variance", "The average squared distance from the mean. In squared units, so hard to read "
                 "directly — mostly a stepping-stone to the SD."),
    ("SD (standard deviation)", "Typical distance from the mean, in the original units. ~95% of "
                                "roughly-Normal data lies within mean ± 2 SD."),
    ("Percentile / quartile", "The value below which a given % of patients fall. Q1=25th, "
                              "Q2=median=50th, Q3=75th."),
    ("Skewness", "A number for asymmetry. 0 ≈ symmetric; positive = long right tail (the medical "
                 "norm); above ~1 is clearly skewed."),
    ("Normal distribution", "The symmetric bell curve. Many tests assume it; check with a "
                            "histogram, Q–Q plot and Shapiro–Wilk."),
    ("Q–Q plot", "Plots your data's quantiles against a perfect Normal. On the straight line = "
                 "Normal; bending away = skewed or heavy-tailed."),
    ("Shapiro–Wilk (swilk)", "A formal test of Normality. p > 0.05 = Normal enough. (Counter-"
                             "intuitively, a BIG p-value is the good result.)"),
    ("Frequency table", "Counts and percentages for a categorical variable — the basis of "
                        "proportions, prevalence and rates."),
]

# ---------------------------------------------------------------------------
# 6. RENDER
# ---------------------------------------------------------------------------
def render_block(b):
    p = ['<div class="block">']
    p.append('<div class="label">⌨️ The Stata command (you\'ll run this in the hands-on)</div>')
    p.append(f'<pre class="code">{esc(b["stata"])}</pre>')
    if b.get("preview"):
        p.append('<div class="label">📋 Result — first rows of the cohort</div>')
        p.append(preview_html())
    if b.get("output"):
        p.append('<div class="label">📋 Result — computed live from the 200 patients</div>')
        p.append(f'<pre class="output">{esc(b["output"])}</pre>')
    if b.get("img"):
        p.append('<div class="label">📈 Graph — drawn from the data</div>')
        p.append(f'<img class="plot-img" src="{b["img"]}" alt="plot">')
    p.append('<div class="callout means"><span class="tag">💡 What this means</span>'
             f'<div>{b["means"]}</div></div>')
    if b.get("practice"):
        p.append('<div class="callout practice"><span class="tag">🚗 In the hands-on (Stata\'s auto data)</span>'
                 f'<div>{b["practice"]}</div></div>')
    if b.get("say"):
        p.append('<div class="callout say"><span class="tag">🗣️ Say this</span>'
                 f'<div>{b["say"]}</div></div>')
    if b.get("warn"):
        p.append('<div class="callout warn"><span class="tag">⚠️ Watch out</span>'
                 f'<div>{b["warn"]}</div></div>')
    p.append('</div>')
    return "\n".join(p)


def render_section(s):
    out = [f'<section id="{s["id"]}">', f'<h2>{s["title"]}</h2>']
    if s.get("lead"):
        out.append(f'<p class="lead">{s["lead"]}</p>')
    out += [render_block(b) for b in s["blocks"]]
    out.append('</section>')
    return "\n".join(out)


def render_toc():
    items = "".join(f'<li><a href="#{s["id"]}">{esc(s["title"])}</a></li>' for s in SECTIONS)
    items += '<li><a href="#guide">Quick decision guide</a></li>'
    items += '<li><a href="#glossary">Plain-English glossary</a></li>'
    return f'<nav class="toc"><div class="toc-h">Contents</div><ol>{items}</ol></nav>'


def render_guide():
    rows = "".join(
        f"<tr><td><b>{esc(t)}</b></td><td>{esc(ex)}</td><td><code>{esc(summ)}</code></td>"
        f"<td>{esc(plot)}</td><td>{esc(note)}</td></tr>"
        for t, ex, summ, plot, note in GUIDE)
    return ('<section id="guide"><h2>Quick decision guide — pick the summary from the variable</h2>'
            '<table class="grid"><tr><th>Variable kind</th><th>Examples</th><th>Summarise with</th>'
            f'<th>Plot</th><th>Clinical note</th></tr>{rows}</table></section>')


def render_glossary():
    rows = "".join(f'<tr><td><b>{esc(t)}</b></td><td>{esc(d)}</td></tr>' for t, d in GLOSSARY)
    return ('<section id="glossary"><h2>Plain-English glossary — every term</h2>'
            f'<table class="grid">{rows}</table></section>')


CSS = """
:root{
  --ink:#1f2328; --muted:#6a737d; --line:#d0d7de; --bg:#fff;
  --code-bg:#f6f8fa; --term-bg:#0d1117; --term-ink:#c9d1d9;
  --means:#0969da; --means-bg:#ddf4ff; --say:#1a7f37; --say-bg:#dafbe1;
  --warn:#9a6700; --warn-bg:#fff8c5; --prac:#8250df; --prac-bg:#f3eefb;
}
*{box-sizing:border-box;}
body{margin:0;font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
     color:var(--ink);background:var(--bg);}
.wrap{max-width:1180px;margin:0 auto;display:grid;grid-template-columns:260px 1fr;gap:32px;padding:0 24px;}
header{grid-column:1/-1;padding:32px 0 8px;border-bottom:2px solid var(--line);}
header h1{margin:0 0 6px;font-size:30px;}
header p{margin:0;color:var(--muted);}
.banner{grid-column:1/-1;background:var(--means-bg);border:1px solid #9ad;border-radius:8px;
        padding:12px 16px;margin:18px 0;font-size:14px;color:#0a3069;}
.toc{position:sticky;top:16px;align-self:start;font-size:14px;max-height:92vh;overflow:auto;}
.toc-h{font-weight:700;text-transform:uppercase;letter-spacing:.04em;font-size:12px;color:var(--muted);margin-bottom:8px;}
.toc ol{list-style:none;margin:0;padding:0;}
.toc li{margin:2px 0;}
.toc a{color:var(--ink);text-decoration:none;display:block;padding:4px 8px;border-radius:6px;}
.toc a:hover{background:var(--code-bg);color:var(--means);}
main{min-width:0;padding-bottom:80px;}
section{margin:0 0 44px;}
h2{font-size:22px;border-bottom:1px solid var(--line);padding-bottom:8px;margin-top:8px;}
.lead{color:var(--muted);margin-top:-2px;}
.block{border:1px solid var(--line);border-radius:10px;padding:16px;margin:18px 0;background:#fff;
       box-shadow:0 1px 2px rgba(0,0,0,.04);}
.label{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700;margin:14px 0 4px;}
.label:first-child{margin-top:0;}
pre{margin:0;padding:12px 14px;border-radius:8px;overflow-x:auto;font:13px/1.5 "SF Mono",Consolas,Menlo,monospace;}
pre.code{background:var(--code-bg);border:1px solid var(--line);color:var(--ink);}
pre.output{background:var(--term-bg);color:var(--term-ink);}
.plot-img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:8px;display:block;}
.callout{border-radius:8px;padding:10px 14px 12px;margin:12px 0 0;font-size:15px;}
.callout .tag{display:inline-block;font-size:12px;font-weight:700;margin-bottom:4px;}
.callout div{margin:0;}
.means{background:var(--means-bg);border-left:4px solid var(--means);}
.means .tag{color:var(--means);}
.say{background:var(--say-bg);border-left:4px solid var(--say);}
.say .tag{color:var(--say);}
.say div{font-style:italic;}
.warn{background:var(--warn-bg);border-left:4px solid var(--warn);}
.warn .tag{color:var(--warn);}
.practice{background:var(--prac-bg);border-left:4px solid var(--prac);}
.practice .tag{color:var(--prac);}
code{background:var(--code-bg);padding:1px 5px;border-radius:4px;font:13px "SF Mono",Consolas,monospace;}
.callout code{background:rgba(0,0,0,.06);}
table.grid{width:100%;border-collapse:collapse;font-size:14.5px;}
table.grid th,table.grid td{text-align:left;padding:8px 10px;border:1px solid var(--line);vertical-align:top;}
table.grid th{background:var(--code-bg);}
table.data{font:12.5px "SF Mono",Consolas,monospace;}
table.data td,table.data th{padding:5px 8px;}
@media print{.toc{display:none;}.wrap{display:block;}.block{break-inside:avoid;box-shadow:none;}}
@media (max-width:820px){.wrap{grid-template-columns:1fr;}.toc{position:static;}}
"""

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Descriptive Statistics & Distributions — Companion</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Descriptive Statistics &amp; Distributions — Companion</h1>
    <p>Concepts first, on real clinical data. Presenter: Dr. Christine Atuhairwe.</p>
  </header>
  <div class="banner">
    <b>How to read this:</b> every number and chart below was <b>computed live</b> from
    <code>{data}</code> — a simulated cohort of <b>{n} patients</b> (so the points land on real
    clinical variables, not car data). Each step shows the exact <b>Stata command</b>; the purple
    <b>🚗 hands-on</b> boxes map it onto Stata's one-line <code>sysuse auto</code> dataset, which
    we'll use to practise. <b>Scroll top → bottom.</b>
  </div>
  {toc}
  <main>
    {body}
    {guide}
    {glossary}
  </main>
</div>
</body>
</html>
"""


def main():
    body = "\n".join(render_section(s) for s in SECTIONS)
    page = PAGE.format(css=CSS, data=DATA, n=N, toc=render_toc(), body=body,
                       guide=render_guide(), glossary=render_glossary())
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    n_blocks = sum(len(s["blocks"]) for s in SECTIONS)
    print(f"Wrote {OUT}: {len(SECTIONS)} sections, {n_blocks} blocks, "
          f"{len(GLOSSARY)} glossary terms.")
    print(f"Wrote {DATA}: {N} patients, {df.shape[1]} columns.")


if __name__ == "__main__":
    main()
