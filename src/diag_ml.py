import sys, numpy as np, warnings; warnings.filterwarnings('ignore')
sys.argv=['x','0.30']
exec(open('benchmark.py').read().split("S = {}")[0])
from sklearn.ensemble import HistGradientBoostingClassifier as H
from sklearn.model_selection import cross_val_predict, StratifiedKFold
cv=StratifiedKFold(5,shuffle=True,random_state=0)
def cvauc(cols):
    p=cross_val_predict(H(max_iter=300,learning_rate=0.05),X[cols].values,y,cv=cv,method='predict_proba')[:,1]; return roc_auc(p,y)
print('demographics only [P,e,mfit,d,G]:', round(cvauc(['P','e','mfit','d','G']),3))
for c in ['P','e','mfit','d','G']: print('  single',c, round(max(roc_auc(X[c].values,y),1-roc_auc(X[c].values,y)),3))
print('dm,z only:', round(cvauc(['dm','z']),3))
