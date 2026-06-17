import cocotb
from cocotb.triggers import RisingEdge, Timer


class AxiLiteMaster:
    def __init__(self, dut, clk, prefix="s00_axi"):
        self.dut = dut
        self.clk = clk
        self.p = prefix

        # Inicialización AXI-Lite (evita X y problemas al arrancar)
        self._s("awvalid").value = 0
        self._s("wvalid").value  = 0
        self._s("bready").value  = 0
        self._s("arvalid").value = 0
        self._s("rready").value  = 0

    def _s(self, name):
        return getattr(self.dut, f"{self.p}_{name}")

    def _s(self, name):
        return getattr(self.dut, f"{self.p}_{name}")

    async def wait_ready(self, sig, timeout=1000):
        for _ in range(timeout):
            if sig.value:
                return
            await RisingEdge(self.clk)
        raise cocotb.result.TestFailure(f"Timeout esperando {sig._name}")


    async def write(self, addr, data: bytes):
        self.dut._log.warning("paso 1")
        self._s("awaddr").value = addr
        self._s("wdata").value = int.from_bytes(data, "little")
        self._s("wstrb").value = (1 << len(data)) - 1

        self.dut._log.warning("paso 2")
        # Activar AWVALID y WVALID a la vez
        self._s("awvalid").value = 1
        self._s("wvalid").value  = 1

        self.dut._log.warning("paso 3")
        # Esperar a que el DUT acepte dirección + datos
        await self.wait_ready(self._s("awready"))


        self.dut._log.warning("paso 4")
        # Desactivar ambos
        self._s("awvalid").value = 0
        self._s("wvalid").value  = 0



        # B channel
        self.dut._log.warning("paso 5")
        self._s("bready").value = 1
        await self.wait_ready(self._s("bvalid"))
        self._s("bready").value = 0


    async def read(self, addr, size):
        # AR channel
        self._s("araddr").value = addr
        self._s("arvalid").value = 1
        await self.wait_ready(self._s("arready"))
        self._s("arvalid").value = 0

        # R channel
        self._s("rready").value = 1
        await self.wait_ready(self._s("rvalid"))
        val = int(self._s("rdata").value)
        self._s("rready").value = 0

        return val.to_bytes(size, "little")



async def clock_gen(clk, period_ns=1):
    # await RisingEdge(clk)
    while True:
        clk.value = 0
        await Timer(period_ns/2, units="ns")
        clk.value = 1
        await Timer(period_ns/2, units="ns")


async def reset_gen(rst, clk, cycles=5):
    rst.value = 0
    for _ in range(cycles):
        await RisingEdge(clk)
    rst.value = 1
    await RisingEdge(clk)


@cocotb.test()
async def test_axi_lite(dut):

    # Lanzar reloj en paralelo
    axi = AxiLiteMaster(dut, dut.s00_axi_aclk, prefix="s00_axi")
    cocotb.start_soon(clock_gen(dut.s00_axi_aclk))

    # Reset
    await reset_gen(dut.s00_axi_aresetn, dut.s00_axi_aclk)

    for _ in range(15):
        await RisingEdge(dut.s00_axi_aclk)
    # Escritura
    await axi.write(0x00, b"\x01\x00\x00\x00")

    await axi.write(0x04, (127).to_bytes(4, "little"))
    # Lectura
    data = await axi.read(0x00, 4)
    dut._log.info(f"Read back: {data.hex()}")

    for _ in range(5000000):
        await RisingEdge(dut.s00_axi_aclk)
        t = cocotb.utils.get_sim_time()
        dut._log.info(f"Tiempo sim: {t}")

