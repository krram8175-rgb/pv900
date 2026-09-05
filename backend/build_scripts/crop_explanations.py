"""Crop the 'Explanation' section from examgoal practice screenshots and wire them
as solution_image for RE-NEET 2026 questions. Usage:
  python3 crop_explanations.py <src_dir> <start_qno>
Screenshots are matched in sorted (chronological) order -> start_qno, start_qno+1, ...
"""
import glob, os, sys, json
from PIL import Image
import numpy as np

IMG_DIR = "/app/backend/chapter_images"
OUT_JSON = "/app/backend/reexam_solutions.json"


def detect(im):
    a = np.array(im.convert('RGB')).astype(int)
    H, W, _ = a.shape
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    paleblue = (b > r + 10) & (b > 200) & (r > 165) & (g > 185) & (b - g > 4)

    def longest_run(row_mask):
        best = cur = 0
        for v in row_mask:
            if v:
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        return best

    runs = np.array([longest_run(paleblue[y]) for y in range(H)])
    solid = runs > 460
    header_top = None
    y = int(H * 0.05)
    while y < H - 20:
        if solid[y] and int(solid[y:y + 40].sum()) >= 18:
            header_top = y
            break
        y += 1
    if header_top is None:
        return None

    cnt = paleblue.sum(axis=1)
    y = header_top
    while y < H and cnt[y] > 200:
        y += 1
    content_start = y

    def is_note_row(yy):
        if not (80 < cnt[yy] < 480):
            return False
        xs = np.where(paleblue[yy])[0]
        return len(xs) > 0 and (xs.max() - xs.min()) < 480 and xs.max() > W * 0.55

    note_top = None
    yy = content_start + 30
    while yy < H - 25:
        if is_note_row(yy) and sum(1 for k in range(yy, min(H, yy + 30)) if is_note_row(k)) >= 22:
            note_top = yy
            break
        yy += 1
    bottom = (note_top - 14) if note_top else int(H * 0.985)
    return (int(W * 0.03), max(0, header_top - 10), int(W * 0.97), bottom)


def main():
    src, start = sys.argv[1], int(sys.argv[2])
    files = sorted(glob.glob(os.path.join(src, 'Screenshot_*.jpg')))
    data = json.load(open(OUT_JSON))
    by_no = {q['question_no']: q for q in data['questions']}
    done = 0
    for i, f in enumerate(files):
        qno = start + i
        box = detect(Image.open(f))
        if not box:
            print('WARN no header:', qno, os.path.basename(f)); continue
        name = f'rn2026_q{qno}-sol.png'
        Image.open(f).crop(box).save(os.path.join(IMG_DIR, name))
        if qno in by_no:
            by_no[qno]['solution_image'] = name
            done += 1
        print(qno, os.path.basename(f), 'h=', box[3] - box[1])
    json.dump(data, open(OUT_JSON, 'w'), ensure_ascii=False, indent=2)
    print('WROTE solution_image for', done, 'questions')


if __name__ == '__main__':
    main()
