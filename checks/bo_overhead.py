# Per-step BoTorch overhead in 3D (P1, P2, back gate): GP refit + acquisition optimisation.
import time, warnings, torch
warnings.filterwarnings("ignore")
from botorch.models import SingleTaskGP
from botorch.fit import fit_gpytorch_mll
from gpytorch.mlls import ExactMarginalLogLikelihood
from botorch.acquisition.logei import qLogExpectedImprovement
from botorch.optim import optimize_acqf
torch.set_num_threads(1); torch.manual_seed(0)
bounds = torch.tensor([[0.0]*3, [1.0]*3], dtype=torch.double)
f = lambda X: torch.sigmoid(10*(0.3 - (X - 0.6).norm(dim=-1, keepdim=True)))   # plateau-like objective
for n in (10, 50, 100, 200, 300):
    X = torch.rand(n, 3, dtype=torch.double); Y = f(X) + 0.01*torch.randn(n, 1, dtype=torch.double)
    t = time.perf_counter()
    gp = SingleTaskGP(X, Y); fit_gpytorch_mll(ExactMarginalLogLikelihood(gp.likelihood, gp))
    t_fit = time.perf_counter() - t; t = time.perf_counter()
    optimize_acqf(qLogExpectedImprovement(gp, best_f=Y.max()), bounds=bounds, q=1, num_restarts=10, raw_samples=256)
    t_acq = time.perf_counter() - t
    print(f"n = {n:3d} points: GP fit {t_fit:5.2f} s + acquisition {t_acq:5.2f} s = {t_fit+t_acq:5.2f} s per step")
