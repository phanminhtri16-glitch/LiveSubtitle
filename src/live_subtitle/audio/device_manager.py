import pyaudiowpatch as pyaudio
from src.live_subtitle.utils.logger import logger

def get_default_loopback_device(p: pyaudio.PyAudio | None = None) -> dict | None:
    """
    Finds and returns the WASAPI loopback device corresponding to the default
    playback device (Speakers/Headphones).
    """
    owns_p = False
    if p is None:
        p = pyaudio.PyAudio()
        owns_p = True

    try:
        try:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            logger.warning("WASAPI host API not found on this system.")
            return None

        default_output_index = wasapi_info.get("defaultOutputDevice")
        if default_output_index is None or default_output_index < 0:
            logger.warning("No default WASAPI output device found.")
            return None

        default_speakers = p.get_device_info_by_index(default_output_index)

        # If already a loopback device, return it
        if default_speakers.get("isLoopbackDevice", False):
            return default_speakers

        # Match loopback device name with default speaker name
        speaker_name = default_speakers.get("name", "")
        for loopback in p.get_loopback_device_info_generator():
            if speaker_name in loopback.get("name", ""):
                logger.info(f"Matched WASAPI loopback device: {loopback['name']}")
                return loopback

        # Fallback: return the first available loopback device
        for loopback in p.get_loopback_device_info_generator():
            logger.info(f"Fallback to first WASAPI loopback device: {loopback['name']}")
            return loopback

        logger.warning("No WASAPI loopback devices available.")
        return None
    except Exception as e:
        logger.error(f"Error querying WASAPI loopback device: {e}")
        return None
    finally:
        if owns_p:
            p.terminate()

def list_output_devices() -> list[dict]:
    """
    Lists all available output render endpoints under WASAPI.
    """
    p = pyaudio.PyAudio()
    devices = []
    try:
        try:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            return devices

        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if (
                dev.get("hostApi") == wasapi_info["index"]
                and dev.get("maxOutputChannels", 0) > 0
                and not dev.get("isLoopbackDevice", False)
            ):
                devices.append(dev)
    except Exception as e:
        logger.warning(f"Error enumerating output devices: {e}")
    finally:
        p.terminate()
    return devices
