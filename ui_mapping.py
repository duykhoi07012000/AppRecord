import sys
import pyautogui
from MainUI import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow
import numpy as np
import cv2
import threading
import pyaudio
import wave
from moviepy.editor import AudioFileClip, VideoFileClip
import time

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.recording_screen = False
        self.recording_screen_thread = None
        self.out = None
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.screen_width, self.screen_height = pyautogui.size()

        self.recording_audio = False
        self.recording_audio_thread = None
        self.chunk = 1024  # Record in chunks of 1024 samples
        self.sample_format = pyaudio.paInt16  # 16 bits per sample
        self.channels = 2
        self.fs = 44100  # Record at 44100 samples per second
        # self.seconds = 3
        self.filename = "output_audio_recording.wav"
        self.p = None
        self.stream = None
        self.frames = []

        self.pushButton_start.clicked.connect(self.start_record_the_screen)
        self.pushButton_start.clicked.connect(self.start_record_the_audio)
        self.pushButton_stop.clicked.connect(self.stop_record)

    def start_record_the_screen(self):
        self.recording_screen = True
        self.out = cv2.VideoWriter(
            "output_screen_recording.avi",
            self.fourcc,
            60.0,
            (self.screen_width, self.screen_height)
        )
        self.pushButton_start.setEnabled(False)
        self.pushButton_stop.setEnabled(True)
        # Start recording video in a separate thread
        self.start_time = time.time()  # Record start time
        self.num_frames = 0  # Initialize frame counter
        self.recording_screen_thread = threading.Thread(target=self.record_screen)
        self.recording_screen_thread.start()

    def record_screen(self):
        while self.recording_screen:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            self.out.write(frame)
            self.num_frames += 1  # Increment frame counter

    def start_record_the_audio(self):
        self.recording_audio = True
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
                    format=self.sample_format,
                    channels=self.channels,
                    rate=self.fs,
                    frames_per_buffer=self.chunk,
                    input=True
        )
        self.frames = []
        self.recording_audio_thread = threading.Thread(target=self.record_audio)
        self.recording_audio_thread.start()

    def record_audio(self):
        while self.recording_audio:
            data = self.stream.read(self.chunk)
            self.frames.append(data)

    def stop_record(self):
        self.pushButton_start.setEnabled(True)
        self.pushButton_stop.setEnabled(False)
        self.recording_screen = False
        self.recording_screen_thread.join()
        self.out.release()
        self.recording_audio = False
        self.recording_audio_thread.join()
        self.save_audio()
        self.combine_audio_video()
    def save_audio(self):
        self.stream.stop_stream()
        self.stream.close()
        # Terminate the PortAudio interface
        self.p.terminate()
        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.sample_format))
        wf.setframerate(self.fs)
        wf.writeframes(b''.join(self.frames))
        wf.close()
    def combine_audio_video(self):
        video_clip = VideoFileClip("output_screen_recording.avi")
        audio_clip = AudioFileClip("output_audio_recording.wav")

        # Calculate the actual frame rate based on recorded frames and elapsed time
        actual_frame_rate = self.num_frames / (time.time() - self.start_time)

        final_clip = video_clip.set_audio(audio_clip)
        final_clip = final_clip.set_duration(audio_clip.duration)  # Adjust duration
        final_clip = final_clip.set_fps(actual_frame_rate)  # Set the calculated frame rate
        final_clip.write_videofile("output_video.mp4", codec="libx264")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())