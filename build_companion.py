#!/usr/bin/env python3
"""
Build a self-contained HTML companion / cheat-sheet for the
Non-Linear Regression (Stata) lecture.

For every step it shows:
  - the Stata command you type
  - a REPRESENTATIVE output (what the table looks like; exact numbers
    vary by Stata version / RNG)
  - a plain-English "what this means" explanation
  - a "say this out loud" presenter cue

Run:  python3 build_companion.py
Out:  nonlinear_regression_companion.html  (open in any browser)
"""

import html

OUT = "nonlinear_regression_companion.html"

# ---------------------------------------------------------------------------
# CONTENT
# Each block is a dict:
#   code    : the Stata you type (required)
#   output  : representative Stata output, or None if the command only draws a plot
#   plot    : short description of the graph it produces (optional)
#   means   : "what this output / command means" (HTML allowed)
#   say     : optional "say this out loud" presenter line
#   warn    : optional pitfall / watch-out
# ---------------------------------------------------------------------------

SECTIONS = [
    {
        "id": "intro",
        "title": "Before you start — the 4-step rhythm",
        "lead": "Every non-linear fit in this lecture follows the same four beats. "
                "If you can narrate these four, you can narrate the whole deck.",
        "blocks": [
            {
                "code": "* 1. LOOK   plot the raw data first\n"
                        "* 2. GUESS  read starting values off the plot\n"
                        "* 3. FIT    nl (y = ...), initial(...)\n"
                        "* 4. CHECK  did it converge? are residuals clean?",
                "output": None,
                "means": "Linear regression lets you skip straight to the fit. Non-linear "
                         "regression does <b>not</b>: the computer searches for the parameters "
                         "by trial-and-improvement, starting from <i>your</i> initial guess. A "
                         "bad guess means it may never find the answer. So we always "
                         "<b>plot first, guess sensibly, fit, then check</b>.",
                "say": "Non-linear models aren't solved with a formula — they're found by "
                       "searching. Our job is to give the search a good place to start and "
                       "to check where it ended up.",
            },
        ],
    },
    {
        "id": "model1",
        "title": "Model 1 — Exponential decay",
        "lead": "Dataset: Stata's built-in <code>auto</code>. Clinical analogy: a drug "
                "concentration falling as body mass rises — fast at first, then flattening.",
        "blocks": [
            {
                "code": "sysuse auto, clear\n"
                        "describe\n"
                        "list mpg weight in 1/5",
                "output": "Contains data from ...\\auto.dta\n"
                          " Observations:           74          1978 automobile data\n"
                          "    Variables:           12\n"
                          "------------------------------------------------------------\n"
                          "     +---------------------+\n"
                          "     | mpg   weight        |\n"
                          "  1. |  22    2,930        |\n"
                          "  2. |  17    3,350        |\n"
                          "  3. |  22    2,640        |\n"
                          "  4. |  20    3,250        |\n"
                          "  5. |  15    4,080        |\n"
                          "     +---------------------+",
                "means": "<code>sysuse auto, clear</code> loads the demo dataset (the "
                         "<code>clear</code> discards anything already in memory). "
                         "<code>describe</code> lists the variables and how many rows. "
                         "<code>list … in 1/5</code> prints the first 5 rows so you can "
                         "eyeball the numbers. Here <b>mpg</b> is the outcome (stand-in for "
                         "drug concentration) and <b>weight</b> the predictor (body mass).",
                "say": "We borrow the cars dataset as a pharmacokinetics stand-in: mileage "
                       "behaves like drug concentration, weight like body mass.",
            },
            {
                "code": 'twoway scatter mpg weight, ///\n'
                        '    title("MPG vs Vehicle Weight") ///\n'
                        '    xtitle("Weight (lbs)") ytitle("Miles per Gallon")',
                "output": None,
                "plot": "A scatter of points sloping down and curving — high MPG for light "
                        "cars, dropping steeply then levelling off for heavy ones.",
                "means": "Always plot before fitting. The <b>curved, decaying</b> shape is the "
                         "evidence that a straight line is wrong and an exponential decay curve "
                         "is right. The <code>///</code> just continues one long command onto "
                         "the next line.",
                "say": "See the curve? A straight line would under-predict the light cars and "
                       "over-predict the heavy ones. That curve is why we go non-linear.",
            },
            {
                "code": "nl (mpg = {a} * exp({b} * weight)), ///\n"
                        "    initial(a 40 b -0.0005)",
                "output": "      mpg | Coefficient  Std. err.    t    P>|t|   [95% conf. int.]\n"
                          "----------+------------------------------------------------------\n"
                          "       /a |   41.23456     2.34500  17.58  0.000   36.567   45.902\n"
                          "       /b |   -0.000478    0.00007  -6.83  0.000  -0.00062 -0.00034",
                "means": "<code>nl</code> fits a <b>n</b>on-<b>l</b>inear model. The "
                         "<code>{a}</code> and <code>{b}</code> in curly braces are the unknowns "
                         "Stata estimates. <code>initial(a 40 b -0.0005)</code> is your starting "
                         "guess, read off the plot (ceiling ≈ 40 MPG, gentle decay). "
                         "Reading the table: <b>/a ≈ 41</b> is the ceiling (MPG at zero weight); "
                         "<b>/b ≈ −0.00048</b> is the decay rate — negative, so MPG falls as "
                         "weight rises. Both <b>P&gt;|t| = 0.000</b>, so both are clearly real, "
                         "not chance.",
                "say": "a is the starting height, b is how fast it falls. b is negative — that's "
                       "decay. Tiny p-values mean we're confident both numbers are real.",
                "warn": "If Stata prints “convergence not achieved” the numbers are meaningless — "
                        "fix your <code>initial()</code> guesses and refit.",
            },
            {
                "code": "nl (mpg = {a} * exp({b} * weight)), ///\n"
                        "    initial(a 40 b -0.0005) vce(robust)",
                "output": None,
                "means": "Same model, but <code>vce(robust)</code> swaps in <b>robust standard "
                         "errors</b>. The coefficients (/a, /b) don't change — only the Std. err., "
                         "t and CI columns do. Use it when the residual spread isn't constant "
                         "(common with decay/growth data). The conclusions usually hold; the "
                         "uncertainty is just reported more honestly.",
                "say": "Robust standard errors don't move the estimates — they make the error "
                       "bars trustworthy when the scatter isn't even.",
            },
            {
                "code": "predict fitted_exp, yhat\n"
                        "predict resid_exp, resid\n"
                        "rvfplot, yline(0)\n"
                        "qnorm resid_exp\n"
                        "histogram resid_exp, normal",
                "output": None,
                "plot": "(1) residuals vs fitted — should be a shapeless cloud around the zero "
                        "line; (2) Q-Q plot — points should hug the diagonal; (3) histogram — "
                        "should look roughly bell-shaped.",
                "means": "<code>predict … yhat</code> saves the curve's predictions; "
                         "<code>predict … resid</code> saves the residuals (actual − predicted). "
                         "The three plots are the standard health-check: <b>no pattern</b> in "
                         "residuals-vs-fitted, points <b>on the line</b> in the Q-Q plot, and a "
                         "<b>bell shape</b> in the histogram all say the model fits well.",
                "say": "Residuals are what the model couldn't explain. If they're patternless and "
                       "bell-shaped, the model has squeezed out all the signal.",
                "warn": "A funnel or U-shape in residuals-vs-fitted means the model shape is "
                        "wrong — not just noisy.",
            },
            {
                "code": "nlcom (half_life: ln(2) / -_b[/b])",
                "output": "  half_life |   1450.2     177.4    8.17  0.000   1102.5   1797.9",
                "means": "<code>nlcom</code> computes a <b>new quantity</b> from the fitted "
                         "parameters and gives it a correct confidence interval. Here "
                         "<b>half-life = ln(2) / −b ≈ 1450 lbs</b>: every extra ~1450 lbs of "
                         "weight halves the MPG — exactly like a drug's half-life. "
                         "<code>_b[/b]</code> means “the estimated value of parameter b.”",
                "say": "This is the clinically intuitive number: how much change halves the "
                       "outcome. Same maths as drug half-life.",
            },
        ],
    },
    {
        "id": "model2",
        "title": "Model 2 — Logistic growth (S-curve)",
        "lead": "Dataset: Stata's <code>uslifeexp</code> (life expectancy 1900–2000). Clinical "
                "analogy: tumour growth, CD4 recovery, cognitive decline — slow, then fast, then "
                "a ceiling.",
        "blocks": [
            {
                "code": "sysuse uslifeexp, clear\n"
                        "list year le in 1/10",
                "output": "     +-------------+\n"
                          "     | year   le   |\n"
                          "  1. | 1900  47.3  |\n"
                          "  2. | 1901  49.1  |\n"
                          "  3. | 1902  51.5  |\n"
                          "      ...\n"
                          " 10. | 1909  52.1  |",
                "means": "New dataset. <b>year</b> is the predictor, <b>le</b> (life expectancy "
                         "in years) is the outcome. We just load and peek at it. The values rise "
                         "over time in an S-shape.",
                "say": "Life expectancy over the 20th century: it climbs, accelerates, then "
                       "levels off — the classic S-curve.",
            },
            {
                "code": 'twoway scatter le year, ///\n'
                        '    title("US Life Expectancy Over Time")',
                "output": None,
                "plot": "An S-shaped rising cloud: slow gains early, steep rise mid-century, "
                        "flattening near the end.",
                "means": "The <b>S-shape</b> (slow → fast → plateau) is the fingerprint of "
                         "logistic growth. That's what tells us to fit a logistic curve rather "
                         "than a line or a plain exponential.",
                "say": "Three phases — lag, surge, ceiling. Whenever you see that, think "
                       "logistic.",
            },
            {
                "code": "nl (le = {asym} / (1 + exp({rate} * (year - {inflect})))), ///\n"
                        "    initial(asym 80 rate -0.1 inflect 1950)\n"
                        "estimates store logistic_model",
                "output": "       le | Coefficient  Std. err.    t    P>|t|   [95% conf. int.]\n"
                          "----------+------------------------------------------------------\n"
                          "    /asym |   79.234      1.234    64.21  0.000   76.745   81.723\n"
                          "    /rate |   -0.095      0.011    -8.64  0.000   -0.117   -0.073\n"
                          " /inflect | 1958.45       2.101   931.78  0.000 1954.222 1962.678",
                "means": "Three meaningful parameters: <b>/asym ≈ 79</b> is the ceiling (max life "
                         "expectancy the curve approaches); <b>/inflect ≈ 1958</b> is the year of "
                         "fastest growth (the middle of the S); <b>/rate</b> sets the steepness. "
                         "Tiny p-values + tight CIs = all three precisely estimated. "
                         "<code>estimates store</code> saves the fit so we can compare models "
                         "later.",
                "say": "Asym is the ceiling, inflect is the tipping-point year, rate is how "
                       "steep the climb is. All three are sharply estimated.",
            },
            {
                "code": "predict fitted_log, yhat\n"
                        "local asym = _b[/asym]\n"
                        "local rate = _b[/rate]\n"
                        "local inflect = _b[/inflect]\n"
                        'display "Predicted LE 2020: " `asym\'/(1+exp(`rate\'*(2020-`inflect\')))',
                "output": "Predicted LE 2020: 79.06",
                "means": "We pull each estimated parameter into a <code>local</code> (a named "
                         "value) and plug them into the logistic formula for year 2020 to "
                         "<b>forecast</b>. Result ≈ 79 years — close to the ceiling, because by "
                         "2020 the curve has nearly flattened.",
                "say": "Once we have the parameters we can read the curve at any year — here, a "
                       "2020 forecast of about 79 years.",
                "warn": "Forecasting far past your data is risky: the model assumes the same "
                        "S-curve keeps holding.",
            },
        ],
    },
    {
        "id": "model3",
        "title": "Model 3 — Michaelis–Menten (saturating dose–response)",
        "lead": "Simulated dose–response data (we set the true answer, so we can check the fit). "
                "Clinical analogy: receptor binding — response rises with dose then saturates.",
        "blocks": [
            {
                "code": "clear\n"
                        "set seed 12345\n"
                        "set obs 40\n"
                        "gen dose = (_n - 1) * (100 / 39)\n"
                        "gen response = (90 * dose) / (25 + dose) + rnormal(0, 4)",
                "output": None,
                "means": "We <b>simulate</b> a study so we know the truth. <code>set seed</code> "
                         "makes it reproducible; <code>set obs 40</code> creates 40 rows; "
                         "<code>dose</code> runs 0→100 mg/kg. The true curve has <b>Vmax = 90</b> "
                         "(max response) and <b>Km = 25</b> (the EC50), plus random noise "
                         "<code>rnormal(0,4)</code>. The fit below should recover ~90 and ~25.",
                "say": "We built this data ourselves with Vmax 90 and EC50 25 — so we can grade "
                       "the model on whether it finds those numbers back.",
            },
            {
                "code": "nl (response = {vmax} * dose / ({km} + dose)), ///\n"
                        "    initial(vmax 90 km 25)",
                "output": " response | Coefficient  Std. err.    t    P>|t|   [95% conf. int.]\n"
                          "----------+------------------------------------------------------\n"
                          "    /vmax |   89.456      2.345    38.15  0.000   84.712   94.200\n"
                          "      /km |   24.876      2.123    11.72  0.000   20.578   29.174",
                "means": "<b>/vmax ≈ 89</b> is the saturating maximum response. <b>/km ≈ 25</b> "
                         "is the EC50 — the dose that produces <b>half</b> of Vmax. Both land "
                         "right on the true values (90 and 25), so the model works. In pharmacology "
                         "Km/EC50 is the key potency number.",
                "say": "Vmax is the most the drug can do; Km is the dose that gets you halfway "
                       "there — the potency. We recovered both almost exactly.",
            },
            {
                "code": "predict cooksd_mm, cooksd\n"
                        "scatter cooksd_mm _n, yline(4/40)",
                "output": None,
                "plot": "A spike plot of Cook's distance per observation, with a horizontal "
                        "cut-off line at 4/40 = 0.1. Bars above the line are influential points.",
                "means": "<b>Cook's distance</b> measures how much one single data point pulls the "
                         "whole fit. The common cut-off is <b>4/n</b> (here 4/40 = 0.1). Points "
                         "above the line deserve a second look — a data-entry error, or a genuinely "
                         "unusual patient.",
                "say": "Cook's distance asks: would the curve move a lot if I deleted this one "
                       "point? Anything above the line, we investigate.",
            },
        ],
    },
    {
        "id": "model4",
        "title": "Model 4 — Exponential growth (viral load)",
        "lead": "Simulated viral load climbing after infection. Clinical analogy: early viral "
                "replication or untreated tumour growth.",
        "blocks": [
            {
                "code": "clear\n"
                        "set seed 67890\n"
                        "set obs 20\n"
                        "gen day = _n\n"
                        "gen viral_load = 100 * exp(0.3 * day) + rnormal(0, 200)",
                "output": None,
                "means": "Same simulate-from-known-truth recipe. True start <b>a = 100</b>, true "
                         "growth rate <b>b = 0.3</b> per day. Note <code>+exp(+0.3·day)</code> — "
                         "a <b>positive</b> exponent means growth (Model 1 had a negative one for "
                         "decay).",
                "say": "Same exponential family as Model 1, but the exponent is positive now — "
                       "so instead of decay we get explosive growth.",
            },
            {
                "code": "nl (viral_load = {a} * exp({b} * day)), ///\n"
                        "    initial(a 100 b 0.3)",
                "output": "viral_load| Coefficient  Std. err.    t    P>|t|   [95% conf. int.]\n"
                          "----------+------------------------------------------------------\n"
                          "       /a |   98.456     12.34      7.98  0.000   73.456  123.456\n"
                          "       /b |   0.312       0.045     6.93  0.000    0.218    0.406",
                "means": "<b>/a ≈ 98</b> recovers the starting load (~100); <b>/b ≈ 0.31</b> the "
                         "daily growth rate (~0.3). Both close to the truth.",
                "say": "Starting load about 100, growing ~31% a day — right where we built it.",
            },
            {
                "code": "nlcom (doubling_time: ln(2) / _b[/b])",
                "output": " doubling_~e |   2.221     0.320    6.94  0.000    1.594    2.848",
                "means": "The mirror image of half-life. <b>Doubling time = ln(2) / b ≈ 2.2 days</b>: "
                         "the viral load doubles roughly every 2 days. This is the clinically "
                         "meaningful translation of the raw rate <i>b</i>.",
                "say": "A growth rate of 0.31 is abstract; “doubles every two days” is what a "
                       "clinician actually feels.",
            },
        ],
    },
    {
        "id": "compare",
        "title": "Linear vs non-linear — which wins?",
        "lead": "Fit both to the same data and let the numbers decide.",
        "blocks": [
            {
                "code": "regress mpg weight\n"
                        "estimates store linear_model\n"
                        "nl (mpg = {a} * exp({b} * weight)), initial(a 40 b -0.0005)\n"
                        "estimates store nl_model\n"
                        "estimates stats linear_model nl_model",
                "output": "    Model |     N    ll(null)  ll(model)   df      AIC       BIC\n"
                          "----------+--------------------------------------------------\n"
                          "  linear  |    74      .        -195.0      2     394.0     398.6\n"
                          "  nl      |    74      .        -189.7      2     383.4     388.0",
                "means": "<b>AIC</b> and <b>BIC</b> score model fit while penalising complexity — "
                         "<b>lower is better</b>. Here the non-linear model has lower AIC and BIC "
                         "(383/388 vs 394/399), so it fits the curved data better. The gap is "
                         "modest, so interpretability also matters in the choice.",
                "say": "Lower AIC/BIC wins. The exponential curve beats the straight line here — "
                       "and it's also the more interpretable story.",
                "warn": "Only compare AIC/BIC for models fit to the <b>same outcome on the same "
                        "rows</b>. Don't compare across different datasets.",
            },
        ],
    },
    {
        "id": "diagnostics",
        "title": "Diagnostic checklist — run after EVERY fit",
        "lead": "Six quick checks. The first one is non-negotiable.",
        "blocks": [
            {
                "code": "di e(converged)",
                "output": "1",
                "means": "<code>e(converged)</code> is 1 if the search succeeded, 0 if it gave up. "
                         "<b>If this isn't 1, stop</b> — every other number is unreliable. This is "
                         "the single most important line in the whole lecture.",
                "say": "First question, always: did it converge? One means yes. Zero means throw "
                       "the results away and fix your starting values.",
            },
            {
                "code": "swilk resid",
                "output": "    Variable |   Obs    W      V      z     Prob>z\n"
                          "  -----------+----------------------------------\n"
                          "       resid |    74  0.981  1.23  0.46  0.3210",
                "means": "<b>Shapiro–Wilk</b> formally tests whether residuals are normal. The "
                         "rule: <b>Prob&gt;z (the p-value) &gt; 0.05 ⇒ normal enough</b>. Here "
                         "0.32 &gt; 0.05, so residuals pass. (Counter-intuitively, here a "
                         "<i>big</i> p-value is the good result.)",
                "say": "Shapiro–Wilk: above 0.05 means the residuals are acceptably normal. Big "
                       "p-value is good news this time.",
            },
            {
                "code": "predict cooksd, cooksd\n"
                        "summarize cooksd, detail",
                "output": None,
                "means": "Re-checks for influential points (see Model 3). <code>summarize … detail</code> "
                         "shows the spread; watch the max — anything well above 4/n is worth "
                         "investigating.",
                "say": "One more pass for points that punch above their weight.",
            },
            {
                "code": "nl (y = {a} * exp({b} * x)), initial(a 10 b -0.1) level(95)",
                "output": None,
                "means": "<code>level(95)</code> requests 95% confidence intervals. For small "
                         "samples the profile-likelihood CIs Stata can produce are more honest "
                         "than the default symmetric ones. Also sanity-check: do the estimates "
                         "make <b>clinical</b> sense?",
                "say": "Last check is human, not statistical: do these numbers make sense for a "
                       "real patient?",
            },
        ],
    },
    {
        "id": "debug",
        "title": "When it won't converge",
        "lead": "The most common failure in non-linear regression — and the fixes.",
        "blocks": [
            {
                "code": "nl (y = {a} * exp({b} * x)), initial(a 40 b -0.0005) trace",
                "output": "Iteration 0:  residual SS = 1.23e+04\n"
                          "Iteration 1:  residual SS = 8.91e+03\n"
                          "Iteration 2:  residual SS = 8.40e+03\n"
                          "...",
                "means": "<code>trace</code> prints the residual sum-of-squares at each step of "
                         "the search. If it keeps falling and settles, good. If it bounces or "
                         "explodes, your starting values are sending the search the wrong way.",
                "say": "Trace lets you watch the search think. Smoothly shrinking is healthy; "
                       "bouncing means bad starting values.",
            },
            {
                "code": "nl (...), initial(...) iterate(100)\n"
                        "nl (...), initial(...) technique(gn)",
                "output": None,
                "means": "<code>iterate(100)</code> gives the search more attempts; "
                         "<code>technique(gn)</code> switches to the Gauss–Newton algorithm. "
                         "But the real fix is almost always <b>better <code>initial()</code> "
                         "values</b> — read them off the plot.",
                "say": "More iterations and a different algorithm sometimes help — but nine times "
                       "out of ten the cure is a smarter starting guess.",
            },
        ],
    },
    {
        "id": "exercise",
        "title": "Hands-on exercise — hospital infection rate",
        "lead": "A logistic S-curve: infection rate stays low until ~75% bed occupancy, then "
                "rises sharply. Learners build, fit, and interpret it.",
        "blocks": [
            {
                "code": "clear\n"
                        "set seed 999\n"
                        "set obs 30\n"
                        "gen occupancy = 40 + (_n - 1) * (95 - 40) / 29\n"
                        "gen infection_rate = 12 / (1 + exp(0.3*(occupancy-75))) + rnormal(0, 0.5)",
                "output": None,
                "means": "Build 30 hospitals with occupancy 40→95%. True logistic parameters: "
                         "ceiling <b>12</b> infections / 1000 patient-days, inflection at "
                         "<b>75%</b> occupancy, growth rate 0.3.",
                "say": "We're manufacturing a realistic safety signal: infections that stay flat "
                       "until the ward gets dangerously full.",
            },
            {
                "code": "nl (infection_rate = {asym} / ///\n"
                        "    (1 + exp({rate_g}*(occupancy-{inflect})))), ///\n"
                        "    initial(asym 12 rate_g 0.3 inflect 75)",
                "output": "infection_~e| Coefficient  Std. err.   t    P>|t|  [95% conf. int.]\n"
                          "------------+----------------------------------------------------\n"
                          "      /asym |   12.234     0.345    35.46  0.000   11.527   12.941\n"
                          "    /rate_g |    0.312     0.045     6.93  0.000    0.220    0.404\n"
                          "   /inflect |   75.123     0.876    85.76  0.000   73.345   76.901",
                "means": "<b>/asym ≈ 12.2</b> = the ceiling infection rate. <b>/inflect ≈ 75.1%</b> "
                         "= the occupancy at half the maximum — and for a logistic curve the "
                         "inflection point <b>is</b> the EC50. <b>/rate_g ≈ 0.31</b> = steepness. "
                         "All recovered from the true values.",
                "say": "The model nails the danger threshold at ~75% occupancy — that's the "
                       "number that changes how you run the ward.",
            },
            {
                "code": 'di "Occupancy at 50% max rate: " _b[/inflect] " (95% CI: " ///\n'
                        '   _b[/inflect] - 1.96*_se[/inflect] ", " ///\n'
                        '   _b[/inflect] + 1.96*_se[/inflect] ")"',
                "output": "Occupancy at 50% max rate: 75.123 (95% CI: 73.406, 76.840)",
                "means": "Builds the headline sentence by hand: take the estimate "
                         "<code>_b[/inflect]</code> and its standard error <code>_se[/inflect]</code>, "
                         "and form a 95% CI as estimate ± 1.96 × SE. <b>The actionable message: "
                         "keep occupancy below ~75% and infection rates stay low.</b>",
                "say": "Here's the policy line: below about 75% occupancy you're safe; above it, "
                       "infections take off.",
            },
        ],
    },
]

GLOSSARY = [
    ("Coefficient", "The estimated value of a parameter (e.g. /a, /vmax). For non-linear "
                    "models each one has a real-world meaning — a ceiling, a rate, a midpoint."),
    ("Std. err.", "Standard error: how much the estimate would wobble across repeated samples. "
                  "Smaller = more precise."),
    ("t", "The coefficient divided by its standard error — how many standard errors the estimate "
          "sits away from zero. Bigger (in absolute value) = stronger evidence it's not zero."),
    ("P>|t|", "The p-value. Probability of seeing this estimate if the true value were zero. "
              "Below 0.05 = statistically significant. (Exception: in normality tests like "
              "Shapiro–Wilk you WANT p > 0.05.)"),
    ("[95% conf. int.]", "95% confidence interval — the plausible range for the true value. "
                         "Narrow = precise. If it excludes zero, the effect is significant."),
    ("yhat / fitted", "The model's predicted value for each row — points on the fitted curve."),
    ("resid (residual)", "Actual minus predicted. What the model couldn't explain. Good residuals "
                         "are small, patternless, and bell-shaped."),
    ("e(converged)", "1 = the search found a stable answer; 0 = it failed. Must be 1 before you "
                     "trust anything else."),
    ("AIC / BIC", "Model-comparison scores that reward fit and punish complexity. Lower is better. "
                  "Only compare models on the same data."),
    ("Cook's distance", "How much one single data point moves the whole fit. Above 4/n = "
                        "influential, worth investigating."),
    ("nlcom", "Computes a NEW quantity from fitted parameters (half-life, doubling time, EC50) "
              "with a correct confidence interval."),
    ("initial()", "Your starting guesses for the parameters. The single biggest cause of (and "
                  "cure for) convergence problems."),
]

MODEL_GUIDE = [
    ("Exponential decay", "y = a · e^(b·x), b &lt; 0", "Falls fast then flattens",
     "Drug clearance, radioactive decay"),
    ("Exponential growth", "y = a · e^(b·x), b &gt; 0", "Rises ever faster",
     "Early viral load, untreated tumour"),
    ("Michaelis–Menten", "y = Vmax·x / (Km + x)", "Rises then saturates at a ceiling",
     "Receptor binding, dose–response"),
    ("Logistic (sigmoid)", "y = asym / (1 + e^(rate·(x−inflect)))", "S-curve: lag, surge, plateau",
     "CD4 recovery, tumour growth, adoption"),
]

# ---------------------------------------------------------------------------
# RENDER
# ---------------------------------------------------------------------------

def esc(s):
    return html.escape(s)

def render_block(b):
    parts = ['<div class="block">']
    parts.append(f'<div class="label">🖥️ Command</div>')
    parts.append(f'<pre class="code">{esc(b["code"])}</pre>')
    if b.get("output"):
        parts.append('<div class="label">📋 Representative output</div>')
        parts.append(f'<pre class="output">{esc(b["output"])}</pre>')
    if b.get("plot"):
        parts.append('<div class="label">📈 Graph</div>')
        parts.append(f'<div class="plot">{b["plot"]}</div>')
    parts.append('<div class="callout means"><span class="tag">💡 What this means</span>'
                 f'<div>{b["means"]}</div></div>')
    if b.get("say"):
        parts.append('<div class="callout say"><span class="tag">🗣️ Say this</span>'
                     f'<div>{b["say"]}</div></div>')
    if b.get("warn"):
        parts.append('<div class="callout warn"><span class="tag">⚠️ Watch out</span>'
                     f'<div>{b["warn"]}</div></div>')
    parts.append('</div>')
    return "\n".join(parts)

def render_section(s):
    out = [f'<section id="{s["id"]}">']
    out.append(f'<h2>{s["title"]}</h2>')
    if s.get("lead"):
        out.append(f'<p class="lead">{s["lead"]}</p>')
    for b in s["blocks"]:
        out.append(render_block(b))
    out.append('</section>')
    return "\n".join(out)

def render_toc():
    items = "".join(f'<li><a href="#{s["id"]}">{esc(s["title"])}</a></li>' for s in SECTIONS)
    items += '<li><a href="#guide">Model decision guide</a></li>'
    items += '<li><a href="#glossary">Output glossary</a></li>'
    return f'<nav class="toc"><div class="toc-h">Contents</div><ol>{items}</ol></nav>'

def render_guide():
    rows = "".join(
        f"<tr><td><b>{esc(n)}</b></td><td><code>{f}</code></td><td>{esc(shape)}</td>"
        f"<td>{esc(use)}</td></tr>"
        for n, f, shape, use in MODEL_GUIDE
    )
    return (f'<section id="guide"><h2>Model decision guide — pick the curve from the shape</h2>'
            f'<table class="grid"><tr><th>Model</th><th>Formula</th><th>Shape</th>'
            f'<th>Clinical example</th></tr>{rows}</table></section>')

def render_glossary():
    rows = "".join(f'<tr><td><b>{esc(term)}</b></td><td>{esc(d)}</td></tr>'
                   for term, d in GLOSSARY)
    return (f'<section id="glossary"><h2>Output glossary — every term, plain English</h2>'
            f'<table class="grid">{rows}</table></section>')

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Non-Linear Regression — Stata Companion</title>
<style>
:root {{
  --ink:#1f2328; --muted:#6a737d; --line:#d0d7de; --bg:#ffffff;
  --code-bg:#f6f8fa; --term-bg:#0d1117; --term-ink:#c9d1d9;
  --means:#0969da; --means-bg:#ddf4ff; --say:#1a7f37; --say-bg:#dafbe1;
  --warn:#9a6700; --warn-bg:#fff8c5;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
       color:var(--ink); background:var(--bg); }}
.wrap {{ max-width:1180px; margin:0 auto; display:grid; grid-template-columns:260px 1fr; gap:32px; padding:0 24px; }}
header {{ grid-column:1/-1; padding:32px 0 8px; border-bottom:2px solid var(--line); }}
header h1 {{ margin:0 0 6px; font-size:30px; }}
header p {{ margin:0; color:var(--muted); }}
.banner {{ grid-column:1/-1; background:var(--warn-bg); border:1px solid #e7c200;
          border-radius:8px; padding:12px 16px; margin:18px 0; font-size:14px; color:#553c00; }}
.toc {{ position:sticky; top:16px; align-self:start; font-size:14px; max-height:92vh; overflow:auto; }}
.toc-h {{ font-weight:700; text-transform:uppercase; letter-spacing:.04em; font-size:12px;
         color:var(--muted); margin-bottom:8px; }}
.toc ol {{ list-style:none; margin:0; padding:0; }}
.toc li {{ margin:2px 0; }}
.toc a {{ color:var(--ink); text-decoration:none; display:block; padding:4px 8px; border-radius:6px; }}
.toc a:hover {{ background:var(--code-bg); color:var(--means); }}
main {{ min-width:0; padding-bottom:80px; }}
section {{ margin:0 0 44px; }}
h2 {{ font-size:22px; border-bottom:1px solid var(--line); padding-bottom:8px; margin-top:8px; }}
.lead {{ color:var(--muted); margin-top:-2px; }}
.block {{ border:1px solid var(--line); border-radius:10px; padding:16px; margin:18px 0;
         background:#fff; box-shadow:0 1px 2px rgba(0,0,0,.04); }}
.label {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted);
         font-weight:700; margin:10px 0 4px; }}
.label:first-child {{ margin-top:0; }}
pre {{ margin:0; padding:12px 14px; border-radius:8px; overflow-x:auto;
      font:13.5px/1.5 "SF Mono",Consolas,Menlo,monospace; }}
pre.code {{ background:var(--code-bg); border:1px solid var(--line); color:var(--ink); }}
pre.output {{ background:var(--term-bg); color:var(--term-ink); }}
.plot {{ background:var(--code-bg); border:1px dashed var(--line); border-radius:8px;
        padding:10px 14px; font-size:14px; color:#444; font-style:italic; }}
.callout {{ border-radius:8px; padding:10px 14px 12px; margin:12px 0 0; font-size:15px; }}
.callout .tag {{ display:inline-block; font-size:12px; font-weight:700; margin-bottom:4px; }}
.callout div {{ margin:0; }}
.means {{ background:var(--means-bg); border-left:4px solid var(--means); }}
.means .tag {{ color:var(--means); }}
.say {{ background:var(--say-bg); border-left:4px solid var(--say); }}
.say .tag {{ color:var(--say); }}
.say div {{ font-style:italic; }}
.warn {{ background:var(--warn-bg); border-left:4px solid var(--warn); }}
.warn .tag {{ color:var(--warn); }}
code {{ background:var(--code-bg); padding:1px 5px; border-radius:4px;
       font:13px "SF Mono",Consolas,monospace; }}
.callout code {{ background:rgba(0,0,0,.06); }}
table.grid {{ width:100%; border-collapse:collapse; font-size:14.5px; }}
table.grid th, table.grid td {{ text-align:left; padding:8px 10px; border:1px solid var(--line);
                               vertical-align:top; }}
table.grid th {{ background:var(--code-bg); }}
@media print {{
  .toc {{ display:none; }} .wrap {{ display:block; }} .banner {{ break-inside:avoid; }}
  .block {{ break-inside:avoid; box-shadow:none; }}
}}
@media (max-width:820px) {{ .wrap {{ grid-template-columns:1fr; }} .toc {{ position:static; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Non-Linear Regression in Stata — Companion</h1>
    <p>Every command, what its output means, and what to say. Presenter: Dr. Christine Atuhairwe.</p>
  </header>
  <div class="banner">
    <b>About the outputs:</b> the tables below are <b>representative</b> — they show the shape and
    typical magnitude you'll see. Exact figures vary by Stata version and (for simulated datasets)
    the random-number stream, so read them for <i>meaning</i>, not to the last decimal.
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
    page = HTML.format(toc=render_toc(), body=body,
                       guide=render_guide(), glossary=render_glossary())
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    n_blocks = sum(len(s["blocks"]) for s in SECTIONS)
    print(f"Wrote {OUT}: {len(SECTIONS)} sections, {n_blocks} command blocks, "
          f"{len(GLOSSARY)} glossary terms.")

if __name__ == "__main__":
    main()
