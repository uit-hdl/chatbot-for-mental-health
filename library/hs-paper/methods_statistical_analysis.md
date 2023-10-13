Algorithm performance is measured primarily using AUC, sensitivity, and specificity. AUC is the preferred comparison
metric in this study, as it provides a summary of performance that takes into account the rate of both true positives
and true negatives, and does not require selection or estimation of a decision threshold. Unless otherwise stated,
murmur-detection metrics represent average performance across auscultation positions, as metrics are computed using data
from all positions merged into a single dataset that associates recordings to murmur-grades. All confidence intervals
(CI) and p-values reported in this paper correspond to a significance level of 5%, and all statistical tests are
two-sided. The level of statistical significance is signified by (*), (**), and (***), which corresponds to p-values
within the intervals (0.01,0.05], (0.001,0.01] and (0,0.001] respectively. 

We assume that metrics computed on each CV-validation set are independent and identically distributed. CI’s for
sensitivities and specificities were computed using exact methods based on the corresponding binomial distributions.
Decision thresholds were automatically set (for each target separately) as the thresholds that maximized
sensitivity+specificity on the CV training-set under the condition that sensitivity should exceed 50%. As measures of
interrater agreement (all positions considered jointly) we used linear correlation, Cohen’s kappa for agreement on
presence of any murmur, and proportion of recordings with agreement on the presence of any murmur. For Cohen’s kappa, we
also assessed agreement for each position separately. In order to contextualize the AUC for murmur-detection obtained by
the algorithm, we evaluated how well the annotations of SA could distinguish the recordings that AD had classified as
murmur-grade>=2 by treating SAs annotations as predictors of ADs annotations and computing the AUC.
