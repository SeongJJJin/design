"""
텍스트 처리 유틸리티 모듈
중복된 텍스트 처리 로직을 통합하여 일관성을 보장합니다.
"""

import os
from typing import Optional

# PIL 선택적 임포트 - 없어도 fallback 계산으로 작동
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = ImageDraw = ImageFont = None


class TextUtils:
    """텍스트 처리를 위한 유틸리티 클래스"""
    
    def __init__(self, fonts_path: str = None):
        """
        Args:
            fonts_path: 폰트 파일이 위치한 경로
        """
        if fonts_path is None:
            # 기본 폰트 경로 설정 (프로젝트 루트/assets/fonts)
            self.fonts_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'fonts'
            )
        else:
            self.fonts_path = fonts_path
    
    @staticmethod
    def clean_text_newlines(text) -> str:
        """
        텍스트의 개행문자 정리 (내용 유지하면서 개행문자만 제거)
        
        Args:
            text: 정리할 텍스트
            
        Returns:
            정리된 텍스트
        """
        if not isinstance(text, str):
            text = str(text)

        # 개행문자(\n, \r\n, \r)를 공백으로 변환
        cleaned = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')

        # 연속된 공백을 하나로 정리
        cleaned = ' '.join(cleaned.split())

        # 앞뒤 공백 제거
        cleaned = cleaned.strip()

        return cleaned
    
    def get_font(self, size: int, weight: str = 'normal', font_type: str = 'content'):
        """
        폰트 로딩 (position_settings.py와 json_to_image.py 로직 통합)
        
        Args:
            size: 폰트 크기
            weight: 폰트 굵기 ('normal', 'bold')
            font_type: 폰트 타입 ('title', 'number', 'content')
            
        Returns:
            ImageFont 객체 (PIL 사용 시) 또는 None (fallback 시)
        """
        if not PIL_AVAILABLE:
            return None
            
        # 제목/번호용 또는 Bold 폰트 - Bold 우선
        if font_type in ['title', 'number'] or weight == 'bold':
            font_paths = [
                os.path.join(self.fonts_path, 'NotoSansCJKkr-Bold.otf'),
                os.path.join(self.fonts_path, 'NotoSansCJKkr-Bold.ttf'),
                os.path.join(self.fonts_path, 'NotoSansKR-Bold.ttf'),
                os.path.join(self.fonts_path, 'malgunbd.ttf'),
                os.path.join(self.fonts_path, 'malgun.ttf')
            ]
        else:
            # 내용용 폰트 - Regular 우선
            font_paths = [
                os.path.join(self.fonts_path, 'NotoSansCJKkr-Regular.otf'),
                os.path.join(self.fonts_path, 'NotoSansCJKkr-Regular.ttf'),
                os.path.join(self.fonts_path, 'NotoSansKR-Regular.ttf'),
                os.path.join(self.fonts_path, 'malgun.ttf')
            ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    continue
                    
        return ImageFont.load_default() if ImageFont else None
    
    def wrap_text_to_fit(self, draw, text: str, font, max_width: int) -> list:
        """
        텍스트를 최대 너비에 맞게 줄바꿈 (개선된 버전)
        
        Args:
            draw: ImageDraw 객체
            text: 줄바꿈할 텍스트
            font: 사용할 폰트
            max_width: 최대 너비
            
        Returns:
            줄바꿈된 텍스트 라인 리스트
        """
        # PIL 없는 경우 fallback 사용
        if not PIL_AVAILABLE or draw is None or font is None:
            return self._wrap_text_fallback(text, max_width)
            
        # 먼저 전체 텍스트 크기 확인
        try:
            full_bbox = draw.textbbox((0, 0), text, font=font)
            full_width = full_bbox[2] - full_bbox[0]
            
            # 전체 텍스트가 max_width에 맞으면 1줄로 반환
            if full_width <= max_width:
                return [text]
                
        except Exception:
            pass  # 실패 시 단어별 분할 진행
            
        words = text.split()
        lines = []
        current_line = []
        
        # 빈 텍스트 처리
        if not words:
            return ['']

        for word in words:
            test_line = current_line + [word]
            test_text = ' '.join(test_line)
            
            try:
                bbox = draw.textbbox((0, 0), test_text, font=font)
                text_width = bbox[2] - bbox[0]
            except Exception:
                # textbbox 실패 시 fallback 계산
                text_width = len(test_text) * 20  # 대략적인 추정
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # 단일 단어가 max_width보다 긴 경우
                    # 한글의 경우 문자 단위로 강제 분할 시도
                    if len(word) > 1:
                        split_result = self._force_split_long_word(draw, word, font, max_width)
                        lines.extend(split_result[:-1])  # 마지막을 제외하고 추가
                        current_line = [split_result[-1]] if split_result else [word]
                    else:
                        lines.append(word)
                        current_line = []

        if current_line:
            lines.append(' '.join(current_line))

        # 최소 1줄은 보장
        if not lines:
            lines = [text]

        return lines
        
    def _force_split_long_word(self, draw, word: str, font, max_width: int) -> list:
        """긴 단어를 강제로 분할"""
        if len(word) <= 1:
            return [word]
            
        # 문자 단위로 나누어 max_width에 맞게 분할
        result = []
        current_part = ""
        
        for char in word:
            test_text = current_part + char
            try:
                bbox = draw.textbbox((0, 0), test_text, font=font)
                text_width = bbox[2] - bbox[0]
            except Exception:
                text_width = len(test_text) * 20
                
            if text_width <= max_width:
                current_part = test_text
            else:
                if current_part:
                    result.append(current_part)
                    current_part = char
                else:
                    # 단일 문자도 넘치는 경우
                    result.append(char)
                    current_part = ""
        
        if current_part:
            result.append(current_part)
            
        return result if result else [word]
    
    def _wrap_text_fallback(self, text: str, max_width: int) -> list:
        """PIL 없이 텍스트 줄바꿈 (fallback, 개선된 한글 처리)"""
        # 너무 긴 단어는 강제로 분할 (한글의 경우)
        words = self._split_long_words(text.split(), max_width)
        lines = []
        current_line = []
        current_width = 0
        
        if not words:
            return ['']
        
        for word in words:
            # 한글과 영어/숫자를 구분하여 너비 추정
            korean_chars = sum(1 for c in word if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3)
            other_chars = len(word) - korean_chars
            word_width = korean_chars * 30 + other_chars * 18
            
            # 공백 포함 계산
            space_width = 18 if current_line else 0
            total_width = current_width + space_width + word_width
            
            if total_width <= max_width:
                current_line.append(word)
                current_width += space_width + word_width
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_width = word_width
                else:
                    # 단일 단어가 너무 긴 경우 (이미 분할되었어야 함)
                    lines.append(word)
                    current_line = []
                    current_width = 0
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [text]
    
    def _split_long_words(self, words: list, max_width: int) -> list:
        """너무 긴 단어를 적절히 분할"""
        result = []
        max_chars_per_word = max_width // 25  # 대략적인 문자 수 제한
        
        for word in words:
            if len(word) <= max_chars_per_word:
                result.append(word)
            else:
                # 긴 단어를 적절한 크기로 분할
                while len(word) > max_chars_per_word:
                    # 한글 단어의 경우 의미 단위로 분할 시도
                    split_pos = max_chars_per_word
                    # 쉼표나 구두점이 있으면 그 지점에서 분할
                    for i, char in enumerate(word[:max_chars_per_word]):
                        if char in ',，.。;；:：':
                            split_pos = i + 1
                            break
                    
                    result.append(word[:split_pos])
                    word = word[split_pos:]
                
                if word:  # 남은 부분 추가
                    result.append(word)
        
        return result
    
    def calculate_text_lines_accurate(self, text: str, max_width: int, font_size: int, 
                                    font_type: str = 'content', font_weight: str = 'normal') -> int:
        """
        실제 폰트를 사용하여 정확한 텍스트 라인 수 계산
        
        Args:
            text: 계산할 텍스트
            max_width: 최대 너비
            font_size: 폰트 크기
            font_type: 폰트 타입 ('title', 'number', 'content')
            font_weight: 폰트 굵기 ('normal', 'bold')
            
        Returns:
            필요한 라인 수
        """
        
        # 개행문자 전처리
        cleaned_text = self.clean_text_newlines(text)
        
        # 빈 텍스트 처리
        if not cleaned_text.strip():
            return 1
        
        # PIL 사용 불가능한 경우 바로 fallback 사용
        if not PIL_AVAILABLE:
            return self._calculate_text_lines_fallback(cleaned_text, max_width)
            
        try:
            # 임시 이미지 생성하여 실제 폰트로 측정
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            
            font = self.get_font(font_size, font_weight, font_type)
            if font is None:
                return self._calculate_text_lines_fallback(cleaned_text, max_width)
            
            # 실제 줄바꿈 계산
            lines = self.wrap_text_to_fit(temp_draw, cleaned_text, font, max_width)
            actual_lines = len(lines)
            
            
            return max(1, actual_lines)
            
        except Exception as e:
            # 폰트 로딩 실패 시 기본 계산 방식 사용
            return self._calculate_text_lines_fallback(cleaned_text, max_width)
    
    def _calculate_text_lines_fallback(self, text: str, max_width: int) -> int:
        """
        폰트 로딩 실패 시 사용하는 대체 계산 방식 (개선된 한글 추정)
        
        Args:
            text: 계산할 텍스트
            max_width: 최대 너비
            
        Returns:
            추정 라인 수
        """
        
        # 한글과 영어/숫자를 구분하여 더 정확한 추정
        korean_chars = sum(1 for c in text if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3)
        other_chars = len(text) - korean_chars
        
        # 한글: 약 30px, 영어/숫자: 약 18px로 추정 (36pt 폰트 기준)
        estimated_width = korean_chars * 30 + other_chars * 18
        
        if estimated_width <= max_width:
            total_lines = 1
        else:
            # 단어 단위로 줄바꿈을 고려한 더 정확한 계산
            words = text.split()
            lines = []
            current_line = []
            current_width = 0
            
            for word in words:
                word_korean_chars = sum(1 for c in word if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3)
                word_other_chars = len(word) - word_korean_chars
                word_width = word_korean_chars * 30 + word_other_chars * 18
                
                # 공백 포함 계산
                if current_line:
                    word_width += 18  # 공백 너비
                
                if current_width + word_width <= max_width:
                    current_line.append(word)
                    current_width += word_width
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                        current_width = word_width - (18 if len(current_line) > 1 else 0)  # 공백 제거
                    else:
                        # 단일 단어가 너무 긴 경우
                        lines.append(word)
                        current_line = []
                        current_width = 0
            
            if current_line:
                lines.append(' '.join(current_line))
            
            total_lines = len(lines) if lines else 1
        
        return max(1, total_lines)
    
    def get_text_actual_height(self, text: str, font_size: int, max_width: int,
                              font_type: str = 'content', font_weight: str = 'normal',
                              line_height_multiplier: int = 44) -> int:
        """
        텍스트의 실제 높이 계산
        
        Args:
            text: 계산할 텍스트
            font_size: 폰트 크기
            max_width: 최대 너비
            font_type: 폰트 타입
            font_weight: 폰트 굵기
            line_height_multiplier: 라인당 높이
            
        Returns:
            텍스트 높이 (픽셀)
        """
        lines = self.calculate_text_lines_accurate(text, max_width, font_size, font_type, font_weight)
        return lines * line_height_multiplier