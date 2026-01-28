#!/usr/bin/env python3
"""
CP2112 I2C Bus Wrapper
Provides a minimal I2C bus interface for CP2112 to work with Adafruit CircuitPython libraries
"""


class CP2112I2CBus:
    """Minimal I2C bus wrapper for CP2112 to work with Adafruit libraries.
    
    This class wraps a CP2112 device instance to provide the I2C bus interface
    expected by Adafruit CircuitPython display libraries.
    """
    
    def __init__(self, cp2112_device):
        """Initialize the I2C bus wrapper.
        
        Args:
            cp2112_device: CP2112Device instance to wrap
        """
        self.device = cp2112_device
    
    def writeto(self, address, buffer, *, start=0, end=None, stop=True):
        """Write data to I2C device.
        
        This method is intended to be compatible with the CircuitPython
        ``busio.I2C.writeto`` API. The CP2112 always generates a stop
        condition at the end of a transfer and does not support repeated
        starts, so the ``stop`` argument is accepted for compatibility but
        is otherwise ignored.
        
        Args:
            address: I2C device address (7-bit)
            buffer: Bytes-like object containing data to write.
            start (int, optional): Start index within ``buffer`` to write
                from. Defaults to 0.
            end (int or None, optional): One-past-end index within
                ``buffer`` to stop writing at. If None, writes through the
                end of ``buffer``. Defaults to None.
            stop (bool, optional): Whether to generate a stop bit at the
                end of the transfer. Accepted for API compatibility but
                ignored because CP2112 always sends a stop. Defaults to True.
        """
        if end is None:
            end = len(buffer)
        # Use a memoryview to avoid copying when slicing, then convert to
        # bytes for the underlying CP2112 device API.
        view = memoryview(buffer)[start:end]
        self.device.write(address, bytes(view))
    
    def readfrom_into(self, address, buffer, *, start=0, end=None):
        """Read data from I2C device into buffer.
        
        This method is intended to be compatible with the CircuitPython
        ``busio.I2C.readfrom_into`` API.
        
        Args:
            address: I2C device address (7-bit)
            buffer: Writable buffer to read data into.
            start (int, optional): Start index within ``buffer`` where
                received data should be stored. Defaults to 0.
            end (int or None, optional): One-past-end index within
                ``buffer`` where data storage should stop. If None, reads
                through the end of ``buffer``. Defaults to None.
        """
        if end is None:
            end = len(buffer)
        length = end - start
        if length <= 0:
            return
        data = self.device.read(address, length)
        for i, byte in enumerate(data):
            buffer[start + i] = byte
    
    def writeto_then_readfrom(
        self,
        address,
        buffer_out,
        buffer_in,
        *,
        out_start=0,
        out_end=None,
        in_start=0,
        in_end=None,
        stop=False,
    ):
        """Write to an address and then read from the same address.
        
        This method is intended to be compatible with the CircuitPython
        ``busio.I2C.writeto_then_readfrom`` API. The CP2112 does not support
        a true repeated-start condition, so this implementation performs a
        write operation followed by a separate read operation, each with
        their own stop condition. The ``stop`` parameter is accepted for
        compatibility but is otherwise ignored.
        
        Args:
            address: I2C device address (7-bit).
            buffer_out: Bytes-like object containing data to write.
            buffer_in: Writable buffer to receive the data read back.
            out_start (int, optional): Start index within ``buffer_out`` to
                write from. Defaults to 0.
            out_end (int or None, optional): One-past-end index within
                ``buffer_out`` to stop writing at. If None, writes through
                the end of ``buffer_out``. Defaults to None.
            in_start (int, optional): Start index within ``buffer_in`` where
                received data should be stored. Defaults to 0.
            in_end (int or None, optional): One-past-end index within
                ``buffer_in`` where data storage should stop. If None, reads
                through the end of ``buffer_in``. Defaults to None.
            stop (bool, optional): Accepted for API compatibility but
                ignored; CP2112 always sends a stop between write and read.
        """
        # Handle output slice
        if out_end is None:
            out_end = len(buffer_out)
        out_view = memoryview(buffer_out)[out_start:out_end]
        if len(out_view):
            self.device.write(address, bytes(out_view))

        # Handle input slice
        if in_end is None:
            in_end = len(buffer_in)
        in_length = in_end - in_start
        if in_length <= 0:
            return
        data = self.device.read(address, in_length)
        for i, byte in enumerate(data):
            buffer_in[in_start + i] = byte
    
    def try_lock(self):
        """Try to lock the bus.
        
        CP2112 doesn't require explicit locking, so this always succeeds.
        
        Returns:
            bool: Always True
        """
        return True
    
    def unlock(self):
        """Unlock the bus.
        
        CP2112 doesn't require explicit locking, so this is a no-op.
        """
        pass
    
    def scan(self):
        """Scan I2C bus for devices.
        
        Attempts to read from all valid I2C addresses to detect devices.
        
        Returns:
            list: List of I2C addresses where devices were found
        """
        found = []
        # Scan valid I2C 7-bit address range (0x08-0x77)
        for addr in range(0x08, 0x78):
            try:
                # Try to read 1 byte to detect device presence
                self.device.read(addr, 1)
                found.append(addr)
            except (OSError, IOError):
                # Device not present at this address
                pass
        return found
