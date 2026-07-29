"""Generate deterministic controlled MP4 fixtures; these are demos, not real CCTV samples."""
from pathlib import Path

import cv2
import numpy as np

OUT=Path(__file__).resolve().parents[1]/"demo-videos"

def blank(value=0):return np.full((120,160,3),value,dtype=np.uint8)
def save(name,frames):
    OUT.mkdir(exist_ok=True);writer=cv2.VideoWriter(str(OUT/name),cv2.VideoWriter_fourcc(*"mp4v"),5,(160,120))
    for frame in frames:writer.write(frame)
    writer.release()

def main():
    normal=[blank() for _ in range(12)]
    spill=[]
    for _ in range(6):
        frame=blank();cv2.ellipse(frame,(80,76),(42,18),0,0,360,(255,80,10),-1);spill.append(frame)
    blocked=[]
    for _ in range(6):
        frame=blank();cv2.rectangle(frame,(35,25),(125,105),(220,220,220),-1);blocked.append(frame)
    stocked=blank(220);depleted=blank()
    queue=[]
    for _ in range(6):
        frame=blank()
        for x in (35,70,105):cv2.circle(frame,(x,35),10,(230,230,230),-1);cv2.rectangle(frame,(x-8,45),(x+8,95),(230,230,230),-1)
        queue.append(frame)
    clear=[blank() for _ in range(8)]
    save("normal.mp4",normal);save("spill-hazard.mp4",spill+clear);save("blocked-aisle.mp4",blocked+clear);save("depleted-promo.mp4",[stocked]*3+[depleted]*6+[stocked]*8);save("queue.mp4",queue+clear)
    print(f"Generated controlled demos in {OUT}")

if __name__=="__main__":main()
