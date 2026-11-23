"""Sanity check of the follow-up K formula on the Sun-Jupiter system (NASA NSSDC values).
Jupiter makes the Sun move with K = (2 pi a / P) * MJ/(Msun+MJ) = 12.46 m/s for a circular orbit seen edge-on."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'followup'))
from kfun import K_kms

def test_sun_jupiter_K():
    K = K_kms(1.0, 1.0, 4332.589, e=0.0, inc_deg=90.0)*1000      # m/s
    assert abs(K - 12.46) < 0.15

def test_K_scales_with_sin_i_and_mass():
    assert abs(K_kms(2.0, 1.0, 365.25, inc_deg=30.0) - K_kms(1.0, 1.0, 365.25, inc_deg=90.0)) < 1e-3
