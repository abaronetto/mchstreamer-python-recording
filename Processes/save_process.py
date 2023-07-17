import wave
import os
import logging
from CustomExceptions.custom_handlers import *

# Initialize custom logger for multiprocessing logging
process_logger = logging.getLogger('save_process')

# Register handler for the SIGTERM signal
signal.signal(signal.SIGTERM, sigterm_handler)


def save_data(connection_error, disconnection_error, que1, que2, channels, format_size, rate, chunk, path):

    try:
        # Filename creation for partial data. Every minute one .wav file is saved
        n_file = 1
        filename = path + '/audio data minute ' + str(n_file)

        # Queue and Stream initialization
        record_seconds = 60  # Every 60 seconds data are saved
        frames_per_window = int(rate / chunk * record_seconds)  # Number of frames per window of observation
        frames_collected = 0  # Number of frames that have been collected

        # Open wav file and set it up
        w = wave.open(filename + '.wav', 'wb')
        w.setnchannels(channels)
        w.setsampwidth(format_size)
        w.setframerate(rate)

        # If the MCH Streamer is not connected, then the recording does not start
        while connection_error.value is False and disconnection_error.value is False:
            # Frames are extracted from the queue and written in the .wav file
            if not que1.empty():
                if frames_collected < frames_per_window:
                    received_frame = que1.get()
                    w.writeframes(received_frame)
                    frames_collected += 1
                else:
                    # When the frames are collected, they are saved in the .wav file
                    frames_collected = 0
                    # Close the file
                    w.close()

                    # Send the filename to to the next process to be compressed
                    que2.put(filename)
                    n_file += 1

                    # Open a new file
                    filename = path + '/audio data minute ' + str(n_file)  # update filename
                    w = wave.open(filename + '.wav', 'wb')
                    w.setnchannels(channels)
                    w.setsampwidth(format_size)
                    w.setframerate(rate)

        # If the MCH Streamer is not connected (from the beginning)
        if connection_error.value is True:
            raise StreamConnectionError

        # If the Streamer board was disconnected during the recording or the stream connection was interrupted
        if disconnection_error.value is True:
            raise DisconnectionError

    except (KeyboardInterrupt, DisconnectionError):
        # If SIGINT or SIGTERM signal occurred or the connection was interrupted, the process completes the ongoing
        # tasks and terminates.

        # If the observed window is not empty, left frames are permuted and
        # the saved, even if the number is < target
        while not que1.empty():
            received_frame = que1.get()
            w.writeframes(received_frame)
            que2.put(filename)
            process_logger.info('Data are stored in the directory %s' % path)

    except StreamConnectionError:
        # If the MCH Streamer is not well connected at the beginning, the process terminates and
        #  the .wav file is not saved
        os.remove(filename + '.wav')
        process_logger.error('Stream connection error: no audio data were saved.')

    except SystemExit:
        # If SIGINT or SIGTERM signal occurred or the connection was interrupted, the process completes the ongoing
        # tasks and terminates.
        pass

    finally:
        # Close .wav file
        w.close()
