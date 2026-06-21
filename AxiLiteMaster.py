import cocotb
from cocotb.triggers import RisingEdge


class AxiLiteMaster:
    """
    Class to test the AXI Lite as a Master.
    """
    def __init__(self, dut, clk, prefix="s00_axi"):
        """
        Predefine the value.
        """
        self.dut = dut
        self.clk = clk
        self.p = prefix

        # Initialice the signals.
        self._s("awvalid").value = 0
        self._s("wvalid").value  = 0
        self._s("bready").value  = 0
        self._s("arvalid").value = 0
        self._s("rready").value  = 0

    def _s(self, name):
        """Get the port as Python signal.
        """
        return getattr(self.dut, f"{self.p}_{name}")

    async def wait_ready(self, sig, timeout=1000):
        """Waiting to avoid blocking.

        Args:
            sig (int): condition
            timeout (int, optional): Value to wait. Defaults to 1000.

        Raises:
            cocotb.result.TestFailure: Timeout waiting.
        """
        for _ in range(timeout):
            if sig.value:
                return
            await RisingEdge(self.clk)
        raise cocotb.result.TestFailure(f"Timeout waiting {sig._name}")


    async def write(self, addr, data: bytes):
        """This method writes in the register.

        Args:
            addr (int): address to write.
            data (bytes): data to write.
        """
        self._s("awaddr").value = addr
        self._s("wdata").value = int.from_bytes(data, "little")
        self._s("wstrb").value = (1 << len(data)) - 1


        # Active AWVALID and WVALID at the same time.
        self._s("awvalid").value = 1
        self._s("wvalid").value  = 1


        # Wait unitl the DUT accepts the address and data.
        await self.wait_ready(self._s("awready"))


        # Deactivate both
        self._s("awvalid").value = 0
        self._s("wvalid").value  = 0



        # B channel
        
        self._s("bready").value = 1
        await self.wait_ready(self._s("bvalid"))
        self._s("bready").value = 0


    async def read(self, addr, size):
        """This method reads the register value.

        Args:
            addr (int): address to read
            size (int): bytes to read

        Returns:
            int: read value 
        """
        # --- AR channel ---
        self._s("araddr").value = addr
        self._s("arvalid").value = 1

        # Wait until the slave accept the address.
        await self.wait_ready(self._s("arready"))

        # Drops ARVALID to complete the handshake
        self._s("arvalid").value = 0
        self._s("araddr").value = 0

        # --- R channel ---
        self._s("rready").value = 1

        # Wait until the data is available.
        await self.wait_ready(self._s("rvalid"))

        # Captures the data.
        val = int(self._s("rdata").value)

        # Drops the RREADY to complete the handshake.
        self._s("rready").value = 0


        # Return the value in bytes format.
        return val.to_bytes(size, "little")

