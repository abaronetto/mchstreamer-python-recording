import ctypes
import logging
import pyaudio

# Initialize custom logger for multiprocessing logging
process_logger = logging.getLogger('stream_setup')


# Define the Python wrapper will be used to call the C backend
def ALSA_py_error_handler(filename, line, function, err, fmt,arg):
    # Logging into the log file the warnings coming from portaudio library
    process_logger.warning('ALSA lib configuration error: file {} line {} function {} {}'
                           .format(filename, line, function, fmt))


def stream_set_up():
    asound = ctypes.cdll.LoadLibrary('/usr/lib/x86_64-linux-gnu/libportaudio.so.2')

    # Define our error handler type for this function call:
    # include/error.h:59:typedef void (*snd_lib_error_handler_t)(const char *file, int line,
    # const char *function, int err, const char *fmt, ...) /* __attribute__ ((format (printf, 5, 6))) */;
    # CFUNCTYPE is a factory; it creates "types" for callback functions
    # CFUNCTYPE arguments are types
    # 1. Return of the C function to which it points
    # (here void -> None)
    # 2. Inputs of the C function to which it points
    # (here char*, int, char*, int, char* -> c_char_p, c_int, c_char_p, c_int, c_char_p
    # 3. The pointer to the variadic argument list is passed as c_void_p

    ALSA_ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                                               ctypes.c_char_p, ctypes.c_void_p)

    # Create the C-callable callback ALSA_c_error_handler
    ALSA_c_error_handler = ALSA_ERROR_HANDLER_FUNC(ALSA_py_error_handler)

    # Set the C-side error handler; it will use the Python callback but is callable from C
    asound.snd_lib_error_set_handler(ALSA_c_error_handler)

    p_audio = pyaudio.PyAudio()

    # Get the index of the MCH Streamer
    num_devices = p_audio.get_device_count()  # Number of all available audio peripherals
    index = -1  # -1 means the variable INDEX is void
    for num_device in range(0, num_devices):
        # Look for the MCH Streamer in the list of audio peripheral. If MCH Streamer is present, then its information
        # are logged into the log file and the functions returns its index in the list
        if "MCHStreamer" in p_audio.get_device_info_by_index(num_device)['name']:  # Linux OS / TinkerOS
            process_logger.info('Streamer Board information: {}'.format(p_audio.get_device_info_by_index(num_device)))
            index = p_audio.get_device_info_by_index(num_device)['index']
            break

    return p_audio, index


