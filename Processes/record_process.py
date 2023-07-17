import subprocess
from Processes.stream_connection import *
from CustomExceptions.custom_handlers import *

# Initialize custom logger for multiprocessing logging
process_logger = logging.getLogger('record_process')

# Register handler for the SIGTERM signal
signal.signal(signal.SIGTERM, sigterm_handler)


def put_data_in_the_queue(data, q):
    q.put(data)


def audio_record(error_connection, que, audio_format, channels, rate, chunk):

    # Look for the audio peripheral to use for the recording
    p_audio, index_device = stream_set_up()

    # Define callback function which is called everytime new data from the sensors are available
    def callback(in_data, frame_count, time_info, status):
        put_data_in_the_queue(in_data, que)
        return in_data, pyaudio.paContinue

    try:
        if index_device != -1:  # If the MCH Streamer is connected then the audio recording starts

            # Open Streaming
            s = p_audio.open(format=audio_format, channels=channels, rate=rate, input=True,
                             input_device_index=index_device, frames_per_buffer=chunk, stream_callback=callback)

            process_logger.info('The device is going to record at {} Hz, using {} channels.'.format(rate, channels))
            process_logger.info('Start recording.')

            # The recording continues until the stream connection is active.
            # If the stream connection is not active (e.g. the Streamer board was disconnected), the record_process
            # is terminated by SIGSEGV signal (segmentation fault error), exit code 139
            while s.is_active() is True:
                continue

        # If the Streamer board is not connected then an exception is raised and propagated to all the processes
        if index_device == -1:
            error_connection.value = True
            raise StreamConnectionError

    # Recording finishes when SIGINT or SIGTERM signal are catched
    except KeyboardInterrupt:
        process_logger.info('Recording finished.')

    except OSError:
        # If there is a problem with the MCH Streamer, audio drivers are restarted to solve the problem
        process_logger.error('Problem with MCH Streamer connection: restarting the drivers.')
        command_line = subprocess.run(['pulseaudio', '-k'], universal_newlines=True, capture_output=True)
        process_logger.info('Kill pulseaudio processes. {}'.format(command_line.stdout))
        command_line = subprocess.run(['alsa', 'force-reload'], universal_newlines=True, capture_output=True)
        process_logger.info('Reload alsa packages. {}'.format(command_line.stdout))
        command_line = subprocess.run(['pulseaudio', '--start'], universal_newlines=True, capture_output=True)
        process_logger.info('Restart pulseaudio. {}'.format(command_line.stdout))

        # The exception is propagated to the other processes
        error_connection.value = True

    except StreamConnectionError:
        # If the Streamer board is not connecter (from the beginning), no stream connection is opened
        process_logger.error('MCH Streamer is not connected. No stream connection opened.')

    except SystemExit:
        pass

    finally:
        # Close streaming
        if index_device != -1:
            s.stop_stream()
            s.close()

        p_audio.terminate()
