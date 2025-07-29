# PIL 선택적 임포트 - 없어도 기본 기능 작동
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ JsonToImage: PIL/Pillow 없음 - 일부 기능 제한될 수 있음")
import os
import pandas as pd
from ..utils.text_utils import TextUtils


class JsonToImage:
    def __init__(self, excel_file_json, output_image, original_image, split_chunks, chunk_height, fonts_path='/tmp/fonts', output_dir=None, position_settings=None):
        self.excel_file_json = excel_file_json
        self.output_image = output_image
        self.original_image = original_image
        self.layer_spacing = 80
        self.split_chunks = split_chunks
        self.chunk_height = chunk_height
        self.fonts_path = fonts_path
        self.output_dir = output_dir or os.path.dirname(output_image)
        # 위치 설정 (선택적)
        self.position_settings = position_settings
        # 텍스트 유틸리티 초기화
        self.text_utils = TextUtils(fonts_path)

    def get_font(self, font_size, font_weight='normal', text_type='content'):
        """폰트 가져오기 (TextUtils 사용)"""
        if not PIL_AVAILABLE:
            return None
        size = int(float(font_size.replace('pt', '')))
        weight = 'bold' if (text_type in ['title', 'number'] or font_weight == 'bold') else 'normal'
        return self.text_utils.get_font(size, weight, text_type)

    def wrap_text_to_fit(self, draw, text, font, max_width):
        """텍스트를 최대 너비에 맞게 줄바꿈 (TextUtils 사용)"""
        return self.text_utils.wrap_text_to_fit(draw, text, font, max_width)

    def draw_text_bold(self, draw, position, text, font, color, is_bold=False):
        """볼드 텍스트 그리기"""
        x, y = position
        if is_bold:
            for dx in (0, 1):
                for dy in (0, 1):
                    draw.text((x + dx, y + dy), text, font=font, fill=color)
        else:
            draw.text((x, y), text, font=font, fill=color)

    def get_text_actual_height(self, draw, text, font, max_width):
        """텍스트의 실제 높이 계산 (PositionSettings와 완전 일치)"""
        lines = self.wrap_text_to_fit(draw, text, font, max_width)
        if not lines:
            return 0

        # 라인 높이 계산 (PositionSettings와 일관성 유지)
        line_spacing = 44  # PositionSettings의 line_height_multiplier와 동일

        # PositionSettings와 동일한 계산 방식: 줄 수 × line_spacing
        return len(lines) * line_spacing

    def draw_multiline_text(self, draw, position, text, font, color, max_width, is_bold=False, forced_lines=None):
        """여러 줄 텍스트 그리기 (PositionSettings 동기화 지원)"""
        x, y = position
        
        # 라인 높이 계산 (PositionSettings와 일관성 유지)
        line_spacing = 44  # PositionSettings의 line_height_multiplier와 동일
        
        # PositionSettings에서 계산한 줄 수가 있으면 검증 후 사용
        if forced_lines is not None:
            # 먼저 자연스러운 줄바꿈 계산
            natural_lines = self.wrap_text_to_fit(draw, text, font, max_width)
            natural_line_count = len(natural_lines)
            
            # 강제 줄 수와 자연스러운 줄 수가 큰 차이나지 않으면 강제 적용
            if abs(natural_line_count - forced_lines) <= 1:
                if forced_lines == 1:
                    lines = [text]  # 1줄로 강제
                else:
                    # TextUtils와 동일한 방식으로 줄바꿈 (실제 너비 기반)
                    lines = self._wrap_text_to_forced_lines(draw, text, font, max_width, forced_lines)
            else:
                lines = natural_lines
        else:
            # 기존 방식: 자동 줄바꿈 계산
            lines = self.wrap_text_to_fit(draw, text, font, max_width)

        current_y = y
        for i, line in enumerate(lines):
            if line.strip():  # 빈 줄이 아닌 경우만 그리기
                self.draw_text_bold(draw, (x, current_y), line, font, color, is_bold)
            current_y += line_spacing

        # 실제 텍스트 높이: PositionSettings와 정확히 일치
        # line_spacing은 "한 줄이 차지하는 전체 높이"이므로 모든 줄에 적용
        actual_height = len(lines) * line_spacing
        return actual_height
    
    def _wrap_text_to_forced_lines(self, draw, text, font, max_width, target_lines):
        """텍스트를 지정된 줄 수로 강제 분할 (실제 너비 기반)"""
        words = text.split()
        if not words:
            return ['']
        
        if target_lines == 1:
            return [text]
        
        # 자연스러운 줄바꿈을 먼저 시도
        natural_lines = self.wrap_text_to_fit(draw, text, font, max_width)
        
        if len(natural_lines) == target_lines:
            # 이미 목표 줄 수와 일치
            return natural_lines
        elif len(natural_lines) < target_lines:
            # 자연스러운 줄 수가 더 적음 - 강제로 더 나누기
            return self._force_split_into_more_lines(words, target_lines)
        else:
            # 자연스러운 줄 수가 더 많음 - 더 압축하기
            return self._force_merge_into_fewer_lines(natural_lines, target_lines)
    
    def _force_split_into_more_lines(self, words, target_lines):
        """단어를 더 많은 줄로 강제 분할"""
        lines = []
        words_per_line = max(1, len(words) // target_lines)
        
        for i in range(target_lines):
            start_idx = i * words_per_line
            if i == target_lines - 1:  # 마지막 줄
                end_idx = len(words)
            else:
                end_idx = min((i + 1) * words_per_line, len(words))
            
            if start_idx < len(words):
                line_words = words[start_idx:end_idx]
                lines.append(' '.join(line_words))
            else:
                lines.append('')  # 빈 줄
        
        # 빈 줄 제거
        lines = [line for line in lines if line.strip()]
        return lines if lines else ['']
    
    def _force_merge_into_fewer_lines(self, natural_lines, target_lines):
        """자연스러운 줄을 더 적은 줄로 병합"""
        if target_lines >= len(natural_lines):
            return natural_lines
        
        # 간단한 병합 전략: 인접한 줄들을 합치기
        merged_lines = []
        lines_per_target = len(natural_lines) / target_lines
        
        current_line = ""
        lines_count = 0
        
        for i, line in enumerate(natural_lines):
            if current_line:
                current_line += " " + line
            else:
                current_line = line
                
            lines_count += 1
            
            # 목표 줄당 라인 수에 도달했거나 마지막 라인인 경우
            if lines_count >= lines_per_target or i == len(natural_lines) - 1:
                merged_lines.append(current_line)
                current_line = ""
                lines_count = 0
                
                if len(merged_lines) >= target_lines:
                    break
        
        return merged_lines if merged_lines else natural_lines

    def calculate_layer_positions(self, template, image_height=None):
        """레이어 위치 계산 (PositionSettings 사용 가능, 이미지 높이 고려)"""
        layer_keys = sorted(template['layers'].keys(), key=lambda x: int(x.replace('layer', '')))

        # PositionSettings가 있으면 항상 사용 (간격 통일을 위해 강제 적용)
        if self.position_settings:
            return self.calculate_positions_with_settings(template, image_height)

        # PositionSettings가 없는 경우 에러 발생 (일관성 보장)
        raise ValueError("PositionSettings가 필수입니다. 일관성 있는 레이어 계산을 위해 PositionSettings를 사용해주세요.")

    def calculate_positions_with_settings(self, template, image_height=None):
        """PositionSettings를 사용한 위치 계산 (이미지 높이 고려)"""

        # 템플릿에서 데이터 추출
        data_rows = []
        layer_keys = sorted(template['layers'].keys(), key=lambda x: int(x.replace('layer', '')))

        for layer_key in layer_keys:
            layer_data = template['layers'][layer_key]
            layer_num = int(layer_key.replace('layer', ''))
            title = layer_data['title_layer']['text']
            content = layer_data['content_layer']['text']

            data_rows.append({
                '번호': layer_num,
                '제목': title,
                '설명': content
            })

        # DataFrame 생성
        df = pd.DataFrame(data_rows)

        # PositionSettings로 위치 계산 (이미지 높이와 템플릿 데이터 전달)
        positions = self.position_settings.calculate_positions(df, image_height=image_height, template_data=template)

        # 결과를 JsonToImage 형식으로 변환 (레이어 박스 정보 포함)
        layer_positions = {}
        for i, layer_key in enumerate(layer_keys):
            if i < len(positions):
                pos = positions[i]
                layer_num = int(layer_key.replace('layer', ''))
                
                # 레이어 박스 정보가 있는지 확인
                if 'layer_box' in pos:
                    
                    layer_positions[layer_key] = {
                        'base_y': int(pos['layer_box']['start_y']),  # 레이어 박스 시작점을 기준으로 변경
                        'number_y': int(pos['number']['y']),
                        'title_y': int(pos['title']['y']),
                        'content_y': int(pos['content']['y']),
                        'height': int(pos['layer_box']['height']),  # 레이어 박스 전체 높이
                        'actual_content_height': int(pos['content']['height']),
                        # 레이어 박스 정보 추가
                        'layer_box_start': int(pos['layer_box']['start_y']),
                        'layer_box_end': int(pos['layer_box']['end_y']),
                        'layer_box_height': int(pos['layer_box']['height']),
                        # PositionSettings 계산 줄 수 정보 추가 (동기화용)
                        'title_lines': pos['title'].get('lines', 1),
                        'content_lines': pos['content'].get('lines', 1),
                        'title_text': pos['title'].get('text', ''),
                        'content_text': pos['content'].get('text', '')
                    }
                else:
                    # 하위 호환성: 레이어 박스 정보가 없는 경우
                    
                    layer_positions[layer_key] = {
                        'base_y': int(pos['title']['y']),  # 기존 방식
                        'number_y': int(pos['number']['y']),
                        'title_y': int(pos['title']['y']),
                        'content_y': int(pos['content']['y']),
                        'height': int(pos['content']['y'] + pos['content']['height'] - pos['title']['y']),
                        'actual_content_height': int(pos['content']['height'])
                    }

        return layer_positions

    def calculate_required_height(self, layer_positions):
        """필요한 이미지 높이 계산 (동적 레이어 박스 지원, 데이터 양에 따른 하단 여백 최적화)"""
        if not layer_positions:
            return 1500

        max_y = 422  # 기본 상단 높이
        print(f"🔍 높이 계산 시작 - 기본 상단 높이: {max_y}px")
        print(f"🔍 레이어 개수: {len(layer_positions)}개")
        
        for layer_key, pos_info in layer_positions.items():
            # 동적 레이어 박스 정보가 있으면 우선 사용
            if 'layer_box_end' in pos_info:
                layer_bottom = pos_info['layer_box_end']
                print(f"🔍 {layer_key}: layer_box_end = {layer_bottom}px")
            else:
                # 하위 호환성: 기존 방식
                layer_bottom = pos_info['base_y'] + pos_info['height']
                print(f"🔍 {layer_key}: base_y({pos_info['base_y']}) + height({pos_info['height']}) = {layer_bottom}px")
                
            max_y = max(max_y, layer_bottom)
            print(f"🔍 현재 max_y: {max_y}px")

        # 여백만 최소화, 푸터는 원본 크기 유지
        bottom_margin = 10   # 여백만 최소화 (20 → 10)
        bottom_area = 114    # 푸터는 원본 크기 유지 (30 → 114 복원)
        
        required_height = max_y + bottom_margin + bottom_area
        
        print(f"🔍 최종 계산: max_y({max_y}) + bottom_margin({bottom_margin}) + bottom_area({bottom_area}) = {required_height}px")
        print(f"🔍 하단 여백 총합: {bottom_margin + bottom_area}px")
        
        return required_height

    def resize_image(self, original_image, required_height, data_count=0):
        """이미지 높이 동적 조정 (확장/축소 모두 지원, 템플릿 중간 여백 제거)"""
        if not PIL_AVAILABLE:
            return original_image
            
        original_width, original_height = original_image.size
        print(f"🖼️ 이미지 크기 조정 시작 - 원본: {original_width}x{original_height}px")
        print(f"🖼️ 요청된 높이: {required_height}px")
        print(f"🖼️ 데이터 개수: {data_count}개")

        # 푸터 크기 설정 (원본 크기 유지)
        footer_height = 114
        
        if required_height == original_height:
            print(f"🖼️ 크기 조정 불필요 - 원본 크기 그대로 사용")
            return original_image
        elif required_height < original_height:
            print(f"🖼️ 축소 필요 - 템플릿 중간 여백 제거")
            return self._crop_image(original_image, required_height, footer_height)
        else:
            print(f"🖼️ 확장 필요 - 이미지 높이 늘리기")
            return self._extend_image(original_image, required_height, footer_height)
    
    def _crop_image(self, original_image, required_height, footer_height):
        """이미지 축소 - 템플릿 중간 여백 제거"""
        try:
            original_width, original_height = original_image.size
            
            # 새 이미지 생성
            cropped_image = Image.new('RGBA', (original_width, required_height), (255, 255, 255, 255))
            
            # 1. 헤더 영역 복사 (고정: 0~422px)
            header_area = original_image.crop((0, 0, original_width, 422))
            cropped_image.paste(header_area, (0, 0))
            print(f"🖼️ 헤더 영역 복사: 0~422px")
            
            # 2. 콘텐츠 영역 계산 (헤더 다음부터 푸터 직전까지)
            content_start = 422
            content_end = required_height - footer_height
            content_height = content_end - content_start
            
            print(f"🖼️ 콘텐츠 영역: {content_start}~{content_end}px (높이: {content_height}px)")
            
            # 3. 원본에서 콘텐츠 영역 추출 (헤더 바로 다음부터)
            if content_height > 0:
                original_content = original_image.crop((0, 422, original_width, 422 + content_height))
                cropped_image.paste(original_content, (0, content_start))
                print(f"🖼️ 콘텐츠 영역 복사 완료")
            
            # 4. 푸터 영역 복사 (원본 맨 아래에서 가져와서 새 위치에 배치)
            footer_start = required_height - footer_height
            original_footer_start = original_height - 114  # 원본 푸터는 항상 114px
            original_footer = original_image.crop((0, original_footer_start, original_width, original_height))
            
            # 푸터 크기 조정
            if footer_height != 114:
                resized_footer = original_footer.resize((original_width, footer_height))
                cropped_image.paste(resized_footer, (0, footer_start))
                print(f"🖼️ 푸터 리사이즈 후 복사: {footer_start}~{required_height}px (114px → {footer_height}px)")
            else:
                cropped_image.paste(original_footer, (0, footer_start))
                print(f"🖼️ 푸터 원본 크기로 복사: {footer_start}~{required_height}px")
            
            print(f"🖼️ 이미지 축소 완료: {original_width}x{required_height}px")
            return cropped_image
            
        except Exception as e:
            print(f"🖼️ 이미지 축소 실패: {e}")
            return original_image
    
    def _extend_image(self, original_image, required_height, footer_height):
        """이미지 확장 - 기존 로직"""
        try:
            original_width, original_height = original_image.size
            
            extended_image = Image.new('RGBA', (original_width, required_height), (255, 255, 255, 255))

            # 상단 영역 복사 (고정 헤더 영역)
            top_area = original_image.crop((0, 0, original_width, 422))
            extended_image.paste(top_area, (0, 0))
            print(f"🖼️ 헤더 영역 복사 완료: 0~422px")

            # 하단 영역 복사 (동적 푸터 영역)
            bottom_source_start = original_height - 114  # 원본에서는 항상 114로 추출
            bottom_target_start = required_height - footer_height  # 목적지는 동적 크기로 배치
            
            print(f"🖼️ 푸터 설정 - 높이: {footer_height}px")
            print(f"🖼️ 푸터 위치 - 원본: {bottom_source_start}~{original_height}px, 목표: {bottom_target_start}~{required_height}px")
            
            # 원본 푸터를 추출하여 동적 크기로 조정
            original_bottom = original_image.crop((0, bottom_source_start, original_width, original_height))
            
            if footer_height != 114:
                # 푸터 크기가 다르면 리사이즈 적용
                resized_bottom = original_bottom.resize((original_width, footer_height))
                extended_image.paste(resized_bottom, (0, bottom_target_start))
                print(f"🖼️ 푸터 리사이즈 적용: 114px → {footer_height}px")
            else:
                # 기존 크기 그대로 사용
                extended_image.paste(original_bottom, (0, bottom_target_start))
                print(f"🖼️ 푸터 원본 크기 사용: {footer_height}px")

            print(f"🖼️ 이미지 확장 완료: {original_width}x{required_height}px")
            return extended_image
            
        except Exception as e:
            print(f"🖼️ 이미지 확장 실패: {e}")
            return original_image

    def split_and_save_image(self, output_image, chunk_height):
        """이미지를 청크로 분할하여 저장"""
        width, height = output_image.size

        # 출력 디렉토리 생성
        os.makedirs(self.output_dir, exist_ok=True)

        chunk_number = 1
        y_position = 0
        saved_files = []

        while y_position < height:
            # 청크 끝 위치 계산
            end_y = min(y_position + chunk_height, height)

            # 청크 잘라내기
            chunk = output_image.crop((0, y_position, width, end_y))

            # 파일명 생성
            chunk_filename = f"{chunk_number}.png"
            chunk_path = os.path.join(self.output_dir, chunk_filename)

            # 청크 저장
            chunk.save(chunk_path, 'PNG', dpi=(96, 96))
            saved_files.append(chunk_path)

            print(f"청크 {chunk_number} 저장됨: {chunk_filename} (높이: {end_y - y_position}px)")

            # 다음 청크로
            y_position = end_y
            chunk_number += 1

        return saved_files

    def generate_image_from_json(self):
        """JSON에서 이미지 생성 (수정된 실행 순서)"""
        try:
            template = self.excel_file_json

            if not PIL_AVAILABLE:
                return []
                
            original_image = Image.open(self.original_image).convert('RGBA')
            original_width, original_height = original_image.size

            # 이미지 높이를 전달하여 레이어 위치 계산
            layer_positions = self.calculate_layer_positions(template, original_height)

            # 계산된 레이어 위치 기반으로 필요 높이 계산 및 이미지 크기 조정
            required_height = self.calculate_required_height(layer_positions)
            data_count = len(layer_positions)  # 데이터 개수 계산
            image = self.resize_image(original_image, required_height, data_count)
            final_width, final_height = image.size
            
            draw = ImageDraw.Draw(image)

            # 레이어 키를 정렬해서 순서대로 처리
            layer_keys = sorted(template['layers'].keys(), key=lambda x: int(x.replace('layer', '')))

            # PositionSettings 사용 시 위치 데이터 가져오기
            positions_data = None
            if self.position_settings and self.position_settings.is_manual_adjustment_enabled():
                # DataFrame 생성하여 positions 계산
                data_rows = []
                for layer_key in layer_keys:
                    layer_data = template['layers'][layer_key]
                    layer_num = int(layer_key.replace('layer', ''))
                    title = layer_data['title_layer']['text']
                    content = layer_data['content_layer']['text']
                    data_rows.append({
                        '번호': layer_num,
                        '제목': title,
                        '설명': content
                    })
                df = pd.DataFrame(data_rows)
                # 이미지 높이 전달
                positions_data = self.position_settings.calculate_positions(df, image_height=image.size[1])

            for i, layer_key in enumerate(layer_keys):
                layer_data = template['layers'][layer_key]
                layer_pos = layer_positions[layer_key]
                layer_num = int(layer_key.replace('layer', ''))
                

                # 번호 레이어 그리기
                number_info = layer_data['number_layer']['info']
                number_char = layer_data['number_layer']['char']
                number_font = self.get_font(number_char['font_size'], number_char['font_weight'], 'number')
                number_color = tuple(number_char['color'] + [255])
                

                # PositionSettings 사용 시 계산된 X 좌표 적용
                if positions_data and i < len(positions_data):
                    number_x = int(positions_data[i]['number']['x'])
                else:
                    number_x = int(number_info['x'])

                self.draw_text_bold(
                    draw,
                    (int(number_x), layer_pos['number_y']),
                    layer_data['number_layer']['text'],
                    number_font, number_color,
                    False
                )

                # 제목 레이어 그리기
                title_info = layer_data['title_layer']['info']
                title_char = layer_data['title_layer']['char']
                title_font = self.get_font(title_char['font_size'], title_char['font_weight'], 'title')
                title_color = tuple(title_char['color'] + [255])
                title_max_width = int(title_info['width'])
                

                # PositionSettings 사용 시 계산된 X 좌표 적용
                if positions_data and i < len(positions_data):
                    title_x = int(positions_data[i]['title']['x'])
                else:
                    title_x = int(title_info['x'])

                # PositionSettings에서 계산한 줄 수 사용 (동기화)
                title_forced_lines = layer_pos.get('title_lines', None)
                
                self.draw_multiline_text(
                    draw,
                    (title_x, layer_pos['title_y']),
                    layer_data['title_layer']['text'],
                    title_font, title_color, title_max_width,
                    False,
                    forced_lines=title_forced_lines
                )

                # 내용 레이어 그리기
                content_info = layer_data['content_layer']['info']
                content_char = layer_data['content_layer']['char']
                content_font = self.get_font(content_char['font_size'], content_char['font_weight'], 'content')
                content_color = tuple(content_char['color'] + [255])
                content_max_width = int(content_info['width'])
                

                # PositionSettings 사용 시 계산된 X 좌표 적용
                if positions_data and i < len(positions_data):
                    content_x = int(positions_data[i]['content']['x'])
                else:
                    content_x = int(content_info['x'])

                # PositionSettings에서 계산한 줄 수 사용 (동기화)
                content_forced_lines = layer_pos.get('content_lines', None)
                
                self.draw_multiline_text(
                    draw,
                    (content_x, layer_pos['content_y']),
                    layer_data['content_layer']['text'],
                    content_font, content_color, content_max_width,
                    content_char['font_weight'] == 'bold',
                    forced_lines=content_forced_lines
                )

                # 구분선 그리기 (마지막 레이어가 아닌 경우)
                if i < len(layer_keys) - 1:
                    next_layer_key = layer_keys[i + 1]
                    next_layer_pos = layer_positions[next_layer_key]
                    
                    # 통일된 구분선 위치: 현재 레이어 박스 끝과 다음 레이어 박스 시작의 정중앙 (정수 연산)
                    if 'layer_box_end' in layer_pos and 'layer_box_start' in next_layer_pos:
                        current_end = int(layer_pos['layer_box_end'])
                        next_start = int(next_layer_pos['layer_box_start'])
                        # 정확한 중앙점 계산 - 부동소수점 오차 제거
                        separator_y = int(current_end + (next_start - current_end) // 2)
                    else:
                        # Fallback: 레이어 간격의 중앙 (정수 연산)
                        layer_spacing = self.position_settings.get_setting('layer_spacing') if self.position_settings else 20
                        separator_y = int(int(layer_pos['base_y']) + int(layer_pos['height']) + layer_spacing // 2)

                    # 이미지 전체 너비로 구분선 그리기
                    image_width = image.size[0]
                    draw.line([(0, separator_y), (image_width, separator_y)], fill=(200, 200, 200, 255), width=1)

            # 이미지 저장
            image.save(self.output_image, 'PNG', dpi=(96, 96))

            # 청크 분할 저장
            result_files = [self.output_image]  # 원본 이미지 경로

            if self.split_chunks:
                chunk_files = self.split_and_save_image(image, self.chunk_height)
                result_files.extend(chunk_files)

            return result_files
        except Exception as e:
            raise e
