"""This module handles deprojection of a set of arrays from another set of
arrays. This is useful for cleaning TODs of unwanted signals, for example."""
import numpy as np, scipy.signal
from enlib import utils, pmat, rangelist

def estimate_white_noise(tod, nchunk=10, chunk_size=1000):
	"""Robust time-domain estimation of white noise level."""
	vs = []
	for ci in range(nchunk):
		i1 = ci*tod.shape[-1]/nchunk
		i2 = i1+chunk_size
		sub = tod[...,i1:i2]
		if sub.shape[-1] < 2: continue
		dtod = sub[...,1:]-sub[...,:-1]
		vs.append(np.mean(dtod**2,-1)/2)
	return np.median(vs,0)

def find_spikes(tod, nsigma=10, width=15, padding=7, noise=None):
	res = []
	ftod = tod.reshape(-1,tod.shape[-1])
	if noise is None: noise = estimate_white_noise(ftod)**0.5
	for di, d in enumerate(ftod):
		smooth = scipy.signal.medfilt(d, width)
		bad = np.abs(d-smooth) > noise[di]*nsigma
		bad = rangelist.Rangelist(bad)
		bad = bad.widen(padding)
		res.append(rangelist.Rangelist(bad))
	res = rangelist.Multirange(res)
	res.data.reshape(tod.shape[:-1])
	return res

def deglitch(tod, nsigma=10, width=15, padding=7, inplace=False):
	spikes = find_spikes(tod)
	return gapfill.gapfill_linear(tod, spikes, inplace=inplace)

def project(tod, basis, weight=1):
	rhs = basis.dot(np.conj((tod*weight)).T)
	div = basis.dot(np.conj((basis*weight)).T)
	amp = np.linalg.solve(div, rhs)
	return np.conj(amp).T.dot(basis)

def fit_phase_flat(tods, az, daz=1*utils.arcmin, cuts=None, niter=3, overlap=10, clean_tod=False):
	# for the given tods[ndet,nsamp], cuts (multirange[ndet,nsamp]) and az[nsamp],
	if not clean_tod: tods = tods.copy()
	# Set up phase pixels
	amin = np.min(az)
	amax = np.max(az)
	naz = int((amax-amin)/daz)+1
	pflat = pmat.PmatPhaseFlat(amin, daz, naz)
	# Output and work arrays
	phase  = np.zeros((2,naz))
	dphase = phase.copy()
	hits   = phase.copy()
	# Precompute div
	pflat.backard(tods*0+1, hits, -1)
	hits[hits==0] = 1
	for i in range(niter):
		# Overall logic: gapfill -> bin -> subtract -> loop
		if cuts is not None:
			gapfill.gapfill_linear(tods, cuts, overlap=overlap, inplace=True)
		pflat.backward(tods, dphase)
		dphase /= hits
		phase += dphase
		pflat.forward(tods, -dphase)
	return phase