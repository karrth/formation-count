
import os
# helps with gopro videos
os.environ['OPENCV_FFMPEG_READ_ATTEMPTS']="20000"

import subprocess
import sys
import cv2
import typer
import math
from datetime import timedelta
from typing_extensions import Annotated

class Point:

    def __init__(self, index: int, seq: str, fps: float, frame):
        self.index = index
        self.seq = seq
        self.fps = fps
        self.frame = frame

    def __str__(self):
        return f"Point({self.seq}/{str(self.timestamp)})"

    def __repr__(self):
        return self.__str__()

    @property
    def timestamp(self):
        return timedelta(seconds=self.index/self.fps)

class Result:

    def __init__(self, start: Point):
        self.points = [start]

    def __str__(self):
        return f"Result({self.start} -> {self.end} ({self.length.seconds} sec) : {self.count})"

    def __repr__(self):
        return self.__str__()

    @property
    def length(self):
        return self.end.timestamp-self.start.timestamp

    @property
    def start(self):
        return self.points[0]

    @property
    def end(self):
        return self.points[-1]

    @property
    def count(self):
        return len(self.points)

    def add(self, point: Point):
        self.points.append(point)

    def extract(self, filepath: str, buffer: int):

        #create a videoCapture Object (this allow to read frames one by one)
        print(f"Extracting from {filepath}")
        filename, file_ext = os.path.splitext(filepath)
        outfile = f"{filename}-points-{self.count}{file_ext}"

        start = str(timedelta(seconds=math.floor(self.start.timestamp.seconds-1)))
        end = str(timedelta(seconds=math.ceil(self.end.timestamp.seconds+1)))

        print(f"Saving extract to {outfile} from {start} to {end}")

        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-i", filepath,
                "-ss", str(start),
                "-to", str(end),
                "-c:v", "copy",
                outfile
            ]
        )

class Counter:

    def __init__(self, fps: float, window: int):
        self.points: list[Point] = []
        self.fps = fps
        self.window = window

    def add(self, index: int, seq: str, frame):
        point = Point(index, seq, self.fps, frame)
        print(point)
        self.points.append(point)

    def delete(self):
        self.points.pop()

    def calculate(self):
        results = []
        for index, point in enumerate(self.points):
            if point.seq == "start":
                results.append(self.find(Result(point), self.points[index+1:]))
        if len(results) == 0:
            print("No results found!")
            return
        final = results[0]
        for item in results:
            print(item)
            if item.count > final.count:
                final = item
        print(f"\nBest result: {final}")
        return final

    def find(self, result: Result, points: list[Point]):
        for point in points:
            if (point.timestamp - result.start.timestamp).seconds <= self.window:
                result.add(point)
            else:
                return result
        return result
            

def play(
    filepath: str,
    window: Annotated[int, typer.Option(help="Window in seconds")] = 35,
    buffer: Annotated[int, typer.Option(help="Seconds to buffer the video on either end")] = 1,
):

    #create a videoCapture Object (this allow to read frames one by one)
    video = cv2.VideoCapture(filepath)
    #check it's ok
    if not video.isOpened():
        print('Something went wrong check if the video name and path is correct')
        sys.exit(1)

    fps = video.get(cv2.CAP_PROP_FPS)
    print(f"FPS: {fps}")
    # frame index
    index = 0
    counter = Counter(fps, window)

    window_name = "Formation Counter"
    cv2.namedWindow(window_name)
    while video.isOpened():
        # read the frame
        success, frame = video.read()
        if not success: 
             print("Could not read the frame")   
             cv2.destroyWindow(window_name)
             break

        # show the frame
        cv2.imshow(window_name, frame)

        # catch user input
        waitKey = cv2.waitKey(15)

        # quit
        if waitKey == ord('q'):
            cv2.destroyWindow(window_name)
            video.release()
            break
        if waitKey == ord('s'):
            counter.add(index, "start", frame)
        if waitKey == ord('p'):
            counter.add(index, "point", frame)
        if waitKey == ord('d'):
            counter.delete()

        index+=1

    video.release()
    try:
        cv2.destroyWindow(window_name)
    except Exception:
        pass

    print(f"Total Video Points: {len(counter.points)}")
    result = counter.calculate()
    if result is None:
        return
    if result.length.seconds < 5:
        print("skipping video render, result is < 5 sec")
        return
    result.extract(filepath, buffer)


if __name__ == '__main__':
    typer.run(play)
