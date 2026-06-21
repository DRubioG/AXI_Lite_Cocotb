# Axi-Lite Cocotb

This tests the AXI-Lite protocol

## Example

``` python

import cocotb
from cocotb.triggers import RisingEdge, Timer
from AxiLiteMaster import *

async def clock_gen(clk, period_ns=1):
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

    # Launch the parallel clock
    axi = AxiLiteMaster(dut, dut.s00_axi_aclk, prefix="s00_axi")
    cocotb.start_soon(clock_gen(dut.s00_axi_aclk))

    # Reset
    await reset_gen(dut.s00_axi_aresetn, dut.s00_axi_aclk)

    for _ in range(15):
        await RisingEdge(dut.s00_axi_aclk)
    # Write
    await axi.write(0x00, (50).to_bytes(4, "little"))
    await axi.write(0x04, (25).to_bytes(4, "little"))

    # Read
    data = await axi.read(0x00, 4)
    dut._log.info(f"Read back: {(int.from_bytes(data, 'little'))}")
    data = await axi.read(0x04, 4)
    dut._log.info(f"Read back: {(int.from_bytes(data, 'little'))}")
    data = await axi.read(0x08, 4)
    dut._log.info(f"Read back: {(int.from_bytes(data, 'little'))}")

    t = cocotb.utils.get_sim_time()
    dut._log.info(f"Time sim: {t}")


```