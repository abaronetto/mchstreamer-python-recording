"""
This code performs multichannel audio record and permutes the read frames, so that the output wav file is encrypted.
Since on the acquisition board a CHUNK size of 1024 will overflow the buffer, this code is implemented by using the
multiprocessing approach.
Another possible solution for overflow is increase the buffer size (2048 is fine).

Hardware: MCHStreamer Kit
Software: Windows OS / Ubuntu / TinkerOS
"""

import datetime
import multiprocessing
from ctypes import c_bool
from Processes.record_process import *
from Processes.save_process import *
from Processes.compress_process import *
from CustomExceptions.custom_handlers import *
from CustomLogging.clean_up_log import *

# Initialize custom logger for multiprocessing logging
process_logger = logging.getLogger('main_process')


if __name__ == '__main__':
    import logging.config
    import yaml
    import sys

    # Detect current working directory
    current_path = os.getcwd()

    clean_up(current_path)

    # Register handler for the SIGTERM signal
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Configure logger. Adding path where config file and custom logger class are stored
    sys.path.append(os.getcwd() + '/CustomLogging')
    formatter_path = os.getcwd() + '/CustomLogging/logging.yaml'
    if os.path.exists(formatter_path):
        with open(formatter_path) as f:
            config = yaml.load(f.read())
        logging.config.dictConfig(config)

    # Set parameters for recording
    RATE = 32000
    # RATE = int(p.get_device_info_by_index(1)['defaultSampleRate'])  # Sampling rate
    CHANNELS = 7  # Number of microphones (including Ref Mic)
    FORMAT = pyaudio.paInt16  # Format of data and size recorded is Int 16 bit
    FORMAT_SIZE = pyaudio.get_sample_size(FORMAT)
    CHUNK = 1024  # Frames per buffer

    # Create directory to save results
    path_results = current_path + '/Recordings' + '/AudioRecorded_' + str(
        datetime.datetime.today().strftime('on%d%b%Y_at%H.%M.%S'))

    try:
        # Check if the folder containing all audio data already exists. If not, it will be created
        if not os.path.exists(current_path + '/Recordings'):
            os.makedirs(current_path + '/Recordings')
            os.mkdir(path_results)
        else:
            os.mkdir(path_results)

    except OSError:
        # If the folder for the results is not created, the record does not start
        process_logger.error('Creation of the directory for the results failed.')
    else:

        try:
            # Initialize flags to handle the "Connection error" and "Disconnection error" events in the processes.
            # Default value is false (no error occurred)
            error_connection_flag = multiprocessing.Value(c_bool, False)
            disconnection_error_flag = multiprocessing.Value(c_bool, False)

            # Multiprocessing initialization
            q_frames = multiprocessing.Queue()  # queue where recorded frames (ready to be written) are put
            q_files = multiprocessing.Queue()  # queue where filenames of wav files (ready to be compressed) are put
            record_process = multiprocessing.Process(name='record', target=audio_record, args=(error_connection_flag,
                                                                                               q_frames, FORMAT,
                                                                                               CHANNELS, RATE, CHUNK))
            save_process = multiprocessing.Process(name='save', target=save_data, args=(error_connection_flag,
                                                                                        disconnection_error_flag,
                                                                                        q_frames, q_files, CHANNELS,
                                                                                        FORMAT_SIZE, RATE, CHUNK,
                                                                                        path_results))
            compress_process = multiprocessing.Process(name='compress', target=compress_data,
                                                       args=(error_connection_flag, disconnection_error_flag, q_files,
                                                             path_results))

            # Start the processes
            record_process.start()
            save_process.start()
            compress_process.start()

            # The main process check periodically if the processes are still running
            while record_process.is_alive() is True and save_process.is_alive() is True \
                    and compress_process.is_alive() is True:
                continue

            # Check if processes ended because of MCH not connected (from the beginning)
            if error_connection_flag.value is True:
                raise StreamConnectionError

            # Check if one of the processes ended with errors (exit code != 0). Usually it happens when the streamer
            # board is disconnected during the recording. If one the processes ended with errors, the others are
            # terminated raising an exception
            if record_process.exitcode != 0 or save_process.exitcode != 0 or compress_process.exitcode != 0:
                disconnection_error_flag.value = True
                raise DisconnectionError

        # Exceptions handling
        except KeyboardInterrupt:
            # If the program was interrupted by SIGINT or SIGTERM signal, the main process waits the processes to
            # complete and then terminates
            record_process.join()
            save_process.join()
            compress_process.join()

            # Move log file to the data folder
            subprocess.run(['mv', 'audio_record.log', path_results])

        except (OSError, StreamConnectionError):
            # If any errors happens due to errors in the streaming set up,
            # log file is stored under the 'Failed run' folder
            try:
                if not os.path.exists(current_path + '/Failed'):
                    os.makedirs(current_path + '/Failed')
                    os.rename('audio_record.log',
                              'audio_record_' + datetime.datetime.today().strftime('on%d%b%Y_at%H.%M.%S') + '.log')
                    subprocess.run(
                        ['mv', 'audio_record_' + datetime.datetime.today().strftime('on%d%b%Y_at%H.%M.%S') + '.log',
                         current_path + '/Failed'])
                else:
                    os.rename('audio_record.log',
                              'audio_record_' + datetime.datetime.today().strftime('on%d%b%Y_at%H.%M.%S') + '.log')
                    subprocess.run(
                        ['mv', 'audio_record_' + datetime.datetime.today().strftime('on%d%b%Y_at%H.%M.%S') + '.log',
                         current_path + '/Failed'])

                record_process.join()
                save_process.join()
                compress_process.join()

            except OSError:
                process_logger.error('Creation of the directory for logs of failed run failed.')

        except DisconnectionError:
            # If the board looses connection with the sensors, all the processes terminate. The recorded data are
            # stored in the "Recordings" folder
            if save_process.is_alive():
                save_process.join()
            if compress_process.is_alive():
                compress_process.join()

            process_logger.error('An unexpected error happened. Check connection with MCH Streamer. '
                                 'Has it been disconnected?')
            subprocess.run(['mv', 'audio_record.log', path_results])

        except SystemExit:
            process_logger.info('The system is shutting down.')
            # Move log file to the data folder
            subprocess.run(['mv', 'audio_record.log', path_results])

            record_process.terminate()
            save_process.terminate()
            compress_process.terminate()
