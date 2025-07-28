"""
위치 설정 관리 클래스
텍스트 레이어들의 위치를 세밀하게 조절할 수 있는 기능을 제공합니다.
"""

# =====================================================================
# 🔧 사용자 간격 설정 영역 - 여기서 값을 직접 수정하세요!
# =====================================================================

# 📏 텍스트 간격 설정 (픽셀 단위)
USER_SPACING_CONFIG = {
    # ✏️ 제목-내용 사이 간격 (기본: 35px)
    # - 값이 클수록 제목과 내용 사이가 더 벌어집니다
    # - 권장 범위: 20~60px
    'title_content_spacing': 25,
    
    # 📦 레이어 간 간격 (기본: 20px) 
    # - 각 레이어(번호, 제목, 내용 묶음) 사이의 간격
    # - 값이 클수록 레이어들이 더 벌어집니다
    # - 권장 범위: 10~50px
    'layer_spacing': 20,
    
    # 📐 레이어 내부 여백 (기본: 상단20px, 하단20px)
    # - 레이어 박스 안에서 텍스트와 경계선 사이의 여백
    # - 권장 범위: 10~40px
    'layer_top_margin': 32,       # 레이어 상단 여백
    'layer_bottom_margin': 32,    # 레이어 하단 여백
}

# 📍 텍스트 위치 설정 (픽셀 단위)
USER_POSITION_CONFIG = {
    # ➡️ 가로 위치 설정
    'title_x': 145.25,    # 제목 시작 X 좌표 (기본: 145.25px)
    'content_x': 146.77,  # 내용 시작 X 좌표 (기본: 146.77px)
    
    # 📏 텍스트 영역 크기 설정
    'title_width': 800,   # 제목 최대 너비 (기본: 800px) - 이 너비를 넘으면 줄바꿈
    'content_width': 800, # 내용 최대 너비 (기본: 850px) - 이 너비를 넘으면 줄바꿈
}

# 🔧 고급 설정 (일반적으로 수정할 필요 없음)
ADVANCED_CONFIG = {
    'start_y': 430,                # 첫 번째 레이어 시작 Y 좌표
    'line_height_multiplier': 44,  # 줄 높이 (각 줄 사이의 간격)
    'fixed_layer_height': 150,     # 기본 레이어 박스 높이
}

# =====================================================================
# 💡 설정 변경 방법:
# 1. 위의 값들을 원하는 숫자로 직접 수정하세요
# 2. 파일을 저장하고 이미지를 다시 생성하면 적용됩니다
# 3. 값이 너무 크거나 작으면 레이아웃이 깨질 수 있으니 조금씩 조정하세요
# =====================================================================

import json
import os
from typing import Dict, Any, Optional

# PIL 선택적 임포트 - 없어도 fallback 계산으로 작동
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL/Pillow 없음 - fallback 텍스트 계산 사용")

from ..utils.text_utils import TextUtils


class PositionSettings:
    """텍스트 위치 설정을 관리하는 클래스"""

    def __init__(self):
        """기본 위치 설정으로 초기화"""
        # 사용자 설정값들을 기본 설정에 병합
        self._settings = {
            # 🔧 사용자 설정 영역에서 가져온 값들
            **USER_SPACING_CONFIG,
            **USER_POSITION_CONFIG, 
            **ADVANCED_CONFIG,
            
            # 📍 고정 설정값들 (일반적으로 수정 불필요)
            'number_x': 67.25,             # 번호 X 좌표
            'number_width_first': 44.98,   # 첫 번째 번호 너비
            'number_width_others': 53.3,   # 나머지 번호 너비
            'number_height': 46.87,        # 번호 높이
        }

        # 위치 조정 활성화 여부
        self._manual_adjustment_enabled = True
        
        # 폰트 경로 설정 (프로젝트 루트/assets/fonts)
        self.fonts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'fonts')
        
        # 텍스트 유틸리티 초기화
        self.text_utils = TextUtils(self.fonts_path)

    def enable_manual_adjustment(self, enabled: bool = True):
        """수동 위치 조정 활성화/비활성화"""
        self._manual_adjustment_enabled = enabled

    def is_manual_adjustment_enabled(self) -> bool:
        """수동 위치 조정 활성화 상태 확인"""
        return self._manual_adjustment_enabled


    def get_setting(self, key: str) -> Any:
        """설정값 가져오기"""
        return self._settings.get(key)

    def set_setting(self, key: str, value: Any):
        """설정값 변경"""
        if key in self._settings:
            self._settings[key] = value
        else:
            raise KeyError(f"Unknown setting key: {key}")

    def get_all_settings(self) -> Dict[str, Any]:
        """모든 설정값 반환"""
        return self._settings.copy()

    def update_settings(self, settings: Dict[str, Any]):
        """여러 설정값 일괄 업데이트"""
        for key, value in settings.items():
            if key in self._settings:
                self._settings[key] = value

    def reset_to_default(self):
        """기본 설정으로 초기화"""
        self.__init__()


    def calculate_positions(self, valid_data, image_height: Optional[int] = None, template_data: Optional[Dict] = None) -> list:
        """향상된 위치 계산 메소드 (템플릿 기반)"""
        # 기존 간단한 계산 방식 (하위 호환성)
        return self._calculate_positions_simple(valid_data, image_height)

    def _calculate_positions_simple(self, valid_data, image_height: Optional[int] = None) -> list:
        """간단한 위치 계산 방식 (동적 박스, 개행문자 처리)"""
        positions = []

        # 기본 설정값들
        start_y = self.get_setting('start_y')
        layer_spacing = self.get_setting('layer_spacing')
        title_content_spacing = self.get_setting('title_content_spacing')
        layer_top_margin = self.get_setting('layer_top_margin')
        layer_bottom_margin = self.get_setting('layer_bottom_margin')
        line_height = self.get_setting('line_height_multiplier')


        current_y = start_y

        for i, (_, row) in enumerate(valid_data.iterrows()):
            layer_num = int(row.get('번호', i + 1))
            
            try:
                title = self.text_utils.clean_text_newlines(str(row['제목']))
            except Exception as e:
                title = str(row['제목'])
                
            try:
                content = self.text_utils.clean_text_newlines(str(row['설명']))
            except Exception as e:
                content = str(row['설명'])

            # 첫 번째 레이어가 아니면 레이어 간격 추가
            if i > 0:
                current_y += layer_spacing

            # === 동적 레이어 박스 구조 (Simple 방식) ===
            layer_box_start_y = current_y

            
            # 텍스트 라인 수 계산 (실제 폰트 기반, json_to_image와 동일한 폰트 크기)
            try:
                title_lines = self.text_utils.calculate_text_lines_accurate(title, self.get_setting('title_width'), 36, 'title', 'bold')
            except Exception as e:
                # 기본값으로 fallback
                title_lines = 1
            
            try:
                content_lines = self.text_utils.calculate_text_lines_accurate(content, self.get_setting('content_width'), 28, 'content', 'normal')
            except Exception as e:
                # 기본값으로 fallback
                content_lines = 1

            # 텍스트 높이 계산
            title_height = title_lines * line_height  # 실제 제목 높이
            content_height = content_lines * line_height  # 실제 내용 높이
            
            # === 간단하고 정확한 레이어 박스 계산 ===
            
            # 1. 총 필요 높이 계산 (여백 포함)
            actual_content_height = title_height + title_content_spacing + content_height
            total_required_height = layer_top_margin + actual_content_height + layer_bottom_margin
            
            # 2. 박스 경계 직접 설정 (현재 위치에서 시작)
            adjusted_layer_start_y = int(current_y)
            final_layer_height = int(total_required_height)
            adjusted_layer_end_y = int(adjusted_layer_start_y + final_layer_height)
            
            # 3. 고정 여백으로 요소 배치 (상단에서 시작)
            title_y = int(adjusted_layer_start_y + layer_top_margin)
            number_y = title_y  # 번호는 제목과 같은 위치
            content_y = int(title_y + title_height + title_content_spacing)
            
            # 4. 실제 여백 계산 (검증용)
            actual_top_margin = title_y - adjusted_layer_start_y
            actual_bottom_margin = adjusted_layer_end_y - (content_y + content_height)
            final_title_content_gap = content_y - (title_y + title_height)
            
            # --- 기존 변수 호환성 유지 ---
            fixed_height = self.get_setting('fixed_layer_height')
            extra_height = max(0, total_required_height - fixed_height)
            gap_exact = abs(final_title_content_gap - title_content_spacing) < 0.1
            margin_ok = abs(actual_top_margin - layer_top_margin) < 1 and abs(actual_bottom_margin - layer_bottom_margin) < 1
            
            # 보정된 값으로 위치 정보 생성 (동적 박스 구조 + 줄 수 정보 추가)
            position = {
                'number': {
                    'width': self.get_setting('number_width_first') if i == 0 else self.get_setting('number_width_others'),
                    'height': self.get_setting('number_height'),
                    'x': self.get_setting('number_x'),
                    'y': number_y
                },
                'title': {
                    'width': self.get_setting('title_width'),
                    'height': title_height,  # 실제 텍스트 기반 높이
                    'x': self.get_setting('title_x'),
                    'y': title_y,
                    'lines': title_lines,  # JsonToImage 동기화용 줄 수
                    'text': title  # JsonToImage 동기화용 텍스트
                },
                'content': {
                    'width': self.get_setting('content_width'),
                    'height': content_height,  # 실제 텍스트 기반 높이
                    'x': self.get_setting('content_x'),
                    'y': content_y,  # 보정된 Y 좌표 사용
                    'lines': content_lines,  # JsonToImage 동기화용 줄 수
                    'text': content  # JsonToImage 동기화용 텍스트
                },
                # 동적 레이어 박스 정보 (보정된 값 포함)
                'layer_box': {
                    'start_y': adjusted_layer_start_y,
                    'end_y': adjusted_layer_end_y,  # 보정된 끝 Y 좌표
                    'height': final_layer_height,  # 보정된 높이
                    'base_height': fixed_height,
                    'extra_height': extra_height,
                    'top_margin': layer_top_margin,
                    'bottom_margin': layer_bottom_margin,
                    'actual_top_margin': actual_top_margin,
                    'actual_bottom_margin': actual_bottom_margin,  # 보정된 여백
                    'title_content_gap': title_content_spacing,  # 항상 설정값으로 보장
                    'content_area_height': actual_content_height,
                    'is_first_layer': (i == 0),
                    'is_last_layer': (i == len(valid_data) - 1),
                    'is_dynamic_expanded': True,  # 동적 확장 박스임을 표시
                    'margin_verified': gap_exact and margin_ok  # 보정 후 검증 결과
                }
            }

            positions.append(position)

            # 다음 레이어 시작점 설정 (보정된 박스 끝 반영)
            current_y = adjusted_layer_end_y

        return positions


    def save_to_file(self, file_path: str):
        """설정을 JSON 파일로 저장"""
        data = {
            'settings': self._settings,
            'manual_adjustment_enabled': self._manual_adjustment_enabled
        }

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, file_path: str):
        """JSON 파일에서 설정 불러오기"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'settings' in data:
            self._settings.update(data['settings'])
        if 'manual_adjustment_enabled' in data:
            self._manual_adjustment_enabled = data['manual_adjustment_enabled']

    def export_preset(self, name: str, description: str = "") -> Dict[str, Any]:
        """현재 설정을 프리셋으로 내보내기"""
        return {
            'name': name,
            'description': description,
            'settings': self._settings.copy(),
            'manual_adjustment_enabled': self._manual_adjustment_enabled
        }

    def import_preset(self, preset_data: Dict[str, Any]):
        """프리셋 데이터 가져오기"""
        if 'settings' in preset_data:
            self._settings.update(preset_data['settings'])
        if 'manual_adjustment_enabled' in preset_data:
            self._manual_adjustment_enabled = preset_data['manual_adjustment_enabled']

    def get_position_summary(self) -> str:
        """현재 위치 설정 요약 반환"""
        summary = f"""위치 설정 요약:
- 시작 Y: {self.get_setting('start_y')}px
- 레이어 간격: {self.get_setting('layer_spacing')}px
- 제목-내용 간격: {self.get_setting('title_content_spacing')}px
- 상단 여백: {self.get_setting('layer_top_margin')}px
- 하단 여백: {self.get_setting('layer_bottom_margin')}px
- 수동 조정: {'활성화' if self._manual_adjustment_enabled else '비활성화'}"""
        return summary
