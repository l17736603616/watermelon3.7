#!/usr/bin/env python3
"""
水印替换程序 v3.7
────────────────────────────────────────────────────────────────
v3.3 修复说明：
  v3.2 的问题：顶部/底部替换图是"预先画好文字的固定图片"，程序检测到原图
  水印框的尺寸后，直接把这张固定图片【强制拉伸】塞进框里。
  如果原始照片里的单位名/标题是一行（框很矮），换成新单位名后文字变成了
  两行（因为新图片本来就是按两行画的），两行内容被硬压扁进一行的高度里，
  看起来就是文字挤在一起、边框"装不下"内容、视觉上很扭曲（用户反馈的
  "边框还是突出来了"）。

  v3.3 改动：不再使用预先画好文字的整张图。而是：
    1. 只从 header 图里【裁出 logo 部分】（左侧白底logo+小标题），按原始比例
       缩放，不再拉伸变形。
    2. 标题 / 维保单位 文字改为【实时绘制】，并自动收缩字号，
       优先保证单行显示；如果实在太长单行放不下，再自动换成两行，
       并重新计算合适的字号，保证两行也能完整地待在检测到的框高度内，
       不会再出现挤压变形或文字超框的问题。

v3.4 修复说明：
  v3.3 把 --site/--unit 设成了命令行必填参数，导致最常用的"把图片拖到
  exe图标上"或"双击运行"完全用不了（拖拽时没办法附加命令行参数）。

  v3.4 改动：新增 config.txt 配置文件（放在程序/exe同目录）：
    site=顶部标题
    unit=维保单位
  双击运行或拖拽图片时会自动读取这个文件；命令行传 --site/--unit 时
  优先用命令行的值。首次运行如果没有配置文件，会自动生成一个模板并
  提示去填写，而不是直接报错退出。

v3.5 修复说明：
  find_card_and_regions() 检测顶部蓝色标题条时有两个边界情况没处理好：
    1. 检测过长：为了把 logo 白底框也框进去，原代码会从蓝色条顶部往上
       逐行探测"是否够亮"，但没设上限。如果蓝色条上方刚好是浅色背景
       （水泥地、白墙/立柱等），探测会一路走到搜索区域顶部，把背景误判
       成水印的一部分，导致新水印的蓝色标题条比原图异常变长，往上侵入
       照片内容。
    2. 检测过短：判断"是不是蓝色"是逐行统计蓝色像素占比，标题文字笔画
       密集处可能让某一行的占比短暂跌破阈值，把本应连续的一整条蓝色区
       域错误切成好几段，而代码只取了第一段，导致检测框比实际标题矮一
       截，新文字超出框外显示不全。

  v3.5 改动：
    1. 删除了那段没有上限的"向上探测扩展"逻辑（蓝色条顶部本身已经测得
       足够准确，不需要再额外扩展）。
    2. 切分出多段候选蓝色区域后，新增一步小间隙合并：相邻两段之间的
       间隔如果很小（远小于标题区和维保单位区之间的正常间隔），就认为
       是同一条被噪声切断了，自动合并回一段。

v3.6 修复说明：
  v3.5 修完标题条"高度"忽长忽短后，又发现"宽度"也会出问题：原代码用
  亮度+低饱和度判断"是否是卡片的一部分"来确定卡片的左右边界，但照片
  里有些背景物体（人物衣领、肤色、白色机柜门等）刚好也满足"亮、纯色"
  的条件，且恰好紧贴在卡片右侧、处于跟标题条/维保单位条同一高度，于是
  被错误地并入了卡片范围，导致新水印的蓝色条右边缘比卡片实际宽度宽出
  一截，看起来像是"凸出来了"，跟中间未被替换的灰色信息行右边缘对不齐。

  v3.6 改动：不再用宽泛的"亮度+低饱和度"来判断标题条/维保单位条各自
  精确的右边界，而是在它们各自所在的垂直范围内，单独用更可靠的蓝色
  通道差异信号（b-r>40）逐列扫描，取蓝色占比最后一次超过阈值的列作为
  右边界。蓝色背景物体的颜色绝大多数情况下不会同时满足"够蓝"这个更
  严格的条件，因此不会再被背景的浅色衣领/机柜/肤色误判牵连进去。

v3.7 修复说明：
  v3.6 解决了背景物体被误判进卡片范围的问题，但又发现了同类问题的另一
  种表现：左边界检测代码本身就有缺陷——它是直接取"所有亮度满足条件的
  列"里最左和最右的那个（np.where 后取首尾），完全没有检查这些列是否
  连续。如果照片最左侧边缘正好有一列因渐晕、反光等原因偶然也满足"够
  亮"的条件（哪怕紧挨着它的几十像素完全不满足，跟真正的卡片之间隔着
  一段明显的暗区），这一个孤立的噪声列也会被直接当成卡片左边界，导致
  新水印的整条边比卡片实际宽度多出一截，看起来像是凸出来了。

  v3.7 改动：列方向的边界检测也改用跟行方向（卡片整体高度判定）一样的
  "连续区段(run)+合并"逻辑，只取其中最长的连续段作为卡片左右边界，不
  再被孤立的噪声列误导。

依赖：pip install Pillow numpy
用法：
  python watermark_replacer.py photo.jpg --site "中国农业银行北方数据中心" --unit "同方泰德国际科技（北京）有限公司"
  python watermark_replacer.py *.jpg --site "..." --unit "..." -o ./my_output

也可以不传 --site/--unit，直接编辑同目录下的 config.txt，然后双击程序
或把图片拖到程序图标上即可。
────────────────────────────────────────────────────────────────
"""

import sys, os, glob, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# exe 打包后 sys.executable 指向 exe 本身，脚本运行时用 __file__
if getattr(sys, "frozen", False):
    _DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    _DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_HEADER = os.path.join(_DIR, "header_tongfangtaider.jpg")
DEFAULT_BAR    = os.path.join(_DIR, "bar_tongfangtaider.jpg")
DEFAULT_OUT    = os.path.join(_DIR, "output")
CONFIG_PATH    = os.path.join(_DIR, "config.txt")

BLUE = (22, 110, 253)        # 品牌蓝（从原素材图采样得到）
WHITE_TEXT = (255, 255, 255)

# 常见中文字体候选路径（Windows / Linux），找不到就报错提示用户用 --font 指定
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",   # 微软雅黑 Bold（Windows 常见）
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",   # 黑体
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def resolve_font(font_arg):
    candidates = ([font_arg] if font_arg else []) + FONT_CANDIDATES
    for p in candidates:
        if p and os.path.exists(p):
            return p
    print("错误：找不到可用的中文字体文件，请用 --font 指定一个 .ttf/.ttc 路径")
    pause_if_frozen()
    sys.exit(1)


def pause_if_frozen():
    """打包成exe后，如果是双击运行（没有命令行参数），出错/结束时窗口会一闪而过看不到提示。
    这里在exe模式下暂停等用户按回车，命令行/脚本调用时不受影响。"""
    if getattr(sys, "frozen", False):
        try:
            input("\n按回车键关闭窗口...")
        except Exception:
            pass


def load_config():
    """读取程序所在目录下的 config.txt（site=xxx / unit=xxx），用于双击或拖拽运行时
    不需要在命令行里输入 --site/--unit。命令行参数优先级更高，传了就会覆盖配置文件。"""
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg


def write_config_template():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write("# 在下面填好标题和维保单位并保存，以后双击程序或把图片拖到程序图标上即可自动使用。\n")
        f.write("# 命令行传了 --site / --unit 时，会优先用命令行的值，忽略这里的设置。\n")
        f.write("site=请将此处改成顶部标题，例如：中国农业银行北方数据中心\n")
        f.write("unit=同方泰德国际科技（北京）有限公司\n")


# ════════════════════════════════════════════════════════════════
# 检测（与 v3.2 相同，负责定位 header_box / bar_box 的位置和尺寸）
# ════════════════════════════════════════════════════════════════

def find_card_and_regions(arr, w, h):
    """
    1. 检测半透明白色/蓝色卡片块（整个水印区域）
    2. 在卡片内找顶部蓝色区和底部蓝色区
    返回 (header_box, bar_box)，均为 (x1,y1,x2,y2)
    """
    search_x2 = int(w * 0.65)
    search_y1 = int(h * 0.50)

    card_rows = []
    for y in range(search_y1, h):
        row = arr[y, 5:search_x2].astype(float)
        r, g, b = row[:,0], row[:,1], row[:,2]
        mn = np.minimum(np.minimum(r,g),b)
        mx = np.maximum(np.maximum(r,g),b)
        mask = ((mn > 130) & (mx-mn < 70)) | \
               ((b-r > 25) & (mn > 100))   | \
               ((b-r > 60) & (b > 150))
        if mask.mean() > 0.40:
            card_rows.append(y)

    if not card_rows:
        return None, None

    runs, s = [], card_rows[0]
    for i in range(1, len(card_rows)):
        if card_rows[i] - card_rows[i-1] > 30:
            runs.append((s, card_rows[i-1]))
            s = card_rows[i]
    runs.append((s, card_rows[-1]))

    merged = [list(runs[0])]
    for r in runs[1:]:
        if r[0] - merged[-1][1] < 50:
            merged[-1][1] = r[1]
        else:
            merged.append(list(r))

    cy1, cy2 = max(merged, key=lambda r: r[1]-r[0])
    if cy2 - cy1 < h * 0.05:
        return None, None

    col_scores = []
    for x in range(0, search_x2):
        col = arr[cy1:cy2, x].astype(float)
        r, g, b = col[:,0], col[:,1], col[:,2]
        mn = np.minimum(np.minimum(r,g),b)
        mx = np.maximum(np.maximum(r,g),b)
        mask = ((mn > 130) & (mx-mn < 70)) | \
               ((b-r > 25) & (mn > 100))   | \
               ((b-r > 60) & (b > 150))
        col_scores.append(mask.mean())
    col_scores = np.array(col_scores)
    light_cols = np.where(col_scores > 0.35)[0]
    if len(light_cols) == 0:
        return None, None

    # 跟行方向(card_rows)一样做 runs+merge，取最长的连续段作为卡片左右
    # 边界，而不是粗暴取全局最左/最右匹配列。原来的写法对孤立的噪声列
    # （比如照片边缘渐晕、反光导致某一列单独超过阈值，但左右两侧紧邻
    # 的几十像素完全不匹配）没有任何防护，会把这种孤立噪声点误当成
    # 边界，跟真正连续的卡片主体之间隔着一段明显的空隙也不会被发现。
    col_runs, cs = [], int(light_cols[0])
    for i in range(1, len(light_cols)):
        if light_cols[i] - light_cols[i-1] > 30:
            col_runs.append((cs, int(light_cols[i-1])))
            cs = int(light_cols[i])
    col_runs.append((cs, int(light_cols[-1])))

    col_merged = [list(col_runs[0])]
    for r in col_runs[1:]:
        if r[0] - col_merged[-1][1] < 50:
            col_merged[-1][1] = r[1]
        else:
            col_merged.append(list(r))

    cx1, cx2 = max(col_merged, key=lambda r: r[1]-r[0])
    cx2 += 1

    blue_zones = []
    in_blue, zone_s = False, None
    for y in range(cy1, cy2):
        row = arr[y, cx1:cx2].astype(int)
        blue_r = np.mean(row[:,2] - row[:,0] > 40)
        is_blue = blue_r > 0.35
        if is_blue and not in_blue:
            zone_s = y
            in_blue = True
        elif not is_blue and in_blue:
            blue_zones.append((zone_s, y))
            in_blue = False
    if in_blue and zone_s:
        blue_zones.append((zone_s, cy2))

    if not blue_zones:
        return None, None

    # 合并间隔很小的相邻蓝色区域：标题文字笔画密集处可能导致单行蓝色像素占比
    # 短暂跌破阈值，把本应连续的一段蓝色条错误切分为多段；而header与bar之间
    # 的合法间隔（中部灰色信息行）远大于此阈值，不会被误合并。
    gap_thresh = max(40, int(h * 0.015))
    merged_zones = [list(blue_zones[0])]
    for z in blue_zones[1:]:
        if z[0] - merged_zones[-1][1] < gap_thresh:
            merged_zones[-1][1] = z[1]
        else:
            merged_zones.append(list(z))
    blue_zones = merged_zones

    if len(blue_zones) < 2:
        return None, None

    top_y1, top_y2 = blue_zones[0]
    bot_y1, bot_y2 = blue_zones[-1]

    def blue_right_edge(y1, y2, x_lo, x_hi, thresh=0.5):
        """在 y1:y2 这一段精确的蓝色条范围内，逐列扫描蓝色通道差异
        (b-r>40) 占比，返回最靠右的"够蓝"列+1，作为这一条的精确右边界。
        蓝色是比亮度更可靠的信号：背景里浅色的衣领、肤色、白墙、机柜等
        物体经常和半透明卡片的亮度/低饱和度特征重叠，但极少会同时满足
        "强烈偏蓝"，所以不会像整体列扫描那样被背景误判拉宽。"""
        right = x_lo
        for x in range(x_lo, x_hi):
            col = arr[y1:y2, x].astype(int)
            if np.mean(col[:, 2] - col[:, 0] > 40) > thresh:
                right = x
        return right + 1

    header_cx2 = blue_right_edge(top_y1, top_y2, cx1, cx2)
    bar_cx2 = blue_right_edge(bot_y1, bot_y2, cx1, cx2)
    cx2_fixed = max(header_cx2, bar_cx2)
    # 蓝色信号本身没扫描到任何东西（理论上不该发生）时保底退回原结果，
    # 避免比修复前更差
    if cx2_fixed - cx1 < (cx2 - cx1) * 0.3:
        cx2_fixed = cx2

    header_box = (cx1, top_y1, cx2_fixed, top_y2)
    bar_box = (cx1, bot_y1, cx2_fixed, bot_y2)

    return header_box, bar_box


# ════════════════════════════════════════════════════════════════
# 素材：从 header 图裁出 logo（保持比例，不再整张拉伸）
# ════════════════════════════════════════════════════════════════

def extract_logo(header_img):
    """从 header_tongfangtaider.jpg 中裁出左侧白底 logo 部分（白色→蓝色的分界列）"""
    arr = np.array(header_img.convert("RGB"))
    h, w = arr.shape[:2]
    y = h // 2
    row = arr[y].astype(int)
    is_white = np.minimum(np.minimum(row[:,0],row[:,1]),row[:,2]) > 200
    is_blue  = (row[:,2] - row[:,0] > 60)
    edge = None
    for x in range(w-1):
        if is_white[x] and is_blue[x+1]:
            edge = x+1
            break
    if edge is None:
        edge = int(w*0.23)  # 兜底：按经验比例
    return header_img.crop((0, 0, edge, h))


# ════════════════════════════════════════════════════════════════
# 动态文字渲染：自动收缩字号，优先单行，单行放不下再换行
# ════════════════════════════════════════════════════════════════

def _text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2]-bbox[0], bbox[3]-bbox[1], bbox[1]

def fit_text_lines(draw, text, max_w, max_h, font_path, max_size=300, min_size=14):
    """
    先尝试单行：从大到小找一个字号，使单行宽度<=max_w 且高度<=max_h。
    如果字号缩到 min_size 单行仍然超宽，则二分尝试把文字拆成两行
    （按字符数对半拆，中文不依赖空格），再找一个能让两行都不超宽、
    且两行总高（含行间距）不超过 max_h 的字号。
    返回 (font, lines, line_height)
    """
    size = max_size
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        tw, th, _ = _text_size(draw, text, font)
        if tw <= max_w and th <= max_h:
            return font, [text], th
        size -= 2

    # 单行放不下，尝试两行（按字符数从中间往两边找一个较均衡的断点）
    n = len(text)
    if n < 2:
        font = ImageFont.truetype(font_path, min_size)
        return font, [text], _text_size(draw, text, font)[1]

    best = None
    for split in range(max(1, n//2 - 4), min(n-1, n//2 + 5)):
        l1, l2 = text[:split], text[split:]
        size = max_size
        while size >= min_size:
            font = ImageFont.truetype(font_path, size)
            w1, h1, _ = _text_size(draw, l1, font)
            w2, h2, _ = _text_size(draw, l2, font)
            line_gap = int(size * 0.25)
            total_h = h1 + h2 + line_gap
            if w1 <= max_w and w2 <= max_w and total_h <= max_h:
                cand = (size, l1, l2, font, h1, h2, line_gap)
                if best is None or cand[0] > best[0]:
                    best = cand
                break
            size -= 2

    if best is None:
        # 实在放不下：用最小字号硬两行（极端长名称兜底，至少不会比v3.2更差）
        split = n // 2
        font = ImageFont.truetype(font_path, min_size)
        return font, [text[:split], text[split:]], _text_size(draw, text[:split], font)[1]

    size, l1, l2, font, h1, h2, line_gap = best
    return font, [l1, l2], (h1, h2, line_gap)


def render_header(box_w, box_h, logo_img, title_text, font_path):
    img = Image.new("RGB", (box_w, box_h), BLUE)
    # logo 保持原始比例缩放（按目标高度），不拉伸变形
    logo_w = max(1, int(logo_img.width * box_h / logo_img.height))
    logo_resized = logo_img.resize((logo_w, box_h), Image.LANCZOS)
    img.paste(logo_resized, (0, 0))

    draw = ImageDraw.Draw(img)
    pad_x = max(10, int(box_w * 0.015))
    text_x0 = logo_w + pad_x
    max_w = box_w - text_x0 - pad_x
    max_h = int(box_h * 0.82)

    font, lines, hinfo = fit_text_lines(draw, title_text, max_w, max_h, font_path)

    if len(lines) == 1:
        tw, th, off = _text_size(draw, lines[0], font)
        y = (box_h - th) // 2 - off
        draw.text((text_x0, y), lines[0], font=font, fill=WHITE_TEXT)
    else:
        h1, h2, gap = hinfo
        total = h1 + h2 + gap
        y0 = (box_h - total) // 2
        _, _, off1 = _text_size(draw, lines[0], font)
        _, _, off2 = _text_size(draw, lines[1], font)
        draw.text((text_x0, y0 - off1), lines[0], font=font, fill=WHITE_TEXT)
        draw.text((text_x0, y0 + h1 + gap - off2), lines[1], font=font, fill=WHITE_TEXT)
    return img


def render_bar(box_w, box_h, text, font_path):
    img = Image.new("RGB", (box_w, box_h), BLUE)
    draw = ImageDraw.Draw(img)
    pad_x = max(10, int(box_w * 0.012))
    max_w = box_w - pad_x * 2
    max_h = int(box_h * 0.86)

    font, lines, hinfo = fit_text_lines(draw, text, max_w, max_h, font_path)

    if len(lines) == 1:
        tw, th, off = _text_size(draw, lines[0], font)
        y = (box_h - th) // 2 - off
        draw.text((pad_x, y), lines[0], font=font, fill=WHITE_TEXT)
    else:
        h1, h2, gap = hinfo
        total = h1 + h2 + gap
        y0 = (box_h - total) // 2
        _, _, off1 = _text_size(draw, lines[0], font)
        _, _, off2 = _text_size(draw, lines[1], font)
        draw.text((pad_x, y0 - off1), lines[0], font=font, fill=WHITE_TEXT)
        draw.text((pad_x, y0 + h1 + gap - off2), lines[1], font=font, fill=WHITE_TEXT)
    return img


# ════════════════════════════════════════════════════════════════
# 单图处理
# ════════════════════════════════════════════════════════════════

def process_image(input_path, output_path, logo_img, site_text, unit_text, font_path):
    try:
        img = Image.open(input_path).convert("RGB")
        arr = np.array(img)
        w, h = img.size
        print(f"  尺寸: {w}×{h}")

        header_box, bar_box = find_card_and_regions(arr, w, h)

        if header_box is None:
            print("  ⚠ 未检测到顶部水印区域，跳过")
            return False
        if bar_box is None:
            print("  ⚠ 未检测到底部水印区域，跳过")
            return False

        hx1,hy1,hx2,hy2 = header_box
        bx1,by1,bx2,by2 = bar_box
        print(f"  顶部: ({hx1},{hy1})-({hx2},{hy2})  {hx2-hx1}×{hy2-hy1}px")
        print(f"  底部: ({bx1},{by1})-({bx2},{by2})  {bx2-bx1}×{by2-by1}px")

        header_img = render_header(hx2-hx1, hy2-hy1, logo_img, site_text, font_path)
        bar_img    = render_bar(bx2-bx1, by2-by1, unit_text, font_path)

        out = img.copy()
        out.paste(header_img, (hx1, hy1))
        out.paste(bar_img,    (bx1, by1))

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        out.save(output_path, quality=95)
        print(f"  ✓ {output_path}")
        return True

    except Exception as e:
        import traceback
        print(f"  ✗ 失败: {e}")
        traceback.print_exc()
        return False


# ════════════════════════════════════════════════════════════════
# 主程序
# ════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="同方泰德水印替换工具 v3.7（支持 config.txt 配置，双击/拖拽即可用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python watermark_replacer.py photo.jpg --site "中国农业银行北方数据中心" --unit "同方泰德国际科技（北京）有限公司"
  python watermark_replacer.py *.jpg --site "..." --unit "..." -o ./my_output

也可以不传 --site/--unit，直接编辑程序所在目录下的 config.txt 后双击运行，
或把图片/文件夹直接拖到 exe 图标上。
        """)
    parser.add_argument("inputs",            nargs="*",              help="输入图片（支持 *.jpg 通配符，也可以拖拽到exe图标上）")
    parser.add_argument("-o","--output-dir", default=DEFAULT_OUT,    help="输出目录（默认: ./output）")
    parser.add_argument("--suffix",          default="",             help="文件名后缀")
    parser.add_argument("--header",          default=DEFAULT_HEADER, help="顶部素材图（仅用于裁出logo，标题文字请用--site指定）")
    parser.add_argument("--bar",             default=DEFAULT_BAR,    help="（v3.3起不再使用，保留兼容旧参数）")
    parser.add_argument("--site",            default=None,           help="顶部标题文字，不传则读取 config.txt 里的 site=")
    parser.add_argument("--unit",            default=None,           help="维保单位文字，不传则读取 config.txt 里的 unit=（不用加“维保单位：”前缀）")
    parser.add_argument("--font",            default=None,           help="中文字体文件路径(.ttf/.ttc)，不传则自动从常见路径里找")
    args = parser.parse_args()

    cfg = load_config()
    site = args.site or cfg.get("site")
    unit = args.unit or cfg.get("unit")

    if not site or not unit or site.startswith("请将此处") or "请填写" in (site or ""):
        if not os.path.exists(CONFIG_PATH):
            write_config_template()
        print("提示：还没有设置顶部标题(site)和维保单位(unit)。")
        print(f"已在程序所在目录生成配置文件：{CONFIG_PATH}")
        print("请用记事本打开它，把 site= 和 unit= 后面改成你需要的文字并保存，")
        print("然后重新双击程序，或把图片拖到程序图标上即可（也可以用 --site/--unit 命令行参数）。")
        pause_if_frozen()
        sys.exit(1)

    EXT = {".jpg",".jpeg",".png",".bmp",".webp"}
    files = []
    for p in args.inputs:
        matched = glob.glob(p)
        files.extend(matched if matched else ([p] if os.path.isfile(p) else []))
    files = [f for f in files if os.path.splitext(f)[1].lower() in EXT]

    if not files:
        print("错误：没有找到有效图片。")
        print("请把图片文件直接拖到本程序的图标上，或在命令行里传入图片路径。")
        pause_if_frozen()
        sys.exit(1)

    if not os.path.exists(args.header):
        print(f"错误：顶部素材图不存在 → {args.header}")
        pause_if_frozen()
        sys.exit(1)

    font_path = resolve_font(args.font)
    header_src = Image.open(args.header).convert("RGB")
    logo_img = extract_logo(header_src)
    os.makedirs(args.output_dir, exist_ok=True)

    unit_text = "维保单位：" + unit

    print(f"字体:       {font_path}")
    print(f"Logo 尺寸:  {logo_img.size[0]}×{logo_img.size[1]}")
    print(f"标题文字:   {site}")
    print(f"单位文字:   {unit_text}")
    print(f"输出目录:   {os.path.abspath(args.output_dir)}")
    print(f"共 {len(files)} 张\n{'─'*40}")

    ok = fail = 0
    for i, src in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {os.path.basename(src)}")
        base, ext = os.path.splitext(os.path.basename(src))
        dst = os.path.join(args.output_dir, base + args.suffix + ext)
        if process_image(src, dst, logo_img, site, unit_text, font_path):
            ok += 1
        else:
            fail += 1

    print(f"{'─'*40}\n完成：成功 {ok} 张，失败 {fail} 张")
    print(f"输出目录：{os.path.abspath(args.output_dir)}")
    pause_if_frozen()

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        pause_if_frozen()
        sys.exit(1)
