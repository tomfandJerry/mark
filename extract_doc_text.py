# 临时脚本：从 .doc 提取文本
import os
import sys

doc_path = r"f:\学习\学校\毕业设计\祝玉洁 基于YOLOv11的SRA图像船舶检测算法设计 开题报告 - 副本.doc"
out_path = r"f:\学习\学校\毕业设计\代码\开题报告-提取.txt"

try:
    import win32com.client
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(doc_path)
    text = doc.Content.Text
    doc.Close(False)
    word.Quit()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print("OK", out_path)
except Exception as e:
    print("Error:", e)
    sys.exit(1)
