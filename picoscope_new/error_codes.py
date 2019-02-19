"""Error codes - copied from the PS6000 programmer's manual."""

# To get formatting correct do following copy-replace in
# Programmers Notepad
# 1. Copy/replace ' - ' with '", "'
# 2. Copy/replace '\r' with '"],\r' (enable slash expressions when doing)
# 3. Copy/replace '^([0-9A-F]{2} ){1}' with '0x\1, "' (w/ regex)
# 4. Copy/replace '^([0-9A-F]{3} ){1}' with '0x\1, "' (w/ regex)
# 5. Copy/repplace '0x' with '[0x'
ERROR_CODES = [
    [0x00, "PICO_OK", "The PicoScope XXXX is functioning correctly."],
    [0x01, "PICO_MAX_UNITS_OPENED",
     "An attempt has been made to open more than PSXXXX_MAX_UNITS."],
    [0x02, "PICO_MEMORY_FAIL",
     "Not enough memory could be allocated on the host machine."],
    [0x03, "PICO_NOT_FOUND", "No PicoScope XXXX could be found."],
    [0x04, "PICO_FW_FAIL", "Unable to download firmware."],
    [0x05, "PICO_OPEN_OPERATION_IN_PROGRESS"],
    [0x06, "PICO_OPERATION_FAILED"],
    [0x07, "PICO_NOT_RESPONDING",
     "The PicoScope XXXX is not responding to commands from the PC."],
    [0x08, "PICO_CONFIG_FAIL",
     "The configuration information in the PicoScope XXXX has become " +
     "corrupt or is missing."],
    [0x09, "PICO_KERNEL_DRIVER_TOO_OLD",
     "The picopp.sys file is too old to be used with the device driver."],
    [0x0A, "PICO_EEPROM_CORRUPT",
     "The EEPROM has become corrupt, so the device will use a default " +
     "setting."],
    [0x0B, "PICO_OS_NOT_SUPPORTED",
     "The operating system on the PC is not supported by this driver."],
    [0x0C, "PICO_INVALID_HANDLE",
     "There is no device with the handle value passed."],
    [0x0D, "PICO_INVALID_PARAMETER", "A parameter value is not valid."],
    [0x0E, "PICO_INVALID_TIMEBASE",
     "The timebase is not supported or is invalid."],
    [0x0F, "PICO_INVALID_VOLTAGE_RANGE",
     "The voltage range is not supported or is invalid."],
    [0x10, "PICO_INVALID_CHANNEL",
     "The channel number is not valid on this device or no channels have " +
     "been set."],
    [0x11, "PICO_INVALID_TRIGGER_CHANNEL",
     "The channel set for a trigger is not available on this device."],
    [0x12, "PICO_INVALID_CONDITION_CHANNEL",
     "The channel set for a condition is not available on this device."],
    [0x13, "PICO_NO_SIGNAL_GENERATOR",
     "The device does not have a signal generator."],
    [0x14, "PICO_STREAMING_FAILED",
     "Streaming has failed to start or has stopped without user request."],
    [0x15, "PICO_BLOCK_MODE_FAILED",
     "Block failed to start", "a parameter may have been set wrongly."],
    [0x16, "PICO_NULL_PARAMETER", "A parameter that was required is NULL."],
    [0x18, "PICO_DATA_NOT_AVAILABLE",
     "No data is available from a run block call."],
    [0x19, "PICO_STRING_BUFFER_TOO_SMALL",
     "The buffer passed for the information was too small."],
    [0x1A, "PICO_ETS_NOT_SUPPORTED", "ETS is not supported on this device."],
    [0x1B, "PICO_AUTO_TRIGGER_TIME_TOO_SHORT",
     "The auto trigger time is less than the time it will take to collect " +
     "the pre-trigger data."],
    [0x1C, "PICO_BUFFER_STALL",
     "The collection of data has stalled as unread data would be " +
     "overwritten."],
    [0x1D, "PICO_TOO_MANY_SAMPLES",
     "Number of samples requested is more than available in the current " +
     "memory segment."],
    [0x1E, "PICO_TOO_MANY_SEGMENTS",
     "Not possible to create number of segments requested."],
    [0x1F, "PICO_PULSE_WIDTH_QUALIFIER",
     "A null pointer has been passed in the trigger function or one of the " +
     "parameters is out of range."],
    [0x20, "PICO_DELAY",
     "One or more of the hold-off parameters are out of range."],
    [0x21, "PICO_SOURCE_DETAILS",
     "One or more of the source details are incorrect."],
    [0x22, "PICO_CONDITIONS", "One or more of the conditions are incorrect."],
    [0x23, "PICO_USER_CALLBACK",
     "The driver's thread is currently in the psXXXXBlockReady callback " +
     "function and therefore the action cannot be carried out."],
    [0x24, "PICO_DEVICE_SAMPLING",
     "An attempt is being made to get stored data while streaming. " +
     "Either stop streaming by calling psXXXXStop, or use " +
     "psXXXXGetStreamingLatestValues."],
    [0x25, "PICO_NO_SAMPLES_AVAILABLE",
     "because a run has not been completed."],
    [0x26, "PICO_SEGMENT_OUT_OF_RANGE",
     "The memory index is out of range."],
    [0x27, "PICO_BUSY", "Data cannot be returned yet."],
    [0x28, "PICO_STARTINDEX_INVALID",
     "The start time to get stored data is out of range."],
    [0x29, "PICO_INVALID_INFO",
     "The information number requested is not a valid number."],
    [0x2A, "PICO_INFO_UNAVAILABLE",
     "The handle is invalid so no information is available about the device." +
     " Only PICO_DRIVER_VERSION is available."],
    [0x2B, "PICO_INVALID_SAMPLE_INTERVAL",
     "The sample interval selected for streaming is out of range."],
    [0x2D, "PICO_MEMORY", "Driver cannot allocate memory."],
    [0x2E, "PICO_SIG_GEN_PARAM",
     "Incorrect parameter passed to signal generator."],
    [0x34, "PICO_WARNING_AUX_OUTPUT_CONFLICT",
     "AUX cannot be used as input and output at the same time."],
    [0x35, "PICO_SIGGEN_OUTPUT_OVER_VOLTAGE",
     "The combined peak to peak voltage and the analog offset voltage " +
     "exceed the allowable voltage the signal generator can produce."],
    [0x36, "PICO_DELAY_NULL", "NULL pointer passed as delay parameter."],
    [0x37, "PICO_INVALID_BUFFER",
     "The buffers for overview data have not been set while streaming."],
    [0x38, "PICO_SIGGEN_OFFSET_VOLTAGE",
     "The analog offset voltage is out of range."],
    [0x39, "PICO_SIGGEN_PK_TO_PK",
     "The analog peak to peak voltage is out of range."],
    [0x3A, "PICO_CANCELLED", "A block collection has been cancelled."],
    [0x3B, "PICO_SEGMENT_NOT_USED",
     "The segment index is not currently being used."],
    [0x3C, "PICO_INVALID_CALL",
     "The wrong GetValues function has been called for the collection mode " +
     "in use."],
    [0x3F, "PICO_NOT_USED", "The function is not available."],
    [0x40, "PICO_INVALID_SAMPLERATIO",
     "The aggregation ratio requested is out of range."],
    [0x41, "PICO_INVALID_STATE",
     "Device is in an invalid state."],
    [0x42, "PICO_NOT_ENOUGH_SEGMENTS",
     "The number of segments allocated is fewer than the number of captures " +
     "requested."],
    [0x43, "PICO_DRIVER_FUNCTION",
     "You called a driver function while another driver function was still " +
     "being processed."],
    [0x45, "PICO_INVALID_COUPLING",
     "An invalid coupling type was specified in psXXXXSetChannel."],
    [0x46, "PICO_BUFFERS_NOT_SET",
     "An attempt was made to get data before a data buffer was defined."],
    [0x47, "PICO_RATIO_MODE_NOT_SUPPORTED",
     "The selected downsampling mode (used for data reduction) is not " +
     "allowed."],
    [0x49, "PICO_INVALID_TRIGGER_PROPERTY",
     "An invalid parameter was passed to psXXXXSetTriggerChannelProperties."],
    [0x4A, "PICO_INTERFACE_NOT_CONNECTED",
     "The driver was unable to contact the oscilloscope."],
    [0x4D, "PICO_SIGGEN_WAVEFORM_SETUP_FAILED",
     "A problem occurred in psXXXXSetSigGenBuiltIn or " +
     "psXXXXSetSigGenArbitrary."],
    [0x4E, "PICO_FPGA_FAIL"],
    [0x4F, "PICO_POWER_MANAGER"],
    [0x50, "PICO_INVALID_ANALOGUE_OFFSET",
     "An impossible analogue offset value was specified in psXXXXSetChannel."],
    [0x51, "PICO_PLL_LOCK_FAILED",
     "Unable to configure the PicoScope XXXX."],
    [0x52, "PICO_ANALOG_BOARD",
     "The oscilloscope's analog board is not detected, or is not connected " +
     "to the digital board."],
    [0x53, "PICO_CONFIG_FAIL_AWG",
     "Unable to configure the signal generator."],
    [0x54, "PICO_INITIALISE_FPGA",
     "The FPGA cannot be initialized, so unit cannot be opened."],
    [0x56, "PICO_EXTERNAL_FREQUENCY_INVALID",
     "The frequency for the external clock is not within 5% of the " +
     "stated value."],
    [0x57, "PICO_CLOCK_CHANGE_ERROR",
     "The FPGA could not lock the clock signal."],
    [0x58, "PICO_TRIGGER_AND_EXTERNAL_CLOCK_CLASH",
     "You are trying to configure the AUX input as both a trigger and a " +
     "reference clock."],
    [0x59, "PICO_PWQ_AND_EXTERNAL_CLOCK_CLASH",
     "You are trying to configure the AUX input as both a pulse width " +
     "qualifier and a reference clock."],
    [0x5A, "PICO_UNABLE_TO_OPEN_SCALING_FILE",
     "The scaling file set can not be opened."],
    [0x5B, "PICO_MEMORY_CLOCK_FREQUENCY",
     "The frequency of the memory is reporting incorrectly."],
    [0x5C, "PICO_I2C_NOT_RESPONDING",
     "The I2C that is being actioned is not responding to requests."],
    [0x5D, "PICO_NO_CAPTURES_AVAILABLE",
     "There are no captures available and therefore no data can be returned."],
    [0x5E, "PICO_NOT_USED_IN_THIS_CAPTURE_MODE",
     "The capture mode the device is currently running in does not support " +
     "the current request."],
    [0x103, "PICO_GET_DATA_ACTIVE", "Reserved"],
    [0x104, "PICO_IP_NETWORKED", "The device is currently connected via " +
     "the IP Network socket and thus the call made is not supported."],
    [0x105, "PICO_INVALID_IP_ADDRESS", "An IP address that is not correct " +
     "has been passed to the driver."],
    [0x106, "PICO_IPSOCKET_FAILED", "The IP socket has failed."],
    [0x107, "PICO_IPSOCKET_TIMEDOUT", "The IP socket has timed out."],
    [0x108, "PICO_SETTINGS_FAILED", "The settings requested have failed to " +
     "be set."],
    [0x109, "PICO_NETWORK_FAILED", "The network connection has failed."],
    [0x10A, "PICO_WS2_32_DLL_NOT_LOADED", "Unable to load the WS2 dll."],
    [0x10B, "PICO_INVALID_IP_PORT", "The IP port is invalid."],
    [0x10C, "PICO_COUPLING_NOT_SUPPORTED",
     "The type of coupling requested is not supported on the opened device."],
    [0x10D, "PICO_BANDWIDTH_NOT_SUPPORTED",
     "Bandwidth limit is not supported on the opened device."],
    [0x10E, "PICO_INVALID_BANDWIDTH",
     "The value requested for the bandwidth limit is out of range."],
    [0x10F, "PICO_AWG_NOT_SUPPORTED",
     "The device does not have an arbitrary waveform generator."],
    [0x110, "PICO_ETS_NOT_RUNNING",
     "Data has been requested with ETS mode set but run block has not been " +
     "called, or stop has been called."],
    [0x111, "PICO_SIG_GEN_WHITENOISE_NOT_SUPPORTED",
     "White noise is not supported on the opened device."],
    [0x112, "PICO_SIG_GEN_WAVETYPE_NOT_SUPPORTED",
     "The wave type requested is not supported by the opened device."],
    [0x116, "PICO_SIG_GEN_PRBS_NOT_SUPPORTED",
     "Siggen does not generate pseudorandom bit stream."],
    [0x117, "PICO_ETS_NOT_AVAILABLE_WITH_LOGIC_CHANNELS",
     "When a digital port is enabled, ETS sample mode is not available for " +
     "use."],
    [0x118, "PICO_WARNING_REPEAT_VALUE", "Not applicable to this device."],
    [0x119, "PICO_POWER_SUPPLY_CONNECTED",
     "The DC power supply is connected."],
    [0x11A, "PICO_POWER_SUPPLY_NOT_CONNECTED",
     "The DC power supply is not connected."],
    [0x11B, "PICO_POWER_SUPPLY_REQUEST_INVALID",
     "Incorrect power mode passed for current power source."],
    [0x11C, "PICO_POWER_SUPPLY_UNDERVOLTAGE",
     "The supply voltage from the USB source is too low."],
    [0x11D, "PICO_CAPTURING_DATA",
     "The device is currently busy capturing data."],
    [0x11E, "PICO_USB3_0_DEVICE_NON_USB3_0_PORT",
     "You must connect the device to a USB 3.0 port, or call " +
     "ps4000aChangePowerSource to switch the device into " +
     "non-USB 3.0-power mode"],
    [0x11F, "PICO_NOT_SUPPORTED_BY_THIS_DEVICE",
     "A function has been called that is not supported by the current " +
     "device variant."],
    [0x120, "PICO_INVALID_DEVICE_RESOLUTION",
     "The device resolution is invalid (out of range)."],
    [0x121, "PICO_INVALID_NUMBER_CHANNELS_FOR_RESOLUTION",
     "The number of channels which can be enabled is limited in " +
     "15 and 16-bit modes"],
    [0x122, "PICO_CHANNEL_DISABLED_DUE_TO_USB_POWERED",
     "USB Power not sufficient to power all channels."]]