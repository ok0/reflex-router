import pytest


def test_two_neuron_lif_cython() -> None:
    from brian2 import (
        Network,
        NeuronGroup,
        SpikeMonitor,
        Synapses,
        defaultclock,
        ms,
        prefs,
    )
    from brian2.codegen.runtime.cython_rt import CythonCodeObject

    if not CythonCodeObject.is_available():
        pytest.fail(
            "brian2 Cython target unavailable: a working C/C++ compiler and Cython are required "
            "(see discovery/README.md 'Host prerequisites'). Not falling back to numpy."
        )

    try:
        prefs.codegen.target = "cython"
        defaultclock.dt = 0.1 * ms

        G = NeuronGroup(
            2,
            "dv/dt = (I - v) / (10*ms) : 1\nI : 1",
            threshold="v > 1",
            reset="v = 0",
            method="exact",
        )
        G.I = [2.0, 0.0]
        S = Synapses(G, G, on_pre="v_post += 1.5")
        S.connect(i=0, j=1)
        M = SpikeMonitor(G)
        net = Network(G, S, M)
        net.run(20 * ms)

        codeobjs = [o.codeobj for o in net.objects if getattr(o, "codeobj", None) is not None]
        assert codeobjs
        assert all(isinstance(c, CythonCodeObject) for c in codeobjs)

        i = M.i[:]
        t = M.t / ms
        n0 = t[i == 0]
        n1 = t[i == 1]
        assert len(n0) >= 2
        assert 6.5 <= n0[0] <= 7.5
        assert len(n1) >= 1
        assert n1[0] > n0[0]
        assert n1[0] <= n0[0] + 0.5
    finally:
        prefs.codegen.target = "auto"
