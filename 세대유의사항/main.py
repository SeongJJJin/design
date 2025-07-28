#!/usr/bin/env python3
"""
주의사항 이미지 생성기 - 메인 실행 파일

Usage:
    python main.py
"""

import sys
import os
import tkinter as tk

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.gui.gui_app import ImageGeneratorApp


def main():
    """메인 함수"""
    try:
        root = tk.Tk()
        app = ImageGeneratorApp(root)
        root.mainloop()
    except Exception as e:
        print(f"애플리케이션 실행 중 오류 발생: {e}")
        input("아무 키나 눌러서 종료...")


if __name__ == "__main__":
    main()
