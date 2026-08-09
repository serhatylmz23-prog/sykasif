from terminal_v2.runtime.kernel import RuntimeKernel

def test_kernel():

    k=RuntimeKernel()

    k.start()

    assert k.status()["running"]
