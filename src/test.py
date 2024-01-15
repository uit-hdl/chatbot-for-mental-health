from utils.backend import get_shared_subfolder_name
from utils.backend import PROMPTS_DIR
from utils.general import test

GLOBAL_VAR = 0.0
test(2)


import numpy as np
import matplotlib.pyplot as plt

fig, ax = plt.subplots(2, 2)
cv_indices = np.arange(8)
colors = ["k", "r", "b", "g"]

for i, ax in zip(cv_indices, ax.flatten(order="A")):
    ax.plot([1,2], [1,2], color=colors[i])