"""Generate a symmetric rounded active border using only the standard library."""
from math import hypot
from pathlib import Path
import struct

SIZE = 128
RADIUS = 3
FEATHER = 3
BUTTON_SIZE = 36
EXTENT = BUTTON_SIZE + 2 * FEATHER
SAMPLES = 4


def opacity(x, y):
    # Rounded-rectangle signed distance, centered within the full texture.
    qx = abs(x - EXTENT / 2) - (BUTTON_SIZE / 2 - RADIUS)
    qy = abs(y - EXTENT / 2) - (BUTTON_SIZE / 2 - RADIUS)
    distance = hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - RADIUS
    if distance < -1 or distance > FEATHER:
        return 0
    fade = 0.55 * (FEATHER - distance) / (FEATHER + 1)
    core = 0.75 if distance <= 0 else 0
    return core + fade * (1 - core)


def main():
    pixels = bytearray()
    for y in range(SIZE):
        for x in range(SIZE):
            alpha = sum(
                opacity((x + (sx + 0.5) / SAMPLES) * EXTENT / SIZE,
                        (y + (sy + 0.5) / SAMPLES) * EXTENT / SIZE)
                for sy in range(SAMPLES) for sx in range(SAMPLES)
            ) / (SAMPLES * SAMPLES)
            pixels.extend((255, 255, 255, round(255 * alpha)))
    # Uncompressed BGRA TGA, top-left origin, eight alpha bits.
    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, SIZE, SIZE, 32, 0x28)
    # Verify exact pixel symmetry before writing the asset.
    rows = [pixels[y * SIZE * 4:(y + 1) * SIZE * 4] for y in range(SIZE)]
    assert rows == rows[::-1], "Border must be vertically symmetric"
    for row in rows:
        cells = [row[x * 4:(x + 1) * 4] for x in range(SIZE)]
        assert cells == cells[::-1], "Border must be horizontally symmetric"
    destination = Path(__file__).resolve().parents[1] / "ui" / "ActiveBorder.tga"
    destination.write_bytes(header + pixels)
    print(f"Generated {destination}")


if __name__ == "__main__":
    main()
