*===============================================================*
*  Descriptive Statistics & Distributions  —  HANDS-ON
*  Companion Stata script for the scrolling HTML site
*  Presenter: Dr. Christine Atuhairwe
*
*  The HTML companion taught each idea on a CLINICAL cohort.
*  Here we PRACTISE the very same commands on Stata's built-in
*  `auto` dataset (loads in one line, no files to find).
*
*  Clinical variable      ->  auto stand-in
*    age / SBP (symmetric) ->  mpg / weight
*    CRP (right-skewed)    ->  price        (a few costly cars = the tail)
*    sex / ward (category) ->  foreign / rep78
*
*  HOW TO USE: run section by section (highlight + Ctrl-D),
*  or run the whole file with:  do descriptives_practice.do
*===============================================================*

clear all
set more off


*===============================================================*
* 1. MEET THE DATA  — rows are cars (think: patients)
*===============================================================*
sysuse auto, clear
describe                 // variables, types, how many observations
list make mpg price weight foreign in 1/8   // eyeball the first 8 rows

* Look for: some columns are numbers you can average (mpg, price, weight),
*           others are labels you can only count (foreign, rep78).


*===============================================================*
* 2. TWO KINDS OF VARIABLE  — this choice drives the summary
*===============================================================*
codebook, compact        // scan the "type" + unique-values columns

* Continuous (average it):    mpg, price, weight, length
* Categorical (count it):     foreign (Domestic/Foreign), rep78 (1-5)


*===============================================================*
* 3. THE CENTRE  — mean, median, mode
*===============================================================*
summarize mpg, detail    // SYMMETRIC: mean ~ median  (either is "typical")

summarize price, detail  // SKEWED:   mean >> median
* A few expensive cars drag the MEAN up, but the MEDIAN is unmoved.
* When mean >> median, report the MEDIAN as the honest centre.


*===============================================================*
* 4. THE SPREAD  — range, IQR, variance, SD
*===============================================================*
tabstat mpg, stats(min p25 median p75 max range iqr sd variance)

* SD = typical distance from the mean, in the original units.
* For roughly-Normal data ~95% sit within mean +/- 2 SD
* (this is exactly how lab REFERENCE RANGES are built).
* IQR = width of the middle 50% — the spread you quote with a median.


*===============================================================*
* 5. THE DESCRIPTIVE TABLE  — your paper's "Table 1"
*===============================================================*
tabstat mpg price weight, ///
    stats(n mean sd min p25 median p75 max) columns(statistics)

* Read each row: mean ~ median  -> report mean (SD)
*                mean >> median  -> report median (p25-p75)   [price]


*===============================================================*
* 6. THE SHAPE  — histograms
*===============================================================*
histogram mpg, normal ///
    title("Distribution of MPG") xtitle("Miles per gallon")

* The red curve is the Normal "bell" with the same mean & SD.
* mpg fills the bell fairly evenly = roughly symmetric.


*===============================================================*
* 7. WHEN THE MEAN LIES  — right-skew, and the log fix
*===============================================================*
histogram price, normal ///
    title("Price — right-skewed") xtitle("Price ($)")

* Long right tail -> the mean is dragged into it.
gen lnprice = ln(price)
histogram lnprice, normal ///
    title("log(Price) — now ~symmetric") xtitle("ln(price)")

* Logging pulls the tail in. Skewed money/lab values are often
* log-transformed before modelling, and reported as median (IQR).


*===============================================================*
* 8. THE BOX-AND-WHISKER PLOT  — five numbers at a glance
*===============================================================*
graph box price, title("Box plot — price")
* Box = Q1 to Q3 (the IQR), line = median, dots beyond whiskers = outliers.
* Box pushed left with a long right whisker = right-skew.

graph box mpg, over(foreign) title("MPG by origin")
* Same plot split by group — a preview of section 11.


*===============================================================*
* 9. IS IT NORMAL?  — Q-Q plot + Shapiro-Wilk
*===============================================================*
qnorm mpg, title("Q-Q plot — MPG")     // points on the line = Normal
swilk mpg                              // RULE: p > 0.05 = Normal enough

qnorm price, title("Q-Q plot — price") // points bend off the line
swilk price                            // p < 0.05 = NOT Normal (the skew)

* Counter-intuitive but key: for swilk, a BIG p-value is the GOOD result.
* In large samples trust the plot/histogram over the p-value alone.


*===============================================================*
* 10. COUNTING CATEGORIES  — frequencies & proportions
*===============================================================*
tabulate foreign         // count, percent, cumulative %
tabulate rep78           // note: repair record has some missing values

* No mean for categories — the PERCENT column is what you report
* ("X% were foreign"). These are the building blocks of prevalence/risk.


*===============================================================*
* 11. DESCRIBE BY GROUP  — the seed of every comparison
*===============================================================*
tabstat mpg, by(foreign) stats(n mean sd min max)
graph bar (mean) mpg, over(foreign) ///
    title("Mean MPG by origin") ytitle("Mean MPG")

* Do foreign cars really get better mileage? DESCRIBE the gap here...
* ...the NEXT lecture (t-test / ANOVA) tests whether it is REAL.
* A difference in means is NOT yet a significant difference.

* Quick formal peek (next lecture's tool):
* ttest mpg, by(foreign)


*===============================================================*
* QUICK REFERENCE  — which summary for which variable
*===============================================================*
* Continuous & symmetric : mean (SD)            | histogram, qnorm, swilk
* Continuous & skewed     : median (p25-p75/IQR) | histogram, graph box
* Categorical             : count (percent)      | tabulate, graph bar
*
* Workhorse commands:
*   summarize VAR, detail
*   tabstat VARLIST, stats(n mean sd min p25 median p75 max)
*   histogram VAR, normal      graph box VAR
*   qnorm VAR                  swilk VAR
*   tabulate VAR               tabstat VAR, by(GROUP) stats(...)
*===============================================================*

* end of file
