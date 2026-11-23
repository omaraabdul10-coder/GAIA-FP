"""RV semi-amplitude of the primary for a companion of mass m2 (Jupiter masses), in km/s.
M1 in solar masses, P in days, inclination in degrees. Same formula as followup/shamakhy_targets.py."""
import numpy as np
MJ = 9.546e-4   # Jupiter mass in solar masses

def K_kms(m2_MJ, M1, P_days, e=0.0, inc_deg=90.0):
    m2 = np.asarray(m2_MJ)*MJ
    return (28.4329*np.asarray(m2_MJ)*np.sin(np.radians(inc_deg))*(M1 + m2)**(-2/3)
            *(np.asarray(P_days)/365.25)**(-1/3)/np.sqrt(1 - np.clip(e, 0, .95)**2)/1000)
