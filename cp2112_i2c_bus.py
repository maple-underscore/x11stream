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
    
    def writeto(self, address, buffer, **kwargs):
        """Write data to I2C device.
        
        Args:
            address: I2C device address (7-bit)
            buffer: Bytes or bytearray to write
            **kwargs: Additional arguments (ignored for CP2112)
        """
        self.device.write(address, bytes(buffer))
    
    def readfrom_into(self, address, buffer, **kwargs):
        """Read data from I2C device into buffer.
        
        Args:
            address: I2C device address (7-bit)
            buffer: Buffer to read data into
            **kwargs: Additional arguments (ignored for CP2112)
        """
        data = self.device.read(address, len(buffer))
        for i, byte in enumerate(data):
            buffer[i] = byte
    
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
