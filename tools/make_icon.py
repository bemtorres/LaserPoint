from __future__ import annotations

import struct
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QRadialGradient

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "icon.ico"
SIZES = (16, 24, 32, 48, 64, 128, 256)


def render(size: int) -> bytes:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    color = QColor("#ff3b30")
    center = QPointF(size / 2.0, size / 2.0)
    radius = size * 0.44
    gradient = QRadialGradient(center, radius)
    glow = QColor(color)
    glow.setAlpha(205)
    edge = QColor(color)
    edge.setAlpha(0)
    gradient.setColorAt(0.0, glow)
    gradient.setColorAt(0.5, glow)
    gradient.setColorAt(1.0, edge)
    painter.setBrush(gradient)
    painter.drawEllipse(center, radius, radius)
    painter.setPen(QPen(QColor(0, 0, 0, 160), max(1.0, size * 0.05)))
    painter.setBrush(color)
    painter.drawEllipse(center, size * 0.23, size * 0.23)
    painter.end()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    data = bytes(buffer.data())
    buffer.close()
    return data


def build_ico(payloads: list[tuple[int, bytes]]) -> bytes:
    count = len(payloads)
    header = struct.pack("<HHH", 0, 1, count)
    offset = 6 + 16 * count
    directory = b""
    blobs = b""
    for size, payload in payloads:
        width = 0 if size >= 256 else size
        height = 0 if size >= 256 else size
        directory += struct.pack(
            "<BBBBHHII", width, height, 0, 0, 1, 32, len(payload), offset
        )
        blobs += payload
        offset += len(payload)
    return header + directory + blobs


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payloads = [(size, render(size)) for size in SIZES]
    OUTPUT.write_bytes(build_ico(payloads))
    print("icono generado: %s" % OUTPUT)


if __name__ == "__main__":
    main()
