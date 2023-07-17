import subprocess
import os
import logging
from CustomExceptions.custom_handlers import *

# Initialize custom logger for multiprocessing logging
process_logger = logging.getLogger('compression_process')

# Register handler for the SIGTERM signal
signal.signal(signal.SIGTERM, sigterm_handler)


def compress_data(connection_error, disconnection_error, que, path):

    try:
        # Creation of zip file
        stored_data = path + '/data.zip'

        # If the MCH Streamer is not connected, then the recording does not start
        while connection_error.value is False and disconnection_error.value is False:
            if not que.empty():
                # If a file is available, then it is compressed and the original copy is deleted
                data_to_compress = que.get()
                args = [stored_data, data_to_compress + '.wav']
                command_line = subprocess.run(['zip', '-j', '-m', '-9', args[0], args[1]], universal_newlines=True,
                                              capture_output=True)
                process_logger.info('Data {}'.format(command_line.stdout[2:-1]))

        # If the MCH Streamer is not connected (from the beginning)
        if connection_error.value is True:
            raise StreamConnectionError

        # If the Streamer board was disconnected during the recording or the stream connection was interrupted
        if disconnection_error.value is True:
            raise DisconnectionError

    except (KeyboardInterrupt, DisconnectionError):
        # If SIGINT or SIGTERM signal occurred or the connection was interrupted, the process completes the ongoing
        # tasks and terminates.

        # Compressing the last .wav file
        command_line = subprocess.run(['zip', '-j', '-r', '-m', '-9', stored_data, path], universal_newlines=True,
                                      capture_output=True)
        process_logger.info('Data {}'.format(command_line.stdout[2:-1]))

    except StreamConnectionError:
        # If MCH Streamer is not connected at the beginning, than the folder for storing data is removed
        # (it would be empty)
        if os.path.exists(path):
            subprocess.run(['rm', '-r', path])
        process_logger.error('Stream connection error: no data to compress.')

    except SystemExit:
        pass
