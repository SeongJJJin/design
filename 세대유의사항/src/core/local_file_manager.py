import gc
import json
import io
import os
import shutil
from .excel_to_json import ExelToJson


class LocalFileManager:
    def __init__(self, base_path=None):
        if base_path is None:
            # 프로젝트 루트/assets 디렉토리를 기본으로 사용
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            base_path = os.path.join(project_root, 'assets')
        self.base_path = base_path
        self.fonts_path = os.path.join(base_path, 'fonts')
        self.templates_path = os.path.join(base_path, 'templates')
        self.data_path = os.path.join(base_path, 'data')
        
        # 필요한 디렉토리 생성
        for path in [self.fonts_path, self.templates_path, self.data_path]:
            os.makedirs(path, exist_ok=True)

    def setup_fonts(self, temp_fonts_path):
        """폰트 파일을 임시 디렉토리로 복사"""
        os.makedirs(temp_fonts_path, exist_ok=True)
        
        font_files = ['NotoSansCJKkr-Bold.otf', 'NotoSansCJKkr-Regular.otf']
        
        for font_file in font_files:
            src_path = os.path.join(self.fonts_path, font_file)
            dst_path = os.path.join(temp_fonts_path, font_file)
            
            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_path)
                print(f"폰트 복사됨: {font_file}")
            else:
                print(f"폰트 파일을 찾을 수 없음: {src_path}")

    def process_excel(self, excel_file_path, position_settings, company_name=None):
        """엑셀 파일 처리 (건설사별 색상 적용)"""
        if not os.path.exists(excel_file_path):
            raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {excel_file_path}")

        with open(excel_file_path, 'rb') as f:
            excel_file = io.BytesIO(f.read())
        excel_processor = ExelToJson(excel_file, position_settings, company_name=company_name)
        excel_file_json = excel_processor.generate_json_from_excel()

        del excel_file, excel_processor
        gc.collect()

        if isinstance(excel_file_json, str):
            excel_file_json = json.loads(excel_file_json)

        return excel_file_json

    def get_template_path(self, construction_name, result_path):
        """템플릿 파일 경로 반환 및 결과 디렉토리로 복사 (.png 및 .jpg 지원)"""
        # 우선순위: _템플릿.png > .jpg
        template_candidates = [
            f'{construction_name}_템플릿.png',  # 기존 방식
            f'{construction_name}.jpg'          # 새로운 방식
        ]
        
        source_template_path = None
        template_filename = None
        
        for candidate in template_candidates:
            candidate_path = os.path.join(self.templates_path, candidate)
            if os.path.exists(candidate_path):
                source_template_path = candidate_path
                template_filename = candidate
                break
        
        if not source_template_path:
            raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {construction_name} (찾은 위치: {self.templates_path})")
        
        os.makedirs(result_path, exist_ok=True)
        result_template_path = os.path.join(result_path, template_filename)
        shutil.copy2(source_template_path, result_template_path)
        
        return result_template_path

    def get_available_templates(self):
        """사용 가능한 템플릿 목록 반환 (.png 및 .jpg 지원)"""
        if not os.path.exists(self.templates_path):
            return []
        
        templates = []
        for file in os.listdir(self.templates_path):
            # .png 템플릿 파일 (기존 방식)
            if file.endswith('_템플릿.png'):
                construction_name = file.replace('_템플릿.png', '')
                templates.append(construction_name)
            # .jpg 파일 (새로운 방식) - 확장자만으로 건설사명 추출
            elif file.endswith('.jpg'):
                construction_name = file.replace('.jpg', '')
                templates.append(construction_name)
        
        # 중복 제거 및 정렬
        return sorted(list(set(templates)))
    
    def find_template_file_path(self, construction_name):
        """건설사명으로 실제 템플릿 파일 경로 찾기 (복사 없이)"""
        template_candidates = [
            f'{construction_name}_템플릿.png',  # 기존 방식
            f'{construction_name}.jpg'          # 새로운 방식
        ]
        
        for candidate in template_candidates:
            candidate_path = os.path.join(self.templates_path, candidate)
            if os.path.exists(candidate_path):
                return candidate_path
        
        return None

    def validate_files(self):
        """필수 파일들이 존재하는지 확인"""
        missing_files = []
        
        # 폰트 파일 체크
        font_files = ['NotoSansCJKkr-Bold.otf', 'NotoSansCJKkr-Regular.otf']
        for font_file in font_files:
            font_path = os.path.join(self.fonts_path, font_file)
            if not os.path.exists(font_path):
                missing_files.append(f"fonts/{font_file}")
        
        # 템플릿 파일 체크
        templates = self.get_available_templates()
        if not templates:
            missing_files.append("templates/*.png")
        
        return missing_files