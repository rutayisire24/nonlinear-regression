*===============================================================*
*  Applied Non-Linear Regression for Clinical Research
*  Companion Stata script for the slide deck
*  Presenter: Dr. Christine Atuhairwe
*
*  HOW TO USE: run section by section (highlight + Ctrl-D),
*  or run the whole file with:  do nonlinear_regression.do
*===============================================================*

clear all
set more off


*===============================================================*
* MODEL 1 - EXPONENTIAL DECAY   (Auto data)
* Analogy: drug concentration falling as body mass rises
*===============================================================*

* --- Load and explore -----------------------------------------
sysuse auto, clear
describe
list mpg weight in 1/5

* Variables
*   mpg    = miles per gallon   (outcome)
*   weight = vehicle weight, lb (predictor)

* --- Plot first ------------------------------------------------
twoway scatter mpg weight, ///
    title("MPG vs Vehicle Weight") ///
    xtitle("Weight (lbs)") ///
    ytitle("Miles per Gallon") ///
    scheme(s2color)

* --- Fit the model ---------------------------------------------
* Starting values read off the plot: max MPG ~ 40, slow decay
nl (mpg = {a} * exp({b} * weight)), ///
    initial(a 40 b -0.0005)

* Same model with robust standard errors (IRR-style)
nl (mpg = {a} * exp({b} * weight)), ///
    initial(a 40 b -0.0005) vce(robust)

* --- Predict and diagnose --------------------------------------
predict fitted_exp, yhat
predict resid_exp, resid

rvfplot, yline(0) ///
    title("Residuals vs Fitted - Exponential Model")

qnorm resid_exp, ///
    title("Q-Q Plot of Residuals")

histogram resid_exp, normal ///
    title("Distribution of Residuals")

* --- Derived parameter: half-life ------------------------------
* Weight change that halves MPG (same idea as drug half-life)
nlcom (half_life: ln(2) / -_b[/b])


*===============================================================*
* MODEL 2 - LOGISTIC GROWTH   (US life expectancy)
* Analogy: tumour growth, CD4 recovery, cognitive decline
*===============================================================*

* --- Load and explore -----------------------------------------
sysuse uslifeexp, clear
list year le in 1/10

* Variables
*   year = calendar year        (predictor)
*   le   = life expectancy, yr (outcome)

* --- Plot first ------------------------------------------------
twoway scatter le year, ///
    title("US Life Expectancy Over Time") ///
    xtitle("Year") ytitle("Life Expectancy (years)")

* --- Fit the model ---------------------------------------------
* Starting values: ceiling ~80, moderate rate, inflection ~1950
nl (le = {asym} / (1 + exp({rate} * (year - {inflect})))), ///
    initial(asym 80 rate -0.1 inflect 1950)

estimates store logistic_model

* --- Predict, plot, forecast -----------------------------------
predict fitted_log, yhat
predict resid_log, resid

twoway (scatter le year) ///
       (line fitted_log year, lpattern(dash) lcolor(red) lwidth(med)), ///
    title("Actual vs Predicted Life Expectancy") ///
    legend(label(1 "Actual") label(2 "Predicted"))

* Forecast life expectancy for 2020
local asym    = _b[/asym]
local rate    = _b[/rate]
local inflect = _b[/inflect]
display "Predicted LE 2020: " `asym'/(1+exp(`rate'*(2020-`inflect')))

* Residuals over time
scatter resid_log year, yline(0) title("Residuals Over Time")


*===============================================================*
* MODEL 3 - MICHAELIS-MENTEN   (simulated dose-response)
* Analogy: receptor binding, saturating dose-response
*===============================================================*

* --- Simulate a dose-response study ----------------------------
clear
set seed 12345
set obs 40

* Dose levels: 0 to 100 mg/kg
gen dose = (_n - 1) * (100 / 39)

* True values: Vmax = 90%, Km (EC50) = 25 mg/kg, plus noise
gen response = (90 * dose) / (25 + dose) + rnormal(0, 4)

twoway scatter response dose, ///
    title("Dose-Response Curve") ///
    xtitle("Dose (mg/kg)") ytitle("Response (%)") ///
    ylabel(0(20)100)

* --- Fit the model ---------------------------------------------
nl (response = {vmax} * dose / ({km} + dose)), ///
    initial(vmax 90 km 25)

* Same model with robust standard errors
nl (response = {vmax} * dose / ({km} + dose)), ///
    initial(vmax 90 km 25) vce(robust)

* --- Diagnose --------------------------------------------------
predict fitted_mm, yhat
predict resid_mm, resid

twoway (scatter response dose) ///
       (line fitted_mm dose, lcolor(red) lwidth(med)), ///
    title("Michaelis-Menten Fit") ///
    xtitle("Dose (mg/kg)") ytitle("Response (%)")

rvfplot, yline(0) title("Residuals vs Fitted")

predict cooksd_mm, cooksd
scatter cooksd_mm _n, title("Cook's Distance") yline(4/40)


*===============================================================*
* MODEL 4 - EXPONENTIAL GROWTH   (simulated viral load)
* Analogy: viral load increase, early tumour growth
*===============================================================*

* --- Simulate viral load after infection -----------------------
clear
set seed 67890
set obs 20

gen day = _n

* True values: start = 100, growth rate = 0.3, plus noise
gen viral_load = 100 * exp(0.3 * day) + rnormal(0, 200)

twoway scatter viral_load day, ///
    title("Viral Load Over Time") ///
    xtitle("Days Post-Infection") ///
    ytitle("Viral Load (copies/mL)")

* --- Fit the model ---------------------------------------------
nl (viral_load = {a} * exp({b} * day)), ///
    initial(a 100 b 0.3)

* Derived parameter: doubling time
nlcom (doubling_time: ln(2) / _b[/b])


*===============================================================*
* COMPARING LINEAR vs NON-LINEAR
*===============================================================*

sysuse auto, clear

* Linear model on raw data
regress mpg weight
estimates store linear_model

* Non-linear model (exponential decay)
nl (mpg = {a} * exp({b} * weight)), initial(a 40 b -0.0005)
estimates store nl_model
predict resid_exp, resid

* Compare AIC / BIC (lower = better)
estimates stats linear_model nl_model

* Compare residual spread
predict resid_linear, resid
summarize resid_linear resid_exp


*===============================================================*
* DIAGNOSTIC CHECKLIST  (run after EVERY non-linear fit)
*===============================================================*

* 1. Convergence (should be 1)
di e(converged)

* 2. Residuals vs fitted
rvfplot, yline(0)

* 3. Normality of residuals
qnorm resid
swilk resid              // Shapiro-Wilk: p > 0.05 = normal

* 4. Influential points
predict cooksd, cooksd
summarize cooksd, detail

* 5. Parameter plausibility
*    do the estimates make clinical sense?

* 6. Profile-likelihood CIs (better for small samples)
nl (y = {a} * exp({b} * x)), initial(a 10 b -0.1) level(95)


*===============================================================*
* DEBUGGING A MODEL THAT WON'T CONVERGE
*===============================================================*

* Trace each iteration
nl (y = {a} * exp({b} * x)), initial(a 40 b -0.0005) trace

* Increase the iteration limit
nl (y = {a} * exp({b} * x)), initial(a 40 b -0.0005) iterate(100)

* Try a different algorithm
nl (y = {a} * exp({b} * x)), initial(a 40 b -0.0005) technique(gn)


*===============================================================*
* HANDS-ON EXERCISE - Hospital infection rate vs occupancy
* (logistic S-curve: low until ~75% full, then rises sharply)
*===============================================================*

* --- Create the data -------------------------------------------
clear
set seed 999
set obs 30

* Hospital occupancy (%)
gen occupancy = 40 + (_n - 1) * (95 - 40) / 29

* Generate infection rate from a logistic curve + noise
*   asymptote = 12 per 1000 patient-days, inflection at 75%
gen infection_rate = 12 / (1 + exp(0.3*(occupancy-75))) + rnormal(0, 0.5)
replace infection_rate = round(infection_rate, 0.1)

label variable occupancy "Hospital Bed Occupancy (%)"
label variable infection_rate "Infection Rate (per 1000 patient-days)"

list in 1/10
twoway scatter infection_rate occupancy, ///
    title("Hospital Infection Rate by Occupancy") ///
    xtitle("Occupancy (%)") ///
    ytitle("Infection Rate (per 1000 patient-days)")

* --- Fit the logistic model ------------------------------------
nl (infection_rate = {asym} / ///
    (1 + exp({rate_g}*(occupancy-{inflect})))), ///
    initial(asym 12 rate_g 0.3 inflect 75)

* --- Predict and plot ------------------------------------------
predict fitted_rate, yhat
predict resid_ex, resid

twoway (scatter infection_rate occupancy) ///
       (line fitted_rate occupancy, lcolor(red) lwidth(med)), ///
    title("Actual vs Predicted Infection Rate") ///
    xtitle("Occupancy (%)") ytitle("Infection Rate (per 1000)")

* --- EC50 = inflection point -----------------------------------
* For a logistic curve the inflection point IS the EC50.
nlcom (occupancy_50pct: _b[/inflect])

* Report it by hand with a 95% CI
di "Occupancy at 50% max rate: " _b[/inflect] " (95% CI: " ///
   _b[/inflect] - 1.96*_se[/inflect] ", " ///
   _b[/inflect] + 1.96*_se[/inflect] ")"

* --- Residual diagnostics --------------------------------------
qnorm resid_ex, title("Q-Q Plot of Residuals")
rvfplot, yline(0) title("Residuals vs Fitted")


*===============================================================*
* QUICK REFERENCE - the four go-to models
*===============================================================*
* Exponential decay : nl (y = {a} * exp({b} * x)), initial(a 10 b -0.1)
* Exponential growth: nl (y = {a} * (1 - exp({b} * x))), initial(a 100 b 0.1)
* Michaelis-Menten  : nl (y = {vmax} * x / ({km} + x)), initial(vmax 100 km 25)
* Logistic (sigmoid): nl (y = {asym} / (1 + exp({rate}*(x-{inflect})))), ///
*                        initial(asym 80 rate -0.1 inflect 1950)
*===============================================================*

* end of file
