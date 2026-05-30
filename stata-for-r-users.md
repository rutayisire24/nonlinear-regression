# Non-Linear Regression: Stata explained for R users

You know R. You don't know Stata's stats syntax. This maps every command in
`nonlinear_regression.do` to its R equivalent and — more importantly — explains
**why** we run each one.

The single most useful fact: **Stata's `nl` *is* R's `nls()`.** Everything else
is plumbing around that one idea.

---

## 1. The big picture — what are we even doing?

Linear regression (`lm()` / Stata `regress`) fits a *straight line*: `y = a + b*x`.
The parameters enter the equation linearly, so there's a closed-form formula —
R/Stata just solve it in one shot.

**Non-linear regression** fits a *curve* whose parameters enter non-linearly —
`y = a * exp(b*x)`, `y = Vmax*x/(Km+x)`, an S-curve, etc. There is **no formula**
for the answer. Instead the computer *searches*: it starts from your initial guess
and iteratively nudges the parameters until the residual sum-of-squares stops
shrinking. This is exactly how R's `nls()` works.

Two consequences that feel foreign coming from `lm()`:

1. **You must supply starting values** (`start=` in R, `initial()` in Stata). A bad
   guess → the search wanders off and never converges.
2. **You must check it actually converged** before trusting any number.

That's why the workflow is always the same four beats:

| Step | Why | R | Stata |
|------|-----|---|-------|
| **LOOK** | The shape of the scatter tells you which curve to fit | `plot()` / `ggplot` | `twoway scatter` |
| **GUESS** | The search needs a sane starting point | `start = list(...)` | `initial(...)` |
| **FIT** | Run the iterative search | `nls()` | `nl ()` |
| **CHECK** | Did it converge? Are residuals clean? | `summary`, `resid`, `qqnorm` | `e(converged)`, `rvfplot`, `qnorm` |

---

## 2. Master translation table

| Concept | Stata | R |
|---|---|---|
| Load built-in data | `sysuse auto, clear` | `data(mtcars)` (analogous demo set) |
| Clear environment | `clear` / `clear all` | `rm(list = ls())` |
| Inspect structure | `describe` | `str(df)` / `glimpse(df)` |
| First rows | `list mpg weight in 1/5` | `head(df[, c("mpg","weight")], 5)` |
| Create a variable | `gen dose = ...` | `df$dose <- ...` / `mutate()` |
| Overwrite a variable | `replace x = ...` | `df$x <- ...` |
| Row number | `_n` | `seq_len(n)` / `1:n` |
| Number of rows | `set obs 40` | `n <- 40` |
| Random seed | `set seed 12345` | `set.seed(12345)` |
| Normal noise | `rnormal(0, 4)` | `rnorm(n, 0, 4)` |
| Scatter plot | `twoway scatter y x` | `plot(x, y)` |
| **Fit non-linear model** | `nl (y = {a}*exp({b}*x)), initial(a 40 b -0.0005)` | `nls(y ~ a*exp(b*x), data=df, start=list(a=40, b=-0.0005))` |
| Linear model | `regress mpg weight` | `lm(mpg ~ weight, data=df)` |
| A parameter in the model | `{a}` (braces) | a bare symbol in the formula |
| Starting values | `initial(a 40 b -0.0005)` | `start = list(a=40, b=-0.0005)` |
| Get a coefficient | `_b[/b]` | `coef(m)["b"]` |
| Get a standard error | `_se[/b]` | `sqrt(diag(vcov(m)))["b"]` |
| Fitted values | `predict yhat, yhat` | `fitted(m)` / `predict(m)` |
| Residuals | `predict r, resid` | `residuals(m)` |
| Robust standard errors | `vce(robust)` | `lmtest::coeftest(m, vcov = sandwich::vcovHC)` |
| Store a model | `estimates store m1` | `m1 <- nls(...)` (just a variable) |
| Compare models | `estimates stats m1 m2` | `AIC(m1, m2)` / `BIC(m1, m2)` |
| Derived quantity + CI | `nlcom (hl: ln(2)/-_b[/b])` | `car::deltaMethod(m, "log(2)/-b")` |
| Confidence intervals | `... , level(95)` | `confint(m)` (profile likelihood) |
| Convergence flag | `di e(converged)` | `m$convInfo$isConv` |
| Trace iterations | `nl ..., trace` | `nls(..., trace = TRUE)` |
| Max iterations | `nl ..., iterate(100)` | `nls(..., control = nls.control(maxiter = 100))` |
| Algorithm | `nl ..., technique(gn)` | `nls(..., algorithm = "port")` |
| Residuals-vs-fitted plot | `rvfplot` | `plot(fitted(m), residuals(m)); abline(h=0)` |
| Q-Q plot | `qnorm r` | `qqnorm(r); qqline(r)` |
| Histogram + normal | `histogram r, normal` | `hist(r, freq=FALSE); curve(dnorm(...), add=TRUE)` |
| Normality test | `swilk r` | `shapiro.test(r)` |
| Cook's distance | `predict cd, cooksd` | `cooks.distance(m)` (see note in §4) |
| Summary stats | `summarize x, detail` | `summary(x)` / `quantile(x)` |
| Print a value | `display "..." x` | `cat("...", x, "\n")` |
| Local macro (a value) | `local a = _b[/asym]` | `a <- coef(m)["asym"]` |

> **Note on `_b[/b]`:** in Stata the parameters of an `nl` fit are stored with a
> leading slash (`/a`, `/b`). `_b[/b]` means "the estimate of b". In R you just
> index `coef(m)["b"]`.

---

## 3. Walk-through: the four models, both languages

### Model 1 — Exponential decay
*Why:* the scatter of MPG vs weight curves downward and flattens — a straight line
would be biased. We fit `y = a·e^(b·x)` with `b < 0` (decay).

```stata
* Stata
sysuse auto, clear
twoway scatter mpg weight                       // LOOK
nl (mpg = {a}*exp({b}*weight)), initial(a 40 b -0.0005)   // GUESS + FIT
```
```r
# R
plot(mtcars$wt, mtcars$mpg)                      # LOOK
m1 <- nls(mpg ~ a*exp(b*wt), data = mtcars,
          start = list(a = 40, b = -0.0005))     # GUESS + FIT
summary(m1)
```
*Reading it:* `a` ≈ ceiling (y at x=0), `b` ≈ decay rate (negative). Same as R's
`summary(m1)` coefficient table: Estimate / Std.Error / t / p.

**Derived quantity — half-life.** *Why:* the raw rate `b` is abstract; "how much
weight halves the MPG" is intuitive. Half-life `= ln(2)/-b`. But you can't just
compute it — you need its **confidence interval**, which requires propagating the
uncertainty in `b`. Stata's `nlcom` does this with the **delta method**; in R
that's `car::deltaMethod`.

```stata
nlcom (half_life: ln(2) / -_b[/b])
```
```r
car::deltaMethod(m1, "log(2)/-b")   # estimate + SE + 95% CI
```

### Model 2 — Logistic growth (S-curve)
*Why:* life expectancy rises slowly, then fast, then plateaus — an S. Three
meaningful parameters: ceiling, steepness, midpoint (year of fastest growth).

```stata
nl (le = {asym}/(1 + exp({rate}*(year-{inflect})))), ///
    initial(asym 80 rate -0.1 inflect 1950)
```
```r
m2 <- nls(le ~ asym/(1 + exp(rate*(year - inflect))),
          data = d, start = list(asym = 80, rate = -0.1, inflect = 1950))

# R BONUS: a "self-starting" model picks initial values for you
m2 <- nls(le ~ SSlogis(year, Asym, xmid, scal), data = d)
```
> **R has a superpower Stata lacks here:** self-starting functions
> (`SSlogis`, `SSmicmen`, `SSasymp`, `SSgompertz`, `SSweibull`) estimate their own
> starting values, so you can skip the `start=` guesswork entirely.

### Model 3 — Michaelis–Menten (saturating dose–response)
*Why:* response rises with dose then saturates. `Vmax` = ceiling, `Km` = the dose
giving half of Vmax (the EC50 — the key potency number in pharmacology).

```stata
nl (response = {vmax}*dose/({km}+dose)), initial(vmax 90 km 25)
```
```r
m3 <- nls(response ~ vmax*dose/(km + dose), data = d,
          start = list(vmax = 90, km = 25))
# or self-starting:
m3 <- nls(response ~ SSmicmen(dose, Vm, K), data = d)
```

### Model 4 — Exponential growth (viral load)
*Why:* same exponential family as Model 1 but `b > 0` → explosive growth. The
intuitive derived number is **doubling time = ln(2)/b**.

```stata
nl (viral_load = {a}*exp({b}*day)), initial(a 100 b 0.3)
nlcom (doubling_time: ln(2) / _b[/b])
```
```r
m4 <- nls(viral_load ~ a*exp(b*day), data = d, start = list(a = 100, b = 0.3))
car::deltaMethod(m4, "log(2)/b")
```

---

## 4. The statistics concepts, explained

**Why starting values / convergence at all?**
`lm()` solves linear algebra once. `nls()`/`nl` minimise residual SS *iteratively*.
If the surface is flat or the start is far off, the search fails. Always check:
```r
m$convInfo$isConv      # R  → TRUE
```
```stata
di e(converged)        // Stata → 1
```
If this isn't TRUE/1, **every other number is garbage** — fix `start`/`initial`.

**Robust standard errors (`vce(robust)`).**
Non-linear data often has non-constant residual variance (heteroskedasticity).
The *estimates* don't change, but the default standard errors are then wrong.
Robust SEs fix the error bars.
```r
lmtest::coeftest(m, vcov = sandwich::vcovHC(m))
```

**Delta method (`nlcom`).**
You want a function of the parameters (half-life, doubling time, EC50) *with a
correct CI*. You can't just transform the point estimate — you must propagate the
variance. That's the delta method.
```r
car::deltaMethod(m, "log(2)/-b")
```

**AIC / BIC (`estimates stats`).**
How to choose between the linear and non-linear model? AIC and BIC reward fit and
penalise complexity — **lower is better**. Only compare models on the *same data*.
```r
AIC(m_linear, m_nl); BIC(m_linear, m_nl)
```

**Residual diagnostics.**
Residuals = what the model couldn't explain. Good residuals are small, patternless,
and roughly normal.
```r
plot(fitted(m), residuals(m)); abline(h = 0)   # rvfplot: want a shapeless cloud
qqnorm(residuals(m)); qqline(residuals(m))      # qnorm: want points on the line
shapiro.test(residuals(m))                       # swilk: want p > 0.05 (= normal!)
```
> Counter-intuitive: in a normality test a **big** p-value is the *good* result —
> it means you can't reject "these residuals are normal".

**Cook's distance.**
Measures how much one single point pulls the whole fit; cut-off `4/n`.
```r
# Built-in for lm():
cooks.distance(lm_model)
# For nls() it isn't in base R — use the nlstools package or compute manually.
```

**Profile-likelihood CIs (`level(95)`).**
For small samples the symmetric "estimate ± 1.96·SE" interval is too crude. Both
Stata's profile CIs and R's `confint()` on an `nls` object use the more honest
profile-likelihood method.
```r
confint(m)   # profile-likelihood CIs by default for nls
```

---

## 5. TL;DR for an R user

- `nl (...)` **=** `nls(...)`. Braces `{a}` = bare parameter names. `initial()` = `start=`.
- You *must* give starting values and *must* check convergence — same as `nls()`.
- `_b[/p]` = `coef(m)["p"]`, `_se[/p]` = `sqrt(diag(vcov(m)))["p"]`.
- `nlcom` = `car::deltaMethod` (derived quantity + CI via delta method).
- `predict … yhat/resid` = `fitted()` / `residuals()`.
- `estimates stats` = `AIC()`/`BIC()`; `swilk` = `shapiro.test()`; `qnorm` = `qqnorm()`.
- **R-only shortcut:** `SSlogis`, `SSmicmen`, `SSasymp` self-start, so you can often
  drop the starting-value guesswork that Stata forces on you.
