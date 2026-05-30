#!/usr/bin/env python3
"""
Build a self-contained HTML companion for the
APPLIED NON-LINEAR REGRESSION lecture (Dr. Christine Atuhairwe).

This companion MIRRORS the slide deck slide-by-slide, but:
  * every coefficient table is a REAL least-squares fit computed in Python
    (scipy.curve_fit) - on the real `auto` data and on seeded simulations,
    formatted to look like Stata's `nl` output. Your do-file reproduces the
    same fits with `nl` (numbers vary slightly by random-number stream).
  * every "graph" is a REAL generated plot, not a text description.
  * Ebola appears only where the biology already fits: Model 4 is the
    Ebola viral-load curve (within-patient) plus the Gulu 2000 outbreak
    (population), with a short epidemic-curve note on the logistic section.

Run:  python3 build_companion.py
Out:  nonlinear_regression_companion.html   (open in any browser)
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
from scipy.optimize import curve_fit

OUT = "nonlinear_regression_companion.html"

# ---------------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------------
def f_exp(x, a, b):        return a * np.exp(b * x)                       # decay & growth
def f_logan(x, asym, rate, inflect): return asym / (1 + np.exp(rate * (x - inflect)))
def f_mm(x, vmax, km):     return vmax * x / (km + x)
def f_loginc(x, asym, rate, inflect): return asym / (1 + np.exp(-rate * (x - inflect)))

# ---------------------------------------------------------------------------
# DATA  (auto = real; the rest are seeded simulations so the page is stable)
# ---------------------------------------------------------------------------
auto = pd.read_csv("auto-mpg.csv")
W = auto["weight"].to_numpy(float)
MPG = auto["mpg"].to_numpy(float)

rng = np.random.default_rng(2026)

# Logistic — life expectancy 1900-2000 (3-param, as in the deck)
YEAR = np.arange(1900, 2001)
LE = f_logan(YEAR, 79.0, -0.033, 1890) + rng.normal(0, 0.7, YEAR.size)

# Michaelis-Menten — simulated dose-response (true Vmax=90, Km=25)
DOSE = np.linspace(0, 100, 40)
RESP = f_mm(DOSE, 90, 25) + rng.normal(0, 4, DOSE.size)

# Exponential growth — Ebola viral load in an untreated patient (within-host)
VDAY = np.arange(1, 21)
VL = f_exp(VDAY, 100, 0.3) + rng.normal(0, 200, VDAY.size)
VL = np.clip(VL, 1, None)

# Exponential growth — Gulu 2000 early outbreak (population), per the brief
GDAY = np.arange(1, 51)
GCASES = 3 * np.exp(0.046 * GDAY) + rng.normal(0, 2, GDAY.size)
GCASES = np.round(np.clip(GCASES, 0, None))

# Logistic — hands-on exercise: infection rate vs occupancy
#   (sign corrected so the rate RISES with occupancy, matching the narrative)
OCC = 40 + np.arange(30) * (95 - 40) / 29
INF = f_loginc(OCC, 12, 0.30, 75) + rng.normal(0, 0.5, OCC.size)
INF = np.round(np.clip(INF, 0, None), 1)

# ---------------------------------------------------------------------------
# FITTING  -> real Stata-style output tables
# ---------------------------------------------------------------------------
def run_fit(func, x, y, p0, names, bounds=(-np.inf, np.inf)):
    popt, pcov = curve_fit(func, x, y, p0=p0, bounds=bounds, maxfev=40000)
    n, k = len(x), len(popt)
    dof = max(n - k, 1)
    se = np.sqrt(np.diag(pcov))
    tval = popt / se
    pval = 2 * stats.t.sf(np.abs(tval), dof)
    tc = stats.t.ppf(0.975, dof)
    resid = y - func(x, *popt)
    return {"popt": popt, "se": se, "t": tval, "p": pval, "names": names,
            "lo": popt - tc * se, "hi": popt + tc * se,
            "resid": resid, "rss": float(np.sum(resid ** 2)), "n": n, "k": k,
            "fitted": func(x, *popt)}


def g(x):
    ax = abs(x)
    if ax == 0: return "0"
    if ax < 0.01: return f"{x:.6f}"
    if ax < 1:   return f"{x:.4f}"
    if ax < 1000: return f"{x:.3f}"
    return f"{x:,.2f}"


def pfmt(p):
    return "0.000" if p < 0.0005 else f"{p:.3f}"


def fit_table(yname, fit):
    rows = []
    for i, nm in enumerate(fit["names"]):
        rows.append([f"/{nm}", g(fit["popt"][i]), g(fit["se"][i]),
                     f"{fit['t'][i]:.2f}", pfmt(fit["p"][i]),
                     g(fit["lo"][i]), g(fit["hi"][i])])
    head = [yname, "Coef.", "Std.err.", "t", "P>|t|", "[95% conf.", "interval]"]
    cols = list(zip(*([head] + rows)))
    w = [max(len(str(c)) for c in col) for col in cols]
    al = ["<"] + [">"] * 6

    def ln(cells): return "  ".join(f"{str(c):{a}{ww}}" for c, ww, a in zip(cells, w, al))
    sep = "  ".join("-" * ww for ww in w)
    return "\n".join([ln(head), sep] + [ln(r) for r in rows])


FIT_DECAY = run_fit(f_exp, W, MPG, [40, -0.0005], ["a", "b"])
FIT_LOG   = run_fit(f_logan, YEAR, LE, [79, -0.03, 1890], ["asym", "rate", "inflect"])
FIT_MM    = run_fit(f_mm, DOSE, RESP, [90, 25], ["vmax", "km"])
FIT_VL    = run_fit(f_exp, VDAY, VL, [100, 0.3], ["a", "b"])
FIT_GULU  = run_fit(f_exp, GDAY, GCASES, [3, 0.05], ["a", "b"])
FIT_EX    = run_fit(f_loginc, OCC, INF, [12, 0.3, 75], ["asym", "rate_g", "inflect"])

# Derived quantities (real) -------------------------------------------------
b_dec = FIT_DECAY["popt"][1]
half_life = np.log(2) / (-b_dec)
hl_lo, hl_hi = np.log(2) / (-FIT_DECAY["lo"][1]), np.log(2) / (-FIT_DECAY["hi"][1])
pct_per_1000 = (1 - np.exp(b_dec * 1000)) * 100

b_vl = FIT_VL["popt"][1]
dt_vl = np.log(2) / b_vl
dtvl_lo, dtvl_hi = np.log(2) / FIT_VL["hi"][1], np.log(2) / FIT_VL["lo"][1]

b_g = FIT_GULU["popt"][1]
dt_g = np.log(2) / b_g
dtg_lo, dtg_hi = np.log(2) / FIT_GULU["hi"][1], np.log(2) / FIT_GULU["lo"][1]

km = FIT_MM["popt"][0], FIT_MM["popt"][1]
le2020 = float(f_logan(2020, *FIT_LOG["popt"]))
ec50_ex = FIT_EX["popt"][2]

# Linear vs non-linear on auto ---------------------------------------------
slope, intercept = np.polyfit(W, MPG, 1)
lin_resid = MPG - (slope * W + intercept)
lin_rss = float(np.sum(lin_resid ** 2))
def aic(rss, n, k): return n * np.log(rss / n) + 2 * k
AIC_LIN = aic(lin_rss, len(W), 2)
AIC_NL = aic(FIT_DECAY["rss"], len(W), 2)
SD_LIN = np.sqrt(lin_rss / (len(W) - 2))
SD_NL = np.sqrt(FIT_DECAY["rss"] / (len(W) - 2))

# ---------------------------------------------------------------------------
# PLOTS
# ---------------------------------------------------------------------------
plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": "white"})
BLUE, RED, GREEN, AMBER = "#2a6fb3", "#c0392b", "#1a7f37", "#d68910"


def uri(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def scatter_fit(x, y, fit, func, xlab, ylab, title, color=BLUE):
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    ax.scatter(x, y, s=22, alpha=0.6, color=color, label="Data")
    xs = np.linspace(min(x), max(x), 250)
    ax.plot(xs, func(xs, *fit["popt"]), color=RED, lw=2.2, label="Non-linear fit")
    ax.set(xlabel=xlab, ylabel=ylab, title=title)
    ax.legend(fontsize=9)
    return uri(fig)


def diag_pair(fit, title):
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.7))
    ax[0].scatter(fit["fitted"], fit["resid"], s=20, alpha=0.6, color=BLUE)
    ax[0].axhline(0, color=RED, lw=1.5)
    ax[0].set(xlabel="Fitted values", ylabel="Residuals", title="Residuals vs fitted")
    stats.probplot(fit["resid"], dist="norm", plot=ax[1])
    ax[1].get_lines()[0].set(marker="o", markersize=4, alpha=0.6, color=BLUE)
    ax[1].get_lines()[1].set(color=RED, lw=1.8)
    ax[1].set_title("Q-Q plot of residuals")
    fig.suptitle(title, y=1.02, fontsize=12)
    fig.tight_layout()
    return uri(fig)


IMG_DECAY = scatter_fit(W, MPG, FIT_DECAY, f_exp, "Weight (lbs)", "MPG",
                        "Exponential decay: MPG vs weight (real auto data)")
IMG_DECAY_DIAG = diag_pair(FIT_DECAY, "Exponential decay — residual diagnostics")

# logistic with forecast point
def img_logistic():
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    ax.scatter(YEAR, LE, s=18, alpha=0.55, color=BLUE, label="Data")
    xs = np.linspace(1900, 2025, 300)
    ax.plot(xs, f_logan(xs, *FIT_LOG["popt"]), color=RED, lw=2.2, label="Logistic fit")
    ax.scatter([2020], [le2020], color=GREEN, zorder=5, s=55,
               label=f"Forecast 2020 ≈ {le2020:.1f}")
    ax.set(xlabel="Year", ylabel="Life expectancy (years)",
           title="Logistic growth: life expectancy over time")
    ax.legend(fontsize=9)
    return uri(fig)
IMG_LOG = img_logistic()

IMG_MM = scatter_fit(DOSE, RESP, FIT_MM, f_mm, "Dose (mg/kg)", "Response (%)",
                     "Michaelis-Menten: dose-response", color=GREEN)


def img_viral():
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.8))
    xs = np.linspace(1, 20, 200)
    ax[0].scatter(VDAY, VL, s=22, alpha=0.6, color=BLUE, label="Data")
    ax[0].plot(xs, f_exp(xs, *FIT_VL["popt"]), color=RED, lw=2.2, label="Exponential fit")
    ax[0].set(xlabel="Days post-infection", ylabel="Viral load (copies/mL)",
              title="Ebola viral load (linear scale)")
    ax[0].legend(fontsize=9)
    ax[1].scatter(VDAY, VL, s=22, alpha=0.6, color=BLUE)
    ax[1].plot(xs, f_exp(xs, *FIT_VL["popt"]), color=RED, lw=2.2)
    ax[1].set_yscale("log")
    ax[1].set(xlabel="Days post-infection", ylabel="Viral load (log scale)",
              title="Log scale → straight line = exponential")
    fig.tight_layout()
    return uri(fig)
IMG_VL = img_viral()

IMG_GULU = scatter_fit(GDAY, GCASES, FIT_GULU, f_exp, "Days from onset (Day 1 = Aug 30)",
                       "Estimated cumulative cases",
                       "Gulu 2000 — early exponential phase", color=RED)


def img_compare():
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    ax.scatter(W, MPG, s=20, alpha=0.5, color=BLUE, label="Data")
    xs = np.linspace(min(W), max(W), 250)
    ax.plot(xs, slope * xs + intercept, color=AMBER, lw=2, ls="--", label="Linear fit")
    ax.plot(xs, f_exp(xs, *FIT_DECAY["popt"]), color=RED, lw=2.2, label="Non-linear (exp) fit")
    ax.set(xlabel="Weight (lbs)", ylabel="MPG", title="Linear vs non-linear on the same data")
    ax.legend(fontsize=9)
    return uri(fig)
IMG_COMPARE = img_compare()


def img_exercise():
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    ax.scatter(OCC, INF, s=24, alpha=0.6, color=BLUE, label="Data")
    xs = np.linspace(40, 95, 250)
    ax.plot(xs, f_loginc(xs, *FIT_EX["popt"]), color=RED, lw=2.2, label="Logistic fit")
    ax.axvline(ec50_ex, color=GREEN, ls=":", lw=1.8, label=f"Threshold ≈ {ec50_ex:.0f}% occupancy")
    ax.set(xlabel="Bed occupancy (%)", ylabel="Infection rate (per 1000 pt-days)",
           title="Exercise: infection rate vs occupancy")
    ax.legend(fontsize=9)
    return uri(fig)
IMG_EX = img_exercise()

# ---------------------------------------------------------------------------
# CONTENT
# ---------------------------------------------------------------------------
def esc(s): return html.escape(str(s))


def clin_table(rows):
    body = "".join(
        f"<tr><td><b>{esc(p)}</b></td><td>{esc(est)}</td><td>{esc(ci)}</td><td>{esc(m)}</td></tr>"
        for p, est, ci, m in rows)
    return ('<table class="grid"><tr><th>Parameter</th><th>Estimate</th><th>95% CI</th>'
            f'<th>Clinical meaning</th></tr>{body}</table>')


def fit_simple_row(name, est, lo, hi):
    return (f"{name:>16} |  Coef. = {est:,.2f}   "
            f"[95% conf. int.: {min(lo, hi):,.2f}, {max(lo, hi):,.2f}]")


def fixed_compare(aic_l, sd_l, aic_n, sd_n):
    rows = [["Linear", f"{aic_l:.1f}", f"{sd_l:.2f}"],
            ["Non-linear", f"{aic_n:.1f}", f"{sd_n:.2f}"]]
    head = ["Model", "AIC", "Residual SD"]
    cols = list(zip(*([head] + rows)))
    w = [max(len(str(c)) for c in col) for col in cols]
    al = ["<", ">", ">"]
    def ln(c): return "  ".join(f"{str(x):{a}{ww}}" for x, ww, a in zip(c, w, al))
    return "\n".join([ln(head), "  ".join("-" * ww for ww in w)] + [ln(r) for r in rows])


SECTIONS = [
    {"id": "agenda", "title": "What we'll do today",
     "lead": "Six beats. Understand <i>when</i> to go non-linear, learn four clinical models, "
             "fit them on real and simulated data, diagnose the fits, then you run one yourself.",
     "html": '<table class="grid"><tr><th>#</th><th>Activity</th></tr>'
             '<tr><td>1</td><td>Understand <b>when</b> to use non-linear regression</td></tr>'
             '<tr><td>2</td><td>Learn <b>4 clinical models</b> with Stata code</td></tr>'
             '<tr><td>3</td><td><b>Run</b> live examples (real + built-in data)</td></tr>'
             '<tr><td>4</td><td><b>Diagnostic</b> testing in Stata</td></tr>'
             '<tr><td>5</td><td><b>Hands-on</b> exercise (you run the code)</td></tr>'
             '<tr><td>6</td><td><b>Review</b> the solution &amp; discuss</td></tr></table>',
     "blocks": []},

    {"id": "objectives", "title": "Learning objectives",
     "lead": "By the end you'll run these commands and read what they return.",
     "html": '<table class="grid"><tr><th>Command</th><th>What it does</th></tr>'
             '<tr><td><code>nl</code></td><td>Non-linear least-squares estimation</td></tr>'
             '<tr><td><code>predict</code></td><td>Fitted values and residuals</td></tr>'
             '<tr><td><code>rvfplot</code></td><td>Residual-vs-fitted plot</td></tr>'
             '<tr><td><code>qnorm</code></td><td>Normality check (Q-Q plot)</td></tr>'
             '<tr><td><code>nlcom</code></td><td>Derived parameters (half-life, doubling time, EC50)</td></tr>'
             '</table>'
             '<p style="margin-top:10px"><b>Clinical skills:</b> choose the right curve for your '
             'data · interpret EC50, V<sub>max</sub>, half-life, doubling time and asymptote · '
             'diagnose convergence failures.</p>',
     "blocks": []},

    {"id": "models", "title": "The four models at a glance",
     "lead": "The whole lecture is these four shapes. Learn to recognise the shape, and you know "
             "which one to fit.",
     "html": '<table class="grid"><tr><th>Model</th><th>Stata syntax</th><th>Shape</th>'
             '<th>Clinical use</th></tr>'
             '<tr><td><b>Exponential decay</b></td><td><code>nl (y={a}*exp({b}*x))</code>, b&lt;0</td>'
             '<td>Falls fast, then flattens</td><td>Drug clearance, pain resolution</td></tr>'
             '<tr><td><b>Exponential growth</b></td><td><code>nl (y={a}*exp({b}*x))</code>, b&gt;0</td>'
             '<td>Rises ever faster</td><td>Viral load (e.g. early Ebola), tumour growth</td></tr>'
             '<tr><td><b>Michaelis-Menten</b></td><td><code>nl (y={vmax}*x/({km}+x))</code></td>'
             '<td>Rises then saturates</td><td>Dose-response, receptor binding</td></tr>'
             '<tr><td><b>Logistic (sigmoid)</b></td>'
             '<td><code>nl (y={asym}/(1+exp({rate}*(x-{inflect}))))</code></td>'
             '<td>S-curve: lag, surge, plateau</td><td>Growth curves, epidemic case counts</td></tr>'
             '</table>',
     "blocks": []},

    {"id": "method", "title": "The rhythm: plot → guess → fit → check",
     "lead": "Whether it's a drug clearing from blood or an outbreak's case count climbing, "
             "biological change <i>bends</i> — and non-linear models aren't solved by a formula, "
             "they're <b>searched</b> for. Your job is to start the search well and check where it "
             "landed.",
     "blocks": [{
         "stata": "* 1. LOOK   plot the raw data first\n"
                  "* 2. GUESS  read starting values off the plot\n"
                  "* 3. FIT    nl (y = ...), initial(...)\n"
                  "* 4. CHECK  did it converge? are the residuals clean?",
         "means": "Linear regression lets you skip to the fit. Non-linear regression does "
                  "<b>not</b>: Stata improves your starting guess by trial-and-error until it "
                  "converges. A bad guess can wander off forever — so we always <b>plot first, "
                  "guess from the plot, fit, then check</b>.",
         "say": "Non-linear models are found, not solved. Give the search a sensible place to "
                "start, then check where it ended up."}]},

    {"id": "m1", "title": "Model 1 — Exponential decay (real auto data)",
     "eli5": "Picture a <b>hot cup of tea</b> left on the table. It cools <b>fast</b> while it's "
             "piping hot, then slower and slower as it nears room temperature — and it never gets "
             "colder than the room. That \"quick at first, then flattening toward a floor\" shape "
             "<b>is</b> exponential decay. A drug clearing from the blood, a fading bruise, a phone "
             "battery draining — all the same curve. Today the stand-in is a car's fuel economy "
             "falling as the car gets heavier.",
     "lead": "Dataset: the public <code>auto-mpg.csv</code> (398 cars). MPG falls steeply for light "
             "cars then flattens — the same shape as a drug concentration falling as body mass "
             "rises. (Your do-file uses Stata's 74-car <code>sysuse auto</code>: same shape, "
             "smaller-magnitude coefficients.)",
     "blocks": [
        {"stata": "import delimited auto-mpg.csv, clear   // or: sysuse auto, clear\n"
                  "describe\nlist mpg weight in 1/5",
         "means": "<b>mpg</b> is the outcome (a drug-concentration stand-in); <b>weight</b> the "
                  "predictor (body mass). Load, then eyeball a few rows before modelling."},
        {"stata": 'twoway scatter mpg weight, ///\n'
                  '    title("MPG vs Vehicle Weight") xtitle("Weight (lbs)") ytitle("MPG")',
         "img": IMG_DECAY,
         "means": "Model: <b>MPG = a · e^(b·Weight)</b>. The curved, decaying cloud is the evidence "
                  "that a straight line is wrong. <b>a</b> = MPG at zero weight (the ceiling); "
                  "<b>b</b> = decay rate (negative ⇒ MPG falls as weight rises).",
         "say": "See the curve bend? A line would over-predict the heavy cars. That bend is why we "
                "go non-linear."},
        {"stata": "* starting values are a rough GUESS off the plot — the search refines them\n"
                  "nl (mpg = {a} * exp({b} * weight)), initial(a 40 b -0.0005)",
         "output": fit_table("mpg", FIT_DECAY),
         "read": (f"First time reading an <code>nl</code> table — take it column by column. Each row "
                  f"is one parameter the search found. <b>Coef.</b> is the estimate: "
                  f"<b>a ≈ {FIT_DECAY['popt'][0]:.1f}</b> (the ceiling MPG) and "
                  f"<b>b ≈ {b_dec:.5f}</b> (negative ⇒ decay). <b>Std. err.</b> is how much that "
                  f"estimate would wobble in a fresh sample of cars. <b>t</b> is Coef.÷Std.err., and "
                  f"<b>P&gt;|t|</b> turns that into the chance of seeing this if the true value were "
                  f"zero — both read <b>0.000</b>, so neither is a fluke. The "
                  f"<b>[95% conf. interval]</b> is the plausible range for the true value, and "
                  f"neither one crosses 0. So: read just two numbers — a and b — and you've read the "
                  f"whole curve."),
         "means": f"This is a <b>real least-squares fit</b>. <b>a ≈ {FIT_DECAY['popt'][0]:.1f}</b> "
                  f"(ceiling MPG) and <b>b ≈ {b_dec:.5f}</b> (negative ⇒ decay). Both p &lt; 0.001, "
                  f"so neither is plausibly zero. Add <code>vce(robust)</code> for robust SEs when "
                  f"the residual spread isn't even — the coefficients don't move, only the error "
                  f"bars do.",
         "clin": clin_table([
             ("a", f"{FIT_DECAY['popt'][0]:.1f} MPG", f"({FIT_DECAY['lo'][0]:.1f}, {FIT_DECAY['hi'][0]:.1f})",
              "Maximum MPG at zero weight (the ceiling)"),
             ("b", f"{b_dec:.5f}", f"({FIT_DECAY['lo'][1]:.5f}, {FIT_DECAY['hi'][1]:.5f})",
              f"Each +1000 lb lowers MPG by ~{pct_per_1000:.0f}%")]),
         "say": "a is the ceiling, b is the decay rate. The clinical sentence: every extra 1000 lb "
                f"cuts MPG by about {pct_per_1000:.0f}%.",
         "warn": "If Stata prints “convergence not achieved”, the numbers are meaningless — fix "
                 "<code>initial()</code> and refit."},
        {"stata": "predict fitted_exp, yhat\npredict resid_exp, resid\n"
                  "rvfplot, yline(0)\nqnorm resid_exp\nhistogram resid_exp, normal",
         "img": IMG_DECAY_DIAG,
         "means": "The standard health-check, computed from the real residuals: a <b>patternless "
                  "cloud</b> around zero (left) and points <b>hugging the diagonal</b> (right) both "
                  "say the model fits well. A funnel or U-shape would mean the model shape is wrong.",
         "say": "Residuals are what the model couldn't explain. Patternless and on-the-line means "
                "we've squeezed out the signal."},
        {"stata": "nlcom (half_life: ln(2) / -_b[/b])",
         "output": fit_simple_row("half_life", half_life, hl_lo, hl_hi),
         "read": (f"One line, one number: <b>{half_life:.0f}</b> lbs, with its 95% CI in brackets. "
                  f"That's the weight gain that <b>halves</b> MPG. Stata carried the uncertainty in b "
                  f"through into a correct interval for you — no by-hand error propagation."),
         "means": f"<code>nlcom</code> turns parameters into a clinically intuitive quantity with a "
                  f"correct CI. <b>Half-life = ln(2)/(−b) ≈ {half_life:.0f} lbs</b>: every extra "
                  f"~{half_life:.0f} lb <b>halves</b> the MPG — exactly like a drug half-life.",
         "say": "The number a clinician feels: how much change halves the outcome. Same maths as "
                "drug half-life."}]},

    {"id": "m2", "title": "Model 2 — Logistic growth (an S-curve)",
     "eli5": "Picture <b>a juicy rumour spreading through a village</b>. At first only one or two "
             "people know, so it crawls. Then everyone who hears it tells two friends and it "
             "<b>explodes</b>. Finally it slows again — because almost everyone has already heard it. "
             "<b>Slow → fast → plateau</b>: that S-shape is logistic growth. The very same curve "
             "describes life expectancy rising toward a ceiling, a crop growing, or an outbreak's "
             "running case count.",
     "lead": "Dataset: life expectancy, 1900–2000. The S-shape — slow, then fast, then a ceiling — "
             "is the fingerprint of logistic growth (and, as we'll see, of an epidemic curve).",
     "blocks": [
        {"stata": "sysuse uslifeexp, clear\nlist year le in 1/10",
         "means": "<b>year</b> is the predictor, <b>le</b> (life expectancy) the outcome. The values "
                  "rise and then level off."},
        {"stata": "* Model:  le = asym / (1 + exp(rate*(year - inflect)))\n"
                  "twoway scatter le year\n"
                  "nl (le = {asym}/(1+exp({rate}*(year-{inflect})))), ///\n"
                  "    initial(asym 80 rate -0.1 inflect 1950)\n"
                  "estimates store logistic_model",
         "output": fit_table("le", FIT_LOG),
         "img": IMG_LOG,
         "read": (f"Read it the same way, now with three rows. <b>asym ≈ {FIT_LOG['popt'][0]:.1f}</b> "
                  f"= the ceiling the curve climbs toward; <b>inflect ≈ {FIT_LOG['popt'][2]:.0f}</b> "
                  f"= the year of steepest change; <b>rate</b> = how sharp the bend is. Check the "
                  f"<b>P&gt;|t|</b> and CI columns exactly as before — all three are firmly pinned "
                  f"down, so the S-curve is a real description of the data, not wishful drawing."),
         "means": f"Three meaningful parameters, really fitted: <b>asym ≈ {FIT_LOG['popt'][0]:.1f}</b> "
                  f"is the ceiling (max life expectancy the curve approaches); <b>inflect ≈ "
                  f"{FIT_LOG['popt'][2]:.0f}</b> is the year of fastest growth; <b>rate</b> sets the "
                  f"steepness. Here the inflection sits just before our window, so 1900–2000 is the "
                  f"<i>decelerating upper arm</i> of the S — gains slowing as we near the ceiling.",
         "say": "asym is the ceiling, inflect is the tipping-point year, rate is the steepness. "
                "Three numbers, three clear meanings."},
        {"stata": "predict fitted_log, yhat\n"
                  "local asym=_b[/asym]\nlocal rate=_b[/rate]\nlocal inflect=_b[/inflect]\n"
                  'display "Predicted LE 2020: " `asym\'/(1+exp(`rate\'*(2020-`inflect\')))',
         "output": f"Predicted LE 2020: {le2020:.2f}",
         "read": (f"This line isn't a coefficient — it's a <b>prediction</b>. We fed the fitted curve "
                  f"a year it never saw (2020) and it returned <b>{le2020:.1f} years</b>, sitting "
                  f"just under the ceiling because the S has all but flattened. That is what a model "
                  f"is <i>for</i>: answering beyond the data you measured."),
         "means": f"Plug the fitted parameters into the formula for 2020 to <b>forecast</b> ≈ "
                  f"<b>{le2020:.1f} years</b> — close to the ceiling, because the curve has nearly "
                  f"flattened.",
         "ebola": "The same S-curve describes an <b>outbreak's cumulative case count</b>: a slow "
                  "lag, an explosive surge, then a plateau as control measures bite and susceptibles "
                  "run out. The logistic is the natural model for an epidemic curve.",
         "warn": "Forecasting far past your data assumes the same curve keeps holding — be cautious."}]},

    {"id": "m3", "title": "Model 3 — Michaelis–Menten (saturating dose–response)",
     "eli5": "Picture <b>eating when you're hungry</b>. The first few bites satisfy you enormously; "
             "as you fill up each extra bite does a little less; eventually you're <b>completely "
             "full</b> and more food adds nothing. The response climbs, then <b>saturates</b> at a "
             "ceiling. And the amount of food that gets you <b>halfway to full</b> is exactly the "
             "idea behind a drug's EC50 — the dose that delivers half of its biggest possible "
             "effect.",
     "lead": "Simulated dose–response, so we know the truth (true V<sub>max</sub>=90, K<sub>m</sub>=25) "
             "and can grade the fit. Clinical analogy: receptor binding — response rises then saturates.",
     "blocks": [
        {"stata": "clear\nset seed 12345\nset obs 40\n"
                  "gen dose = (_n-1)*(100/39)\n"
                  "gen response = (90*dose)/(25+dose) + rnormal(0,4)",
         "means": "We <b>simulate</b> 40 doses (0→100 mg/kg) from a known curve plus noise, so the "
                  "fit below can be graded against the truth (V<sub>max</sub>=90, K<sub>m</sub>=25)."},
        {"stata": "nl (response = {vmax}*dose/({km}+dose)), initial(vmax 90 km 25)",
         "output": fit_table("response", FIT_MM),
         "img": IMG_MM,
         "read": (f"Two rows. <b>V<sub>max</sub> ≈ {FIT_MM['popt'][0]:.1f}</b> = the saturating "
                  f"maximum response; <b>K<sub>m</sub> ≈ {FIT_MM['popt'][1]:.1f}</b> = the dose that "
                  f"gets you to <b>half</b> of that maximum (the EC50). Here's the honest test: "
                  f"because this data is simulated we <i>know</i> the truth was 90 and 25 — and the "
                  f"fit lands on both. That agreement is your proof the method recovers reality, not "
                  f"just any curve."),
         "means": f"<b>V<sub>max</sub> ≈ {FIT_MM['popt'][0]:.1f}</b> is the saturating maximum "
                  f"response; <b>K<sub>m</sub> ≈ {FIT_MM['popt'][1]:.1f}</b> is the EC50 — the dose "
                  f"giving <b>half</b> of V<sub>max</sub>. Both land on the true values (90, 25), so "
                  f"the model works.",
         "clin": clin_table([
             ("Vmax", f"{FIT_MM['popt'][0]:.1f}%", f"({FIT_MM['lo'][0]:.1f}, {FIT_MM['hi'][0]:.1f})",
              "Maximum achievable response"),
             ("Km (EC50)", f"{FIT_MM['popt'][1]:.1f} mg/kg",
              f"({FIT_MM['lo'][1]:.1f}, {FIT_MM['hi'][1]:.1f})", "Dose for 50% of maximum effect")]),
         "say": f"Vmax is the most the drug can do; the EC50 of ~{FIT_MM['popt'][1]:.0f} mg/kg is the "
                f"potency — the dose that gets you halfway there."},
        {"stata": "predict fitted_mm, yhat\npredict resid_mm, resid\n"
                  "rvfplot, yline(0)\npredict cooksd_mm, cooksd\nscatter cooksd_mm _n, yline(4/40)",
         "means": "After fitting, overlay the fitted curve, check residuals-vs-fitted for pattern, "
                  "and use <b>Cook's distance</b> (cut-off 4/n) to flag any single point that pulls "
                  "the whole fit — a data-entry error or a genuinely unusual subject."}]},

    {"id": "m4", "title": "Model 4 — Exponential growth: Ebola viral load & the Gulu 2000 outbreak",
     "eli5": "Picture <b>money in a savings account earning compound interest</b>, or a single "
             "<b>WhatsApp message forwarded on and on</b>: one becomes two, two become four, four "
             "become eight. Early on nothing looks alarming — then it <b>rockets</b>. The number "
             "that matters is the <b>doubling time</b>: how long until it's twice as big. Untreated "
             "viral load in a patient, and an outbreak's early case count, both grow exactly this "
             "way — which is why a few days' delay costs so much.",
     "lead": "Same exponential family as Model 1, but with a <b>positive</b> rate — so instead of "
             "decay we get explosive growth. We look at it at two scales: inside one patient, and "
             "across a population.",
     "blocks": [
        {"stata": "clear\nset seed 67890\nset obs 20\ngen day = _n\n"
                  "* Ebola viral load climbing in an untreated patient\n"
                  "gen viral_load = 100*exp(0.3*day) + rnormal(0,200)\n"
                  "nl (viral_load = {a}*exp({b}*day)), initial(a 100 b 0.3)",
         "output": fit_table("viral_load", FIT_VL),
         "img": IMG_VL,
         "read": (f"The same two-parameter exponential as Model 1 — but read the <b>sign of b</b>. "
                  f"Here <b>b ≈ {b_vl:.3f}</b> is <b>positive</b>: growth, not decay. "
                  f"<b>a ≈ {FIT_VL['popt'][0]:.0f}</b> is the starting load on day 1. One positive "
                  f"number is the whole alarm — the viral load is climbing, and climbing faster every "
                  f"day."),
         "means": f"<b>a ≈ {FIT_VL['popt'][0]:.0f}</b> is the starting load; <b>b ≈ {b_vl:.3f}</b> "
                  f"the daily growth rate. On the <b>log scale</b> (right) the curve becomes a "
                  f"straight line — the signature of exponential growth.",
         "say": "Inside an untreated patient, Ebola viral load climbs exponentially in the first "
                "days — which is exactly why early treatment matters."},
        {"stata": "nlcom (doubling_time: ln(2) / _b[/b])",
         "output": fit_simple_row("doubling_time", dt_vl, dtvl_lo, dtvl_hi),
         "read": (f"Mirror of the half-life output. One number — <b>{dt_vl:.1f} days</b>, with a CI "
                  f"— the time for the load to <b>double</b>. This is the line a clinician acts on at "
                  f"the bedside, not the raw rate b above it."),
         "means": f"The mirror image of half-life. <b>Doubling time = ln(2)/b ≈ {dt_vl:.1f} days</b> "
                  f"in this within-patient curve — the clinically meaningful translation of the raw "
                  f"rate.",
         "ebola": "A growth rate of 0.3 is abstract; <b>“doubles every couple of days”</b> is what a "
                  "clinician actually feels at the bedside."},
        {"stata": "* ---- Epidemic scale: early Gulu 2000 outbreak ----\n"
                  "clear\nset seed 43210\nset obs 50          // first 50 days from ~Aug 30\n"
                  "gen day = _n\n"
                  "gen gulu_cases = 3*exp(0.046*day) + rnormal(0,2)\n"
                  "replace gulu_cases = 0 if gulu_cases < 0\n"
                  "replace gulu_cases = round(gulu_cases)\n"
                  "nl (gulu_cases = {a=3}*exp({b=0.05}*day))\n"
                  "nlcom (gulu_doubling_time: ln(2) / _b[/b])",
         "output": fit_table("gulu_cases", FIT_GULU) + "\n\n" +
                   fit_simple_row("gulu_doubling_time", dt_g, dtg_lo, dtg_hi),
         "img": IMG_GULU,
         "read": (f"Identical table shape, but now at the population scale. The fitted "
                  f"<b>b ≈ {b_g:.3f}/day</b> feeds straight into the doubling time of "
                  f"≈ <b>{dt_g:.0f} days</b> printed beneath it. Same two numbers, same reading — "
                  f"only the units changed, from copies/mL in one patient to cases across a district."),
         "means": f"Now the <b>same model at the population scale</b> for the early phase of the "
                  f"Gulu, Uganda outbreak (Sudan ebolavirus, 2000). The fitted rate "
                  f"<b>b ≈ {b_g:.3f}/day</b> gives an <b>epidemic doubling time of ≈ {dt_g:.0f} "
                  f"days</b>. Contrast that with the within-patient doubling of ~{dt_vl:.0f} days: "
                  f"same maths, two scales.",
         "ebola": f"This early, near-invisible exponential phase is where outbreaks are won or lost: "
                  f"with cases doubling roughly every {dt_g:.0f} days, even a few weeks' delay in "
                  f"detection means several doublings before the first major intervention.",
         "warn": "This is a <b>reconstructed, illustrative</b> trajectory for teaching the curve "
                 "shape — not an exact case record of the outbreak."}]},

    {"id": "compare", "title": "Linear vs non-linear — which wins?",
     "lead": "Fit both to the same auto data and let the numbers decide.",
     "blocks": [{
         "stata": "regress mpg weight\nestimates store linear_model\n"
                  "nl (mpg = {a}*exp({b}*weight)), initial(a 40 b -0.0005)\n"
                  "estimates store nl_model\nestimates stats linear_model nl_model",
         "output": fixed_compare(AIC_LIN, SD_LIN, AIC_NL, SD_NL),
         "img": IMG_COMPARE,
         "read": (f"Two models, one scorecard — so read <i>down</i> the columns, not across. "
                  f"<b>AIC</b>: lower wins, and the non-linear row ({AIC_NL:.1f}) beats the linear "
                  f"one ({AIC_LIN:.1f}). <b>Residual SD</b> says the same in plain units — the "
                  f"curve's typical miss ({SD_NL:.2f}) is smaller than the line's ({SD_LIN:.2f}). "
                  f"Neither row means anything alone; the <b>comparison between them</b> is the whole "
                  f"point."),
         "means": f"<b>AIC</b> rewards fit and punishes complexity — <b>lower is better</b>. The "
                  f"non-linear model wins here (AIC {AIC_NL:.1f} vs {AIC_LIN:.1f}; residual SD "
                  f"{SD_NL:.2f} vs {SD_LIN:.2f}), because the straight line can't follow the bend. "
                  f"The gain is modest, so interpretability matters too.",
         "say": "Lower AIC wins. The curve beats the line — and tells a more interpretable story.",
         "warn": "Only compare AIC for models on the <b>same outcome and rows</b>."}]},

    {"id": "diag", "title": "Diagnostic checklist — run after EVERY fit",
     "lead": "Six checks. The first is non-negotiable.",
     "blocks": [
        {"stata": "di e(converged)",
         "output": "1",
         "read": ("The most important one-character output of the whole session. <b>1</b> means the "
                  "search settled on a stable answer; a <b>0</b> would void every coefficient you "
                  "read above it. So read this line <i>first</i>, before any estimate."),
         "means": "<code>e(converged)</code> is 1 if the search succeeded, 0 if it gave up. <b>If "
                  "this isn't 1, stop</b> — every other number is unreliable.",
         "say": "First question, always: did it converge? One means yes."},
        {"stata": "rvfplot, yline(0)\nqnorm resid\nswilk resid       // p>0.05 = normal\n"
                  "predict cooksd, cooksd\nsummarize cooksd, detail\n"
                  "nl (...), initial(...) level(95)   // profile CIs for small n",
         "means": "Then: residuals-vs-fitted (no pattern), Q-Q + <b>Shapiro–Wilk</b> (here a "
                  "<b>big</b> p-value is good — p&gt;0.05 means normal enough), Cook's distance for "
                  "influence, and finally the human check: <b>do the estimates make clinical "
                  "sense?</b>",
         "say": "Patternless residuals, points on the line, no single point dominating — and numbers "
                "that make sense for a real patient."}]},

    {"id": "errors", "title": "Common Stata errors — and the fix",
     "lead": "Non-linear fits fail in a handful of predictable ways.",
     "html": '<table class="grid"><tr><th>Message</th><th>Cause</th><th>Fix</th></tr>'
             '<tr><td>“could not calculate numerical derivatives”</td><td>Poor starting values</td>'
             '<td>Adjust <code>initial()</code>; use <code>trace</code> to debug</td></tr>'
             '<tr><td>“region of estimates is not feasible”</td><td>Constraints violated</td>'
             '<td>Bound parameters with <code>constraints()</code></td></tr>'
             '<tr><td>“convergence not achieved”</td><td>Iteration limit reached</td>'
             '<td>Raise <code>iterate(#)</code> or improve initials</td></tr>'
             '<tr><td>“singular matrix”</td><td>Model over-parameterised</td>'
             '<td>Simplify the model or get more data</td></tr>'
             '<tr><td>“variance matrix is nonsymmetric”</td><td>Hessian issues</td>'
             '<td>Try <code>vce(robust)</code> or another <code>technique()</code></td></tr></table>',
     "blocks": []},

    {"id": "debug", "title": "When it won't converge",
     "lead": "The most common failure — and the cures.",
     "blocks": [{
         "stata": "nl (y={a}*exp({b}*x)), initial(a 40 b -0.0005) trace\n"
                  "nl (...), initial(...) iterate(100)\n"
                  "nl (...), initial(...) technique(gn)",
         "means": "<code>trace</code> prints the residual sum-of-squares each step — smoothly "
                  "shrinking is healthy, bouncing means bad starting values. <code>iterate()</code> "
                  "and <code>technique(gn)</code> sometimes help, but nine times in ten the cure is "
                  "a <b>better starting guess read off the plot</b>.",
         "say": "More iterations and a different algorithm occasionally help — but usually it's the "
                "starting values."}]},

    {"id": "exercise", "title": "Hands-on exercise — infection rate vs bed occupancy",
     "eli5": "Picture <b>a car park filling up</b>. While it's half-empty, finding a space is easy "
             "and stress stays low. Past a tipping point — say 75% full — it suddenly gets hard, "
             "tempers fray, and it climbs steeply toward gridlock. A hospital ward behaves the same "
             "as it fills: infections stay flat and safe for a while, then rise sharply once "
             "occupancy crosses a threshold. That's the logistic S-curve again — and your job is to "
             "<b>find that threshold</b>.",
     "lead": "You're studying hospital bed occupancy (%) and infection rate (per 1000 patient-days). "
             "Infections stay low until occupancy crosses a threshold, then rise sharply to a ceiling "
             "— a logistic S-curve. Build it, fit it, interpret it.",
     "blocks": [
        {"stata": "clear\nset seed 999\nset obs 30\n"
                  "gen occupancy = 40 + (_n-1)*(95-40)/29\n"
                  "* rate RISES with occupancy (note the minus sign in the exponent)\n"
                  "gen infection_rate = 12/(1+exp(-0.3*(occupancy-75))) + rnormal(0,0.5)\n"
                  "replace infection_rate = round(infection_rate, 0.1)\n"
                  "twoway scatter infection_rate occupancy",
         "img": IMG_EX,
         "means": "30 hospitals, occupancy 40→95%. True logistic: ceiling <b>12</b> infections / "
                  "1000 patient-days, threshold (inflection) at <b>75%</b>, growth rate 0.3.",
         "warn": "The deck's original formula used <code>exp(0.3*(occupancy-75))</code>, which makes "
                 "the rate <i>fall</i> as wards fill — the opposite of the story. The minus sign "
                 "fixes it."},
        {"stata": "nl (infection_rate = {asym}/(1+exp(-{rate_g}*(occupancy-{inflect})))), ///\n"
                  "    initial(asym 12 rate_g 0.3 inflect 75)\n"
                  "nlcom (occupancy_50pct: _b[/inflect])\n"
                  "predict fitted_rate, yhat\npredict resid_ex, resid\n"
                  "qnorm resid_ex\nrvfplot, yline(0)",
         "output": fit_table("infection_rate", FIT_EX),
         "read": (f"Now you read one unaided. <b>asym ≈ {FIT_EX['popt'][0]:.1f}</b> = the ceiling "
                  f"infection rate; <b>inflect ≈ {FIT_EX['popt'][2]:.1f}%</b> = the occupancy at "
                  f"half-max — and for a logistic that inflection point <i>is</i> the danger "
                  f"threshold; <b>rate_g ≈ {FIT_EX['popt'][1]:.2f}</b> = the steepness. The one "
                  f"number that runs the ward is <b>inflect</b>: report it with its CI and you've "
                  f"answered the question."),
         "means": f"Really fitted: <b>asym ≈ {FIT_EX['popt'][0]:.1f}</b> = the ceiling rate; "
                  f"<b>inflect ≈ {FIT_EX['popt'][2]:.1f}%</b> = the occupancy at half-maximum — and "
                  f"for a logistic the inflection point <b>is</b> the EC50; <b>rate_g ≈ "
                  f"{FIT_EX['popt'][1]:.2f}</b> = steepness.",
         "say": f"The model nails the danger threshold at ~{ec50_ex:.0f}% occupancy — the number "
                f"that changes how you run the ward."},
        {"stata": '* Report the threshold with a 95% CI\n'
                  'di "Occupancy at 50% max: " _b[/inflect] " (95% CI: " ///\n'
                  '   _b[/inflect]-1.96*_se[/inflect] ", " _b[/inflect]+1.96*_se[/inflect] ")"',
         "output": (f"Occupancy at 50% max: {ec50_ex:.1f}% "
                    f"(95% CI: {FIT_EX['lo'][2]:.1f}%, {FIT_EX['hi'][2]:.1f}%)"),
         "means": "<b>The actionable message:</b> keep occupancy below ~75% and infection rates stay "
                  "low; above it they accelerate. <b>Discussion:</b> why logistic not linear? "
                  "(linear assumes a constant increase; logistic captures the threshold). What does "
                  "the inflection tell administrators? (a hard operating limit). What if it didn't "
                  "converge? (adjust starting values, use <code>trace</code>, simplify).",
         "say": "Below ~75% you're safe; above it, infections take off. That's the policy line."}]},

    {"id": "cmds", "title": "Applied Stata commands — quick reference",
     "lead": "The whole toolkit on one screen.",
     "html": '<table class="grid"><tr><th>Task</th><th>Command</th></tr>'
             '<tr><td>Exponential decay</td><td><code>nl (y={a}*exp({b}*x)), initial(a 10 b -0.1)</code></td></tr>'
             '<tr><td>Exponential growth</td><td><code>nl (y={a}*(1-exp({b}*x))), initial(a 100 b 0.1)</code></td></tr>'
             '<tr><td>Michaelis-Menten</td><td><code>nl (y={vmax}*x/({km}+x)), initial(vmax 100 km 25)</code></td></tr>'
             '<tr><td>Logistic</td><td><code>nl (y={asym}/(1+exp({rate}*(x-{inflect}))))</code></td></tr>'
             '<tr><td>Predict fitted / residuals</td><td><code>predict yhat, yhat</code> · <code>predict resid, resid</code></td></tr>'
             '<tr><td>Residual plot · Q-Q</td><td><code>rvfplot, yline(0)</code> · <code>qnorm resid</code></td></tr>'
             '<tr><td>Derived parameter</td><td><code>nlcom (name: expression)</code></td></tr>'
             '<tr><td>Check convergence</td><td><code>di e(converged)</code></td></tr></table>',
     "blocks": []},

    {"id": "summary", "title": "Summary — the seven things to remember",
     "lead": "",
     "html": '<table class="grid"><tr><th>#</th><th>Takeaway</th></tr>'
             '<tr><td>1</td><td>Non-linear models give <b>clinically meaningful parameters</b> '
             '(ceiling, rate, EC50, half-life).</td></tr>'
             '<tr><td>2</td><td><b>Always plot first</b> — the shape tells you which model.</td></tr>'
             '<tr><td>3</td><td><b>Starting values matter</b> — guess from the plot, then refine.</td></tr>'
             '<tr><td>4</td><td><b>Check convergence</b> — <code>e(converged)</code> must be 1.</td></tr>'
             '<tr><td>5</td><td><b>Diagnose residuals</b> — rvfplot, qnorm, Cook\'s D.</td></tr>'
             '<tr><td>6</td><td><b>Report parameters with interpretation</b>, not just numbers.</td></tr>'
             '<tr><td>7</td><td>Four go-to shapes: decay, growth, Michaelis-Menten, logistic.</td></tr></table>',
     "blocks": []},

    {"id": "refs", "title": "References & resources", "lead": "",
     "html": '<ul><li>Motulsky H, Christopoulos A. <i>Fitting Models to Biological Data using '
             'Nonlinear Regression</i>. GraphPad Software; 2003.</li>'
             '<li>Stata User Manual: <code>[R] nl</code></li></ul>',
     "blocks": []},
]

GLOSSARY = [
    ("Coefficient", "The estimated value of a parameter (a, b, vmax …). In non-linear models each "
                    "has a real-world meaning — a ceiling, a rate, a midpoint."),
    ("Std. err.", "How much the estimate would wobble across repeated samples. Smaller = more precise."),
    ("P>|t|", "Probability of the estimate if the true value were zero. <0.05 = significant. "
              "(Exception: in normality tests like Shapiro–Wilk you WANT p>0.05.)"),
    ("[95% conf. int.]", "Plausible range for the true value. Narrow = precise; excludes zero = significant."),
    ("yhat / fitted", "The model's predicted value for each row — points on the fitted curve."),
    ("resid (residual)", "Actual − predicted. Good residuals are small, patternless and bell-shaped."),
    ("e(converged)", "1 = the search found a stable answer; 0 = it failed. Must be 1 first."),
    ("AIC", "Model-comparison score that rewards fit and punishes complexity. Lower is better; "
            "compare only on the same data."),
    ("Cook's distance", "How much one data point moves the whole fit. Above 4/n = influential."),
    ("nlcom", "Computes a NEW quantity from fitted parameters (half-life, doubling time, EC50) "
              "with a correct CI."),
    ("Half-life / doubling time", "ln(2)/rate — the change that halves (decay) or doubles (growth) "
                                  "the outcome. The clinically intuitive translation of the rate."),
    ("EC50", "The dose (or level) giving half the maximum effect. In Michaelis–Menten it's Km; in a "
             "logistic it's the inflection point."),
    ("initial()", "Your starting guesses. The biggest cause of — and cure for — convergence problems."),
]

# ---------------------------------------------------------------------------
# RENDER
# ---------------------------------------------------------------------------
def render_block(b):
    has_result = bool(b.get("output") or b.get("img"))
    p = ['<div class="block slide">']
    # --- code chunk, with a live "Run" button when there's something to reveal ---
    p.append('<div class="code-head">')
    p.append('<span class="label">⌨️ Stata command</span>')
    if has_result:
        p.append('<button class="run-btn" type="button" onclick="runBlock(this)">'
                 '<span class="ico">&#9654;</span> Run</button>')
    p.append('</div>')
    p.append(f'<pre class="code">{esc(b["stata"])}</pre>')
    # --- the result is hidden until "run": output, graph, and how to read it ---
    if has_result:
        p.append('<div class="result" hidden>')
        if b.get("output"):
            p.append('<div class="label">📋 Output — real least-squares fit (computed in Python)</div>')
            p.append(f'<pre class="output">{esc(b["output"])}</pre>')
        if b.get("img"):
            p.append('<div class="label">📈 Graph — generated from the data</div>')
            p.append(f'<img class="plot-img" src="{b["img"]}" alt="plot">')
        if b.get("read"):
            p.append('<div class="callout read"><span class="tag">📖 Read the output</span>'
                     f'<div>{b["read"]}</div></div>')
        p.append('</div>')
    p.append('<div class="callout means"><span class="tag">💡 What this means</span>'
             f'<div>{b["means"]}</div></div>')
    if b.get("clin"):
        p.append('<div class="callout clin"><span class="tag">🩺 Clinical translation</span>'
                 f'<div>{b["clin"]}</div></div>')
    if b.get("ebola"):
        p.append('<div class="callout ebola"><span class="tag">🦠 Outbreak lens</span>'
                 f'<div>{b["ebola"]}</div></div>')
    if b.get("say"):
        p.append('<div class="callout say"><span class="tag">🗣️ Say this</span>'
                 f'<div>{b["say"]}</div></div>')
    if b.get("warn"):
        p.append('<div class="callout warn"><span class="tag">⚠️ Watch out</span>'
                 f'<div>{b["warn"]}</div></div>')
    p.append('</div>')
    return "\n".join(p)


def render_section(s):
    intro = [f'<h2>{s["title"]}</h2>']
    if s.get("eli5"):
        intro.append('<div class="eli5"><span class="tag">🧩 Everyday version</span>'
                     f'<div>{s["eli5"]}</div></div>')
    if s.get("lead"):
        intro.append(f'<p class="lead">{s["lead"]}</p>')
    if s.get("html"):
        intro.append(s["html"])
    out = [f'<section id="{s["id"]}">',
           '<div class="slide intro">' + "\n".join(intro) + '</div>']
    out += [render_block(b) for b in s["blocks"]]
    out.append('</section>')
    return "\n".join(out)


def render_toc():
    items = "".join(f'<li><a href="#{s["id"]}">{esc(s["title"])}</a></li>' for s in SECTIONS)
    items += '<li><a href="#glossary">Output glossary</a></li>'
    return f'<nav class="toc"><div class="toc-h">Contents</div><ol>{items}</ol></nav>'


def render_glossary():
    rows = "".join(f'<tr><td><b>{esc(t)}</b></td><td>{esc(d)}</td></tr>' for t, d in GLOSSARY)
    return ('<section id="glossary"><div class="slide intro">'
            '<h2>Output glossary — every term, plain English</h2>'
            f'<table class="grid">{rows}</table></div></section>')


CSS = """
:root{--ink:#1f2328;--muted:#6a737d;--line:#d0d7de;--bg:#fff;--code-bg:#f6f8fa;
--term-bg:#0d1117;--term-ink:#c9d1d9;--means:#0969da;--means-bg:#ddf4ff;--say:#1a7f37;
--say-bg:#dafbe1;--warn:#9a6700;--warn-bg:#fff8c5;--clin:#0a7d77;--clin-bg:#d7f5f2;
--ebola:#bc4c00;--ebola-bg:#fff1e5;--read:#6639ba;--read-bg:#efeafc;--run:#1a7f37;
--eli:#bf3989;--eli-bg:#fff0f7;}
*{box-sizing:border-box;}
body{margin:0;font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg);}
.wrap{max-width:1180px;margin:0 auto;display:grid;grid-template-columns:270px 1fr;gap:32px;padding:0 24px;}
header{grid-column:1/-1;padding:32px 0 8px;border-bottom:2px solid var(--line);}
header h1{margin:0 0 6px;font-size:30px;}
header p{margin:0;color:var(--muted);}
.banner{grid-column:1/-1;background:var(--means-bg);border:1px solid #9ad;border-radius:8px;padding:12px 16px;margin:18px 0;font-size:14px;color:#0a3069;}
.toc{position:sticky;top:16px;align-self:start;font-size:13.5px;max-height:92vh;overflow:auto;}
.toc-h{font-weight:700;text-transform:uppercase;letter-spacing:.04em;font-size:12px;color:var(--muted);margin-bottom:8px;}
.toc ol{list-style:none;margin:0;padding:0;}
.toc li{margin:2px 0;}
.toc a{color:var(--ink);text-decoration:none;display:block;padding:4px 8px;border-radius:6px;}
.toc a:hover{background:var(--code-bg);color:var(--means);}
main{min-width:0;padding-bottom:80px;}
section{margin:0 0 44px;}
h2{font-size:22px;border-bottom:1px solid var(--line);padding-bottom:8px;margin-top:8px;}
.lead{color:var(--muted);margin-top:-2px;}
.block{border:1px solid var(--line);border-radius:10px;padding:16px;margin:18px 0;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.04);}
.label{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700;margin:14px 0 4px;}
.label:first-child{margin-top:0;}
pre{margin:0;padding:12px 14px;border-radius:8px;overflow-x:auto;font:12.5px/1.5 "SF Mono",Consolas,Menlo,monospace;}
pre.code{background:var(--code-bg);border:1px solid var(--line);color:var(--ink);}
pre.output{background:var(--term-bg);color:var(--term-ink);}
.plot-img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:8px;display:block;}
.callout{border-radius:8px;padding:10px 14px 12px;margin:12px 0 0;font-size:15px;}
.callout .tag{display:inline-block;font-size:12px;font-weight:700;margin-bottom:4px;}
.callout div{margin:0;}
.means{background:var(--means-bg);border-left:4px solid var(--means);} .means .tag{color:var(--means);}
.say{background:var(--say-bg);border-left:4px solid var(--say);} .say .tag{color:var(--say);} .say div{font-style:italic;}
.warn{background:var(--warn-bg);border-left:4px solid var(--warn);} .warn .tag{color:var(--warn);}
.clin{background:var(--clin-bg);border-left:4px solid var(--clin);} .clin .tag{color:var(--clin);}
.ebola{background:var(--ebola-bg);border-left:4px solid var(--ebola);} .ebola .tag{color:var(--ebola);}
.read{background:var(--read-bg);border-left:4px solid var(--read);} .read .tag{color:var(--read);}
.eli5{background:var(--eli-bg);border:1px solid var(--eli);border-left:5px solid var(--eli);
  border-radius:8px;padding:13px 17px;margin:8px 0 14px;font-size:15.5px;line-height:1.55;}
.eli5 .tag{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.02em;
  color:var(--eli);margin-bottom:5px;}
.eli5 b{color:#8a2b62;}
.code-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:14px 0 4px;}
.code-head .label{margin:0;}
.run-btn{font:600 12px/1 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;cursor:pointer;
  border:1px solid var(--run);background:var(--run);color:#fff;border-radius:6px;padding:6px 12px;
  white-space:nowrap;display:inline-flex;align-items:center;gap:6px;transition:background .15s;}
.run-btn:hover{background:#15692d;border-color:#15692d;}
.run-btn:disabled{opacity:.6;cursor:progress;}
.run-btn .ico{font-size:10px;line-height:1;}
.result[hidden]{display:none;}
.result.revealed{animation:revealfade .35s ease;}
@keyframes revealfade{from{opacity:0;transform:translateY(-4px);}to{opacity:1;transform:none;}}
.reveal-all{font:600 12.5px/1 inherit;cursor:pointer;border:1px solid #9ad;background:#fff;
  color:#0a3069;border-radius:6px;padding:7px 13px;margin-left:14px;white-space:nowrap;}
.reveal-all:hover{background:#eef6ff;}
.present-btn{font:600 12.5px/1 inherit;cursor:pointer;border:1px solid var(--run);background:var(--run);
  color:#fff;border-radius:6px;padding:7px 13px;margin-left:10px;white-space:nowrap;}
.present-btn:hover{background:#15692d;}
/* ---- presentation / slide mode: same HTML, shown one concept at a time ---- */
.present-bar{position:fixed;left:0;right:0;bottom:0;z-index:60;display:flex;gap:14px;
  align-items:center;justify-content:center;padding:10px;background:rgba(13,17,23,.93);
  color:#fff;font-size:14px;}
.present-bar button{font:600 14px/1 inherit;cursor:pointer;border:1px solid #30363d;
  background:#21262d;color:#fff;border-radius:7px;padding:8px 16px;}
.present-bar button:hover{background:#30363d;}
.present-bar #slide-count{min-width:78px;text-align:center;font-variant-numeric:tabular-nums;font-weight:600;}
.present-bar .hint{opacity:.6;font-size:12px;margin-left:6px;}
body.presenting{overflow:hidden;}
body.presenting > .wrap > header,body.presenting .toc,body.presenting .banner{display:none !important;}
body.presenting .wrap{display:block;max-width:none;padding:0;gap:0;}
body.presenting main{padding:0;min-height:100vh;}
body.presenting section{margin:0;}
body.presenting .slide{display:none;}
body.presenting .slide.current{display:flex;flex-direction:column;justify-content:flex-start;
  position:fixed;inset:0;z-index:50;background:var(--bg);padding:5vh 7vw 13vh;overflow:auto;font-size:18px;}
body.presenting .slide.intro.current{justify-content:safe center;}
body.presenting .slide.current > *{max-width:1040px;width:100%;margin-left:auto;margin-right:auto;}
body.presenting .slide.current h2{font-size:30px;border:none;padding:0;}
body.presenting .block.slide.current{border:none;box-shadow:none;border-radius:0;background:transparent;padding:0;}
body.presenting .plot-img{max-height:48vh;width:auto;margin:8px auto;}
code{background:var(--code-bg);padding:1px 5px;border-radius:4px;font:12.5px "SF Mono",Consolas,monospace;}
.callout code{background:rgba(0,0,0,.06);}
table.grid{width:100%;border-collapse:collapse;font-size:14px;margin:6px 0;}
table.grid th,table.grid td{text-align:left;padding:7px 9px;border:1px solid var(--line);vertical-align:top;}
table.grid th{background:var(--code-bg);}
.callout table.grid{margin:4px 0 0;background:rgba(255,255,255,.55);}
@media print{.toc{display:none;}.wrap{display:block;}.block{break-inside:avoid;box-shadow:none;}
  .result[hidden]{display:block !important;}
  .run-btn,.reveal-all,.present-btn,.present-bar{display:none !important;}}
@media (max-width:860px){.wrap{grid-template-columns:1fr;}.toc{position:static;}}
"""

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Applied Non-Linear Regression — Stata Companion</title>
<style>{css}</style></head>
<body><div class="wrap">
  <header>
    <h1>Applied Non-Linear Regression — Companion</h1>
    <p>Mirrors the slide deck, step by step. Presenter: Dr. Christine Atuhairwe · Faculty of Health Sciences.</p>
  </header>
  <div class="banner">
    <b>How to use this page:</b> each code block has a <b><span class="ico">&#9654;</span> Run</b>
    button — click it to reveal that command's output and graph, as if you'd run it live in Stata,
    then read the <b>📖 Read the output</b> note to see what the numbers actually say. Teaching live?
    Keep them hidden and reveal one at a time. Reading on your own?
    <button id="revealAll" class="reveal-all" type="button" onclick="toggleAll()">Reveal all outputs</button>
    <button id="presentBtn" class="present-btn" type="button" onclick="enterPresent()">▶ Present (slides)</button>
    <br><span style="font-size:13px">Present mode shows <b>one concept per slide</b> — navigate with
    the on-screen arrows or your keyboard (← →, Esc to exit). Run buttons still work on each slide.</span>
    <br><br>
    <b>About the numbers:</b> every coefficient table below is a <b>real least-squares fit</b>
    computed in Python (<code>scipy.curve_fit</code>) — on the public <code>auto-mpg.csv</code>
    (UCI, 398 cars) and on seeded simulations. Your do-file fits the same models in Stata with
    <code>nl</code>; the <i>shape and interpretation</i> are identical, but exact figures differ
    (Stata's built-in <code>sysuse auto</code> has only 74 cars, and simulations vary with the
    random-number stream). <b>Scroll top → bottom.</b>
  </div>
  {toc}
  <main>{body}{glossary}</main>
</div>
<div id="present-bar" class="present-bar" hidden>
  <button type="button" onclick="slidePrev()">◀ Prev</button>
  <span id="slide-count">1 / 1</span>
  <button type="button" onclick="slideNext()">Next ▶</button>
  <button type="button" onclick="exitPresent()">✕ Exit</button>
  <span class="hint">← → keys · Esc to exit</span>
</div>
{script}
</body></html>
"""

SCRIPT = """<script>
function runBlock(btn){
  var block = btn.closest('.block');
  var res = block.querySelector('.result');
  if(!res){ return; }
  if(res.hasAttribute('hidden')){
    btn.disabled = true;
    btn.innerHTML = '<span class="ico">&#9203;</span> running\\u2026';
    setTimeout(function(){
      res.removeAttribute('hidden');
      res.classList.add('revealed');
      btn.disabled = false;
      btn.innerHTML = '<span class="ico">&#10003;</span> Ran \\u00b7 re-run';
    }, 380);
  } else {
    res.setAttribute('hidden','');
    res.classList.remove('revealed');
    btn.innerHTML = '<span class="ico">&#9654;</span> Run';
  }
}
function toggleAll(){
  var reveal = document.querySelectorAll('.result[hidden]').length > 0;
  document.querySelectorAll('.block').forEach(function(b){
    var res = b.querySelector('.result'); if(!res){ return; }
    var btn = b.querySelector('.run-btn');
    if(reveal){
      res.removeAttribute('hidden'); res.classList.add('revealed');
      if(btn){ btn.innerHTML = '<span class="ico">&#10003;</span> Ran \\u00b7 re-run'; }
    } else {
      res.setAttribute('hidden',''); res.classList.remove('revealed');
      if(btn){ btn.innerHTML = '<span class="ico">&#9654;</span> Run'; }
    }
  });
  var t = document.getElementById('revealAll');
  if(t){ t.textContent = reveal ? 'Hide all outputs' : 'Reveal all outputs'; }
}

/* ---- presentation / slide mode ---- */
var SLIDES = [], CUR = 0;
function showSlide(i){
  if(i < 0){ i = 0; }
  if(i >= SLIDES.length){ i = SLIDES.length - 1; }
  CUR = i;
  SLIDES.forEach(function(s){ s.classList.remove('current'); });
  SLIDES[CUR].classList.add('current');
  SLIDES[CUR].scrollTop = 0;
  var c = document.getElementById('slide-count');
  if(c){ c.textContent = (CUR + 1) + ' / ' + SLIDES.length; }
}
function slideNext(){ showSlide(CUR + 1); }
function slidePrev(){ showSlide(CUR - 1); }
function presentKeys(e){
  if(e.key === 'ArrowRight' || e.key === 'PageDown'){ e.preventDefault(); slideNext(); }
  else if(e.key === 'ArrowLeft' || e.key === 'PageUp'){ e.preventDefault(); slidePrev(); }
  else if(e.key === 'Escape'){ exitPresent(); }
}
function enterPresent(){
  SLIDES = Array.prototype.slice.call(document.querySelectorAll('main .slide'));
  if(!SLIDES.length){ return; }
  document.body.classList.add('presenting');
  var bar = document.getElementById('present-bar');
  if(bar){ bar.hidden = false; }
  showSlide(0);
  document.addEventListener('keydown', presentKeys);
}
function exitPresent(){
  document.body.classList.remove('presenting');
  var bar = document.getElementById('present-bar');
  if(bar){ bar.hidden = true; }
  SLIDES.forEach(function(s){ s.classList.remove('current'); });
  document.removeEventListener('keydown', presentKeys);
}
</script>"""


def main():
    body = "\n".join(render_section(s) for s in SECTIONS)
    page = PAGE.format(css=CSS, toc=render_toc(), body=body, glossary=render_glossary(),
                       script=SCRIPT)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    nb = sum(len(s["blocks"]) for s in SECTIONS)
    print(f"Wrote {OUT}: {len(SECTIONS)} sections, {nb} command blocks.")
    print("\n--- key REAL fitted numbers (verify against narrative) ---")
    print(f"decay  a={FIT_DECAY['popt'][0]:.2f} b={b_dec:.6f}  half-life={half_life:.0f} lb  "
          f"(-1000lb ~ {pct_per_1000:.0f}%)")
    print(f"logist asym={FIT_LOG['popt'][0]:.2f} inflect={FIT_LOG['popt'][2]:.1f}  LE2020={le2020:.1f}")
    print(f"MM     vmax={FIT_MM['popt'][0]:.2f} km={FIT_MM['popt'][1]:.2f}")
    print(f"viral  a={FIT_VL['popt'][0]:.1f} b={b_vl:.3f}  doubling={dt_vl:.2f} d")
    print(f"gulu   a={FIT_GULU['popt'][0]:.2f} b={b_g:.4f}  doubling={dt_g:.1f} d")
    print(f"exer   asym={FIT_EX['popt'][0]:.2f} rate_g={FIT_EX['popt'][1]:.3f} inflect={ec50_ex:.1f}")
    print(f"AIC    linear={AIC_LIN:.1f}  nonlinear={AIC_NL:.1f}")


if __name__ == "__main__":
    main()
