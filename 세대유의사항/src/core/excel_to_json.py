import pandas as pd
import json
import io
from .position_settings import PositionSettings
from ..utils.text_utils import TextUtils
from ..utils.company_colors import CompanyColorManager


class ExelToJson:
    def __init__(self, excel_file, position_settings=None, theme_color=None, company_name=None):
        self.excel_file = excel_file
        # 위치 설정 (기본값: 새 PositionSettings 인스턴스)
        self.position_settings = position_settings or PositionSettings()
        
        # 건설사 테마 색상 설정
        if theme_color:
            # 직접 지정된 색상 사용
            self.theme_color = theme_color
        elif company_name:
            # 건설사명으로 색상 자동 결정
            self.theme_color = CompanyColorManager.get_color(company_name)
        else:
            # 기본 색상 (호반건설)
            self.theme_color = CompanyColorManager.DEFAULT_COLOR.copy()
        
        # 건설사명 저장 (로깅용)
        self.company_name = company_name or "기본"
        
        # 텍스트 유틸리티 초기화
        self.text_utils = TextUtils()


    def calculate_text_lines(self, text, max_width=700):
        """텍스트가 차지할 라인 수 계산 (개행문자 전처리 포함)"""
        # 개행문자 전처리
        # cleaned_text = text  # self.clean_text_newlines(text)

        avg_char_width = 25
        chars_per_line = max_width // avg_char_width

        # 정리된 텍스트는 개행문자가 없으므로 단순 계산
        text_length = len(text)
        if text_length <= chars_per_line:
            total_lines = 1
        else:
            total_lines = (text_length + chars_per_line - 1) // chars_per_line

        return max(1, total_lines)

    def create_layer(self, layer_num, title, content, positions):
        """레이어 생성"""
        return {
            'number_layer': {
                'info': {
                    'width': positions['number']['width'],
                    'height': positions['number']['height'],
                    'x': positions['number']['x'],
                    'y': positions['number']['y']
                },
                'char': {
                    'font_size': '36pt',
                    'font_family': 'Noto Sans CJK KR',
                    'font_weight': 'bold',
                    'color': self.theme_color,
                    'text_height': '44pt',
                    'text_width': '-50'
                },
                'text': f"{layer_num:02d}"
            },
            'title_layer': {
                'info': {
                    'width': positions['title']['width'],
                    'height': positions['title']['height'],
                    'x': positions['title']['x'],
                    'y': positions['title']['y']
                },
                'char': {
                    'font_size': '36pt',
                    'font_family': 'Noto Sans CJK KR',
                    'font_weight': 'bold',
                    'color': self.theme_color,
                    'text_height': '48pt',
                    'text_width': '-50'
                },
                'text': title
            },
            'content_layer': {
                'info': {
                    'width': positions['content']['width'],
                    'height': positions['content']['height'],
                    'x': positions['content']['x'],
                    'y': positions['content']['y']
                },
                'char': {
                    'font_size': '28pt',
                    'font_family': 'Noto Sans CJK KR',
                    'font_weight': 'regular',
                    'color': [10, 10, 10],  # #0A0A0A
                    'text_height': '44pt',
                    'text_width': '-50'
                },
                'text': content
            }
        }

    def calculate_layer_positions(self, valid_data, image_height=None):
        """레이어 위치 계산 (PositionSettings 사용)"""
        return self.position_settings.calculate_positions(valid_data, image_height)

    def find_column_mapping(self, df):
        """컬럼 이름을 자동으로 매핑"""
        columns = df.columns.tolist()
        mapping = {}
        
        # 번호 컬럼 찾기
        for col in columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['번호', 'no', 'num', '순서']):
                mapping['번호'] = col
                break
        
        # 제목 컬럼 찾기
        for col in columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['제목', 'title', '항목', '내용']):
                mapping['제목'] = col
                break
                
        # 설명 컬럼 찾기
        for col in columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['설명', 'desc', '내용', '상세']):
                mapping['설명'] = col
                break
        
        return mapping

    def generate_json_from_excel(self):
        """Excel에서 JSON 생성"""
        try:
            # 색상 정보 로깅
            if self.company_name != "기본":
                color_info = CompanyColorManager.get_color_info(self.company_name)
                print(f"🎨 건설사 테마 색상 적용: {self.company_name} -> {color_info['hex']} (RGB: {self.theme_color})")
            # Excel 파일 읽기
            file_contents = self.excel_file.read()
            file_like = io.BytesIO(file_contents)

            # 여러 헤더 위치로 시도해보기
            df = None
            column_mapping = {}

            for header_row in [0, 1, 2]:
                try:
                    temp_df = pd.read_excel(file_like, header=header_row)
                    file_like.seek(0)  # 파일 포인터 리셋

                    # 컬럼 매핑 시도
                    temp_mapping = self.find_column_mapping(temp_df)

                    # 필수 컬럼이 모두 있는지 확인
                    if len(temp_mapping) >= 2:  # 최소 번호, 제목 또는 설명
                        df = temp_df
                        column_mapping = temp_mapping
                        print(f"헤더 행 {header_row}에서 컬럼 매핑 성공: {column_mapping}")
                        break
                except Exception as e:
                    continue

            if df is None or not column_mapping:
                raise ValueError("적절한 컬럼을 찾을 수 없습니다. 엑셀 파일의 컬럼명을 확인해주세요.")

            # 템플릿 기본 구조
            template = {
                'template_name': None,
                'logo_image': None,
                'dpi': None,
                'layers': {}
            }

            # 컬럼명 변경
            rename_dict = {v: k for k, v in column_mapping.items()}
            df = df.rename(columns=rename_dict)

            # 필수 컬럼이 없는 경우 기본값 설정
            if '번호' not in df.columns:
                df['번호'] = range(1, len(df) + 1)
            if '제목' not in df.columns:
                df['제목'] = df.get('설명', '제목 없음')
            if '설명' not in df.columns:
                df['설명'] = df.get('제목', '설명 없음')

            # 유효한 데이터만 필터링
            available_cols = [col for col in ['번호', '제목', '설명'] if col in df.columns]
            valid_data = df.dropna(subset=available_cols, how='all')

            # 레이어 위치 계산
            layer_positions = self.calculate_layer_positions(valid_data)

            # 각 행에 대해 레이어 생성 (레이어 번호와 위치 인덱스 정확히 매핑)
            position_dict = {}
            for position_index, (_, row) in enumerate(valid_data.iterrows()):
                layer_num = int(row['번호'])
                position_dict[layer_num] = position_index

            for position_index, (_, row) in enumerate(valid_data.iterrows()):
                layer_num = int(row['번호'])
                title = self.text_utils.clean_text_newlines(str(row['제목']))
                content = self.text_utils.clean_text_newlines(str(row['설명']))

                # 위치 정보 가져오기 (올바른 인덱스 사용)
                correct_position_index = position_dict[layer_num]
                if correct_position_index < len(layer_positions):
                    positions = layer_positions[correct_position_index]
                    # print(f"🔧 레이어 매핑: 엑셀번호={layer_num}, 위치인덱스={correct_position_index}")
                else:
                    raise IndexError(f"레이어 {layer_num}의 위치 정보를 찾을 수 없습니다.")

                layer_key = f'layer{layer_num}'
                template['layers'][layer_key] = self.create_layer(layer_num, title, content, positions)

            # # JSON 파일로 저장
            # with open(self.output_file, 'w', encoding='utf-8') as f:
            #     json.dump(template, f, ensure_ascii=False, indent=4)

            return json.dumps(template)
        except Exception as e:
            raise e
