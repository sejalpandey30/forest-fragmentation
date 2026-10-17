"""Accuracy helpers and independent validators (each returns a dict containing 'f1')."""
import numpy as np


def prf(pred, ref, domain=None):
    pred, ref = np.asarray(pred, bool), np.asarray(ref, bool)
    d = np.ones_like(pred) if domain is None else np.asarray(domain, bool)
    tp = int((pred & ref & d).sum()); fp = int((pred & ~ref & d).sum()); fn = int((~pred & ref & d).sum())
    tn = int((~pred & ~ref & d).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(precision=prec, recall=rec, f1=f1, overall_accuracy=(tp + tn) / max(1, tp + fp + fn + tn),
                n_reference=int((ref & d).sum()), n_predicted=int((pred & d).sum()))


def worldcover_validator(cfg, wc2020):
    """Label-transfer check: our 2020 map vs ESA WorldCover 2020 (v100). Same producer as the
    training labels, so it is a consistency check, not fully independent ground truth."""
    def fn(forests, valid):
        if cfg.start_year not in forests:
            return {}
        return prf(forests[2020] if 2020 in forests else forests[cfg.start_year], wc2020 == 10, valid & (wc2020 > 0))
    return fn


def hansen_validator(cfg, tree2000, lossyear):
    """Independent check of CHANGE: loss between start and end year vs Hansen et al. (2013) annual loss.
    Hansen detects stand-replacing loss only, so recall of subtle edge degradation is expected to be low."""
    def fn(forests, valid):
        y0, y1 = cfg.start_year, cfg.end_year
        ref = (tree2000 >= 30) & (lossyear > y0 - 2000) & (lossyear <= y1 - 2000)
        pred = forests[y0] & ~forests[y1]
        return prf(pred, ref, valid & forests[y0])
    return fn
