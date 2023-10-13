The multi-position linear regression model for prediction of AVPGmean obtained after model selection and parameter estimation was 

AVPGmean = 3.5 + 0.6 * MG_A^2 + 1.1 * MG_P^2 + 0.5 * MG_T + ...
... 0.9 * MG_A^2 * noise_P + 8.9 * MG_M * noise_A * noise_P * noise_T.

The subindices A, P, T, M refers to the aortic, pulmonic, tricuspid and mitral position respectively, MGi denotes the predicted murmur-grade of position i, and noise_i  is the indicator variable that modifies the murmur-grade weights if the recording from position i is noisy (in which case MGi is set to zero). The p-values for all model parameters were lower than 0.01.

After selecting the model, we performed cross-validation to estimate how well the multi-position model predicted AVPGmean compared to the single-position models across a range of cutoff thresholds, using AUC as comparison metrics. Figure 5 shows the results for each position, with significant differences indicated by *. For AVPGmean cut off 10 mm Hg, the multi-position prediction outperforms each of the single-position predictions by amounts corresponding to p-values 0.09, 0.02, 0.40 and 0.01 respectively.