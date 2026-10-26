# Throwaway: does tunnel coupling leave a trace in a QDarts charge-sensed scan,
# and how long does a 2-dot + 1-sensor 32x32 / 64x64 scan take?
import time, numpy as np
from qdarts.capacitance_model import CapacitanceModel
from qdarts.simulator import CapacitiveDeviceSimulator
from qdarts.tunneling_simulator import NoisySensorDot, ApproximateTunnelingSimulator
from qdarts.experiment import compensate_simulator_sensors
inner, sens = [0, 1], [2]
C_DD = 20*np.eye(3)/2; C_DD[0,1] = 10; C_DD[0,2] = 4; C_DD[1,2] = 1.0; C_DD = C_DD + C_DD.T   # aF
C_DG = np.zeros((3, 3)); C_DG[0,0] = 11; C_DG[1,1] = 11; C_DG[2,2] = 11; C_DG[2,0] = 1.5; C_DG[2,1] = 0.5
C_DG[0,1] = 2; C_DG[1,0] = 2
def build(tc):
    cap = CapacitiveDeviceSimulator(CapacitanceModel(C_DG, C_DD, -1.0*np.ones(3), ks=4*np.ones(3)))
    T = np.zeros((3,3)); T[0,1] = T[1,0] = tc
    sm = NoisySensorDot(sens); sm.config_peak(g_max=1.0, peak_width_multiplier=20)
    ts = ApproximateTunnelingSimulator(cap, T, 0.3, sm)          # 0.3 K
    cap.set_maximum_polytope_slack(5/ts.beta); ts.num_additional_neighbours[sens] = 2
    ct, m = compensate_simulator_sensors(ts, target_state=[1,1,5], compensation_gates=[2],
                                         sensor_ids=[2], sensor_detunings=np.array([-0.0005]))
    return ct, m
P = np.zeros((3,2)); P[0,0] = 1; P[1,1] = 1
for res in (32, 64):
    out = {}
    for tc in (5e-6, 80e-6):
        ct, m = build(tc)
        minV, maxV = np.array([-0.02,-0.02]), np.array([0.01, 0.01])
        t = time.perf_counter(); s = ct.sensor_scan_2D(P, m, minV, maxV, res, [1,1,5]); dt = time.perf_counter()-t
        out[tc] = np.asarray(s)[:, :, 0]
        print(f"res {res}x{res}, tc = {tc*1e6:.0f} ueV: {dt:.2f} s")
    d = np.abs(out[5e-6]-out[80e-6]); print(f"   max |difference| between tc=5 and 80 ueV scans: {d.max():.3f} (signal range {out[5e-6].min():.2f}-{out[5e-6].max():.2f})")
