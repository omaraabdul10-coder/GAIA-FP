import numpy as np
from scipy.stats import norm, mannwhitneyu
rng=np.random.default_rng(1)
def power(A,n1,n0,alpha,R=3000):
    d=np.sqrt(2)*norm.ppf(A); k=0
    for _ in range(R):
        a=rng.normal(d,1,n1); b=rng.normal(0,1,n0)
        k+= mannwhitneyu(a,b,alternative='greater').pvalue<=alpha
    return k/R
for n1,n0,lab in [(39,26,'H1 tam'),(30,20,'H1, DR4-də bəziləri itsə')]:
    for A in (0.65,0.70,0.73,0.80):
        print(lab,A,[round(power(A,n1,n0,al),2) for al in (0.025,0.0125,0.005)])
for n in (200,500,2000):
    print('n/2 vs n/2',n,[round(power(0.60,n//2,n//2,0.005),2), round(power(0.55,n//2,n//2,0.005),2)])
