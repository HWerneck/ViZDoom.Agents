# -*- coding: utf-8 -*-
"""Dados_Mestrado_Ex3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16QVB-Zy5LaEpqZL3MVhAmp76-x-tJv57

#1. Mount Google Drive
This allows the notebook to import/export data from files inside Google Drive.
"""

from google.colab import drive
drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
from google.colab import files
import math
import numpy as np
import pandas as pd
pd.plotting.register_matplotlib_converters()
import seaborn as sbrn
import matplotlib.pyplot as mplotl
# %matplotlib inline
from scipy import stats

path = "/content/drive/My Drive/ViZDoom/Data/Mestrado/Ex3/Basic/Data/"
agentScreen = "basic"
agentLabel = "labels"
suffix = ".monitor.csv"
suffix_eval = "_eval.monitor.csv"

file_path = path + agentScreen + "1" + suffix
basic_training_data = pd.read_csv(file_path, skiprows = 1)
print(basic_training_data)
basic_training_data.describe()

file_path = path + agentScreen + "1" + suffix_eval
basic_eval_data = pd.read_csv(file_path, skiprows = 1)
print(basic_eval_data)
basic_eval_data.describe()

file_path = path + agentLabel + "1" + suffix
basicLabels_training_data = pd.read_csv(file_path, skiprows = 1)
print(basicLabels_training_data)
basicLabels_training_data.describe()

file_path = path + agentLabel + "1" + suffix_eval
basicLabels_eval_data = pd.read_csv(file_path, skiprows = 1)
print(basicLabels_eval_data)
basicLabels_eval_data.describe()

basic_training_ttest_data = pd.DataFrame()
basic_eval_ttest_data = pd.DataFrame()

basic_training_ttest_data['R1'] = basic_training_data['r']
basic_eval_ttest_data['R1'] = basic_eval_data['r']

basicLabels_training_ttest_data = pd.DataFrame()
basicLabels_eval_ttest_data = pd.DataFrame()

basicLabels_training_ttest_data['R1'] = basicLabels_training_data['r']
basicLabels_eval_ttest_data['R1'] = basicLabels_eval_data['r']

#This code adds data from the .csv files to the first data file
for iii in range (2, 6):
    file_path = path + agentScreen + str(iii) + suffix

    basic_training_data_temp = pd.read_csv(file_path, skiprows = 1)
    tmp = 'R' + str(iii)
    basic_training_ttest_data[tmp] = basic_training_data_temp["r"]

    basic_training_data += pd.read_csv(file_path, skiprows = 1)
basic_training_data = basic_training_data/5
basic_training_data.describe()
basic_training_ttest_data.describe()

#This code adds data from the .csv files to the first data file
for iii in range (2, 6):
    file_path = path + agentScreen + str(iii) + suffix_eval

    basic_eval_data_temp = pd.read_csv(file_path, skiprows = 1)
    tmp = 'R' + str(iii)
    basic_eval_ttest_data[tmp] = basic_eval_data_temp["r"]

    basic_eval_data += pd.read_csv(file_path, skiprows = 1)
basic_eval_data = basic_eval_data/5
basic_eval_data.describe()
basic_eval_ttest_data.describe()

#This code adds data from the .csv files to the first data file
for iii in range (2, 6):
    file_path = path + agentLabel + str(iii) + suffix

    basicLabels_training_data_temp = pd.read_csv(file_path, skiprows = 1)
    tmp = 'R' + str(iii)
    basicLabels_training_ttest_data[tmp] = basicLabels_training_data_temp["r"]

    basicLabels_training_data += pd.read_csv(file_path, skiprows = 1)
basicLabels_training_data = basicLabels_training_data/5
basicLabels_training_data.describe()
basicLabels_training_ttest_data.describe()

#This code adds data from the .csv files to the first data file
for iii in range (2, 6):
    file_path = path + agentLabel + str(iii) + suffix_eval

    basicLabels_eval_data_temp = pd.read_csv(file_path, skiprows = 1)
    tmp = 'R' + str(iii)
    basicLabels_eval_ttest_data[tmp] = basicLabels_eval_data_temp["r"]

    basicLabels_eval_data += pd.read_csv(file_path, skiprows = 1)
basicLabels_eval_data = basicLabels_eval_data/5
basicLabels_eval_data.describe()
basicLabels_eval_ttest_data.describe()

for episode in range(len(basic_training_ttest_data)):
    basic_training_ttest_data.loc[episode, 'Mean'] = basic_training_ttest_data.loc[episode, 'R1':'R5'].mean()
    basic_training_ttest_data.loc[episode, 'Std. Dev.'] = basic_training_ttest_data.loc[episode, 'R1':'R5'].std()

for episode in range(len(basic_eval_ttest_data)):
    basic_eval_ttest_data.loc[episode, 'Mean'] = basic_eval_ttest_data.loc[episode, 'R1':'R5'].mean()
    basic_eval_ttest_data.loc[episode, 'Std. Dev.'] = basic_eval_ttest_data.loc[episode, 'R1':'R5'].std()

for episode in range(len(basicLabels_training_ttest_data)):
    basicLabels_training_ttest_data.loc[episode, 'Mean'] = basicLabels_training_ttest_data.loc[episode, 'R1':'R5'].mean()
    basicLabels_training_ttest_data.loc[episode, 'Std. Dev.'] = basicLabels_training_ttest_data.loc[episode, 'R1':'R5'].std()

for episode in range(len(basicLabels_eval_ttest_data)):
    basicLabels_eval_ttest_data.loc[episode, 'Mean'] = basicLabels_eval_ttest_data.loc[episode, 'R1':'R5'].mean()
    basicLabels_eval_ttest_data.loc[episode, 'Std. Dev.'] = basicLabels_eval_ttest_data.loc[episode, 'R1':'R5'].std()

ttest_basic_basicLabels_ite = pd.DataFrame()

smaller = len(basic_training_ttest_data)
if (smaller > (len(basicLabels_training_ttest_data))):
    smaller = len(basicLabels_training_ttest_data)

for episode in range(smaller):
    ttest, pval = stats.ttest_ind(basic_training_ttest_data.loc[episode, 'R1':'R10'], basicLabels_training_ttest_data.loc[episode, 'R1':'R10'])
    ttest_basic_basicLabels_ite.loc[episode, 't-test'] = ttest
    ttest_basic_basicLabels_ite.loc[episode, 'p-value'] = pval
print(ttest_basic_basicLabels_ite)
ttest_basic_basicLabels_ite.describe()

print(basic_training_data['r'])

print(basicLabels_training_data['r'])

ttest_basic_basicLabels, pval_basic_basicLabels = stats.ttest_ind(basic_training_data['r'], basicLabels_training_data['r'])
print("basic-basicLabels ttest is", ttest_basic_basicLabels, "and pval is", pval_basic_basicLabels, ".")

#Sets plot width and height, respectively
mplotl.figure(figsize=(22,10))

#Sets plot title
#mplotl.title("Training agents -- Experiment 1 - Basic vs Basic (Labels)")

#Sets the limits of each axis
mplotl.xlim(0, 3000)
mplotl.ylim(-1000, 2000)

#Adds a label for each axis
mplotl.xlabel("Episodes")
mplotl.ylabel("Reward")

data1 = basic_training_data['r']
data2 = basicLabels_training_data['r']

#This code specifies the type of plot we are doing. In this case, a line chart
sbrn.lineplot(data = data1, label = "Basic agent")
sbrn.lineplot(data = data2, label = "Basic agent (labels)")

#Saves the figure
mplotl.savefig("Ex3_training_basic-vs-basicLabels.jpeg")
files.download("Ex3_training_basic-vs-basicLabels.jpeg")

#Sets plot width and height, respectively
mplotl.figure(figsize=(22,10))

#Sets plot title
#mplotl.title("Evaluating agents - Experiment 1 - Basic vs Basic (Labels)")

#Sets the limits of each axis
mplotl.xlim(0,70)
mplotl.ylim(-50,2000)
for x in range(7):
    mplotl.axvline(x*10, 0, 100, linestyle = '--', dashes = (10,8), linewidth = 0.5, color = 'black', alpha = 0.2)

#Adds a label for each axis
mplotl.xlabel("Episodes")
mplotl.ylabel("Reward")

#This code specifies the type of plot we are doing. In this case, a line chart
sbrn.lineplot(data = basic_eval_data['r'], label = "Basic agent")
sbrn.lineplot(data = basicLabels_eval_data['r'], label = "Basic agent (Labels)")

#Saves the figure
mplotl.savefig("Ex2_evaluating1_basic-vs-basicLabels.jpeg")
files.download("Ex2_evaluating1_basic-vs-basicLabels.jpeg")

from scipy.stats.mstats_basic import Ttest_1sampResult
#Sets plot width and height, respectively
mplotl.figure(figsize=(22,10))

#Sets plot title
mplotl.title("Basic vs Basic (Labels) - T-test")

#Sets the limits of each axis
mplotl.xlim(0,1000)
mplotl.ylim(-6,6)

#Adds a label for each axis
mplotl.xlabel("Episodes")
mplotl.ylabel("t-test")

#This code specifies the type of plot we are doing. In this case, a line chart
sbrn.scatterplot(data = ttest_basic_basicLabels_ite['t-test'], label = "t-test")
mplotl.axhline(ttest_basic_basicLabels, color = 'r')

#Saves the figure
mplotl.savefig("Ttest1_basic-vs-basicLabels.jpeg")
files.download("Ttest1_basic-vs-basicLabels.jpeg")

n_x = basic_training_data['r'].count()
n_y = basicLabels_training_data['r'].count()

u_x = basic_training_data['r'].mean()
u_y = basicLabels_training_data['r'].mean()

d_x = basic_training_data['r'].std()
d_y = basicLabels_training_data['r'].std()