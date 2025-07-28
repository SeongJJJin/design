"""
고급 위치 조정 기능을 시각적으로 설명하는 도움말 다이어그램 생성기
"""

from PIL import Image, ImageDraw, ImageFont
import os


class HelpDiagramGenerator:
    """도움말 다이어그램 생성 클래스"""
    
    def __init__(self, width=1000, height=1200):
        self.width = width
        self.height = height
        # 배경을 밝은 회색으로 변경하여 대비 향상
        self.image = Image.new('RGB', (width, height), '#F8F9FA')
        self.draw = ImageDraw.Draw(self.image)
        
        # 색상 정의 - 대비를 크게 개선
        self.colors = {
            'title': '#1E3A8A',        # 진한 파란색 (더 진하게)
            'text': '#1F2937',         # 거의 검정 (더 진하게)
            'arrow': '#DC2626',        # 빨간색 (더 진하게)
            'dimension': '#DC2626',    # 빨간색 (더 진하게)
            'background': '#FFFFFF',   # 순백색
            'layer': '#DBEAFE',        # 연한 파란색 (더 진하게)
            'layer_highlight': '#FEF3C7',  # 노란색 (강조용)
            'number': '#EA580C',       # 주황색 (더 진하게)
            'separator': '#6B7280',    # 회색 (더 진하게)
            'label_bg': '#FFFFFF',     # 라벨 배경
            'border': '#374151'        # 테두리색
        }
        
        # 폰트 크기 - 모든 크기를 크게 증가
        self.font_sizes = {
            'title': 32,      # 24 → 32
            'subtitle': 24,   # 18 → 24
            'normal': 18,     # 14 → 18
            'small': 16,      # 12 → 16
            'large': 20       # 새로 추가
        }
    
    def get_font(self, size):
        """폰트 가져오기"""
        try:
            # 시스템 폰트 시도
            return ImageFont.truetype("malgun.ttf", size)
        except:
            try:
                return ImageFont.truetype("arial.ttf", size)
            except:
                return ImageFont.load_default()
    
    def draw_title(self, text, y=30):
        """제목 그리기"""
        font = self.get_font(self.font_sizes['title'])
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        self.draw.text((x, y), text, fill=self.colors['title'], font=font)
        return y + bbox[3] - bbox[1] + 20
    
    def draw_subtitle(self, text, y):
        """부제목 그리기"""
        font = self.get_font(self.font_sizes['subtitle'])
        self.draw.text((30, y), text, fill=self.colors['title'], font=font)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        return y + bbox[3] - bbox[1] + 15
    
    def draw_text(self, text, x, y, color='text'):
        """일반 텍스트 그리기"""
        font = self.get_font(self.font_sizes['normal'])
        self.draw.text((x, y), text, fill=self.colors[color], font=font)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]
    
    def draw_arrow_with_label(self, start_x, start_y, end_x, end_y, label, offset=15):
        """라벨이 있는 화살표 그리기 (개선된 버전)"""
        # 더 굵은 화살표 그리기
        self.draw.line([(start_x, start_y), (end_x, end_y)], fill=self.colors['arrow'], width=4)
        
        # 더 큰 화살표 머리 그리기
        arrow_size = 8
        if end_y > start_y:  # 아래쪽 화살표
            self.draw.polygon([(end_x-arrow_size, end_y-arrow_size*2), 
                             (end_x+arrow_size, end_y-arrow_size*2), 
                             (end_x, end_y)], 
                            fill=self.colors['arrow'])
        else:  # 위쪽 화살표
            self.draw.polygon([(end_x-arrow_size, end_y+arrow_size*2), 
                             (end_x+arrow_size, end_y+arrow_size*2), 
                             (end_x, end_y)], 
                            fill=self.colors['arrow'])
        
        # 더 큰 라벨 그리기
        font = self.get_font(self.font_sizes['normal'])  # small → normal
        bbox = self.draw.textbbox((0, 0), label, font=font)
        label_width = bbox[2] - bbox[0]
        label_height = bbox[3] - bbox[1]
        
        label_x = start_x + offset
        label_y = (start_y + end_y) // 2 - label_height // 2
        
        # 더 눈에 띄는 라벨 배경 (그림자 효과)
        shadow_offset = 2
        self.draw.rectangle([label_x+shadow_offset, label_y+shadow_offset, 
                           label_x+label_width+8+shadow_offset, label_y+label_height+4+shadow_offset], 
                          fill='#00000020')  # 반투명 그림자
        
        # 라벨 배경 (더 큰 패딩)
        self.draw.rectangle([label_x-4, label_y-2, label_x+label_width+8, label_y+label_height+4], 
                          fill=self.colors['label_bg'], outline=self.colors['arrow'], width=2)
        
        # 라벨 텍스트
        self.draw.text((label_x+2, label_y+1), label, fill=self.colors['arrow'], font=font)
    
    def draw_dimension_line(self, start_x, start_y, end_x, end_y, label, side='right'):
        """치수선 그리기 (개선된 버전)"""
        # 더 굵은 치수선
        self.draw.line([(start_x, start_y), (end_x, end_y)], fill=self.colors['dimension'], width=3)
        
        # 더 큰 양쪽 끝 표시
        line_size = 6
        self.draw.line([(start_x-line_size, start_y), (start_x+line_size, start_y)], 
                      fill=self.colors['dimension'], width=3)
        self.draw.line([(end_x-line_size, end_y), (end_x+line_size, end_y)], 
                      fill=self.colors['dimension'], width=3)
        
        # 더 큰 라벨
        font = self.get_font(self.font_sizes['normal'])  # small → normal
        bbox = self.draw.textbbox((0, 0), label, font=font)
        label_width = bbox[2] - bbox[0]
        label_height = bbox[3] - bbox[1]
        
        if side == 'right':
            label_x = max(start_x, end_x) + 15
        else:
            label_x = min(start_x, end_x) - label_width - 15
        
        label_y = (start_y + end_y) // 2 - label_height // 2
        
        # 라벨 배경 (그림자 효과)
        shadow_offset = 2
        self.draw.rectangle([label_x+shadow_offset, label_y+shadow_offset, 
                           label_x+label_width+6+shadow_offset, label_y+label_height+4+shadow_offset], 
                          fill='#00000020')
        
        # 라벨 배경
        self.draw.rectangle([label_x-3, label_y-2, label_x+label_width+6, label_y+label_height+4], 
                          fill=self.colors['label_bg'], outline=self.colors['dimension'], width=2)
        
        self.draw.text((label_x+1, label_y+1), label, fill=self.colors['dimension'], font=font)
    
    def draw_layer_example(self, x, y, width, height, number, title, content, highlight=False):
        """레이어 예시 그리기 (개선된 버전)"""
        # 그림자 효과
        shadow_offset = 3
        self.draw.rectangle([x+shadow_offset, y+shadow_offset, x+width+shadow_offset, y+height+shadow_offset], 
                          fill='#00000015')
        
        # 배경 - 더 진한 색상
        bg_color = self.colors['layer_highlight'] if highlight else self.colors['layer']
        border_color = self.colors['arrow'] if highlight else self.colors['border']
        border_width = 3 if highlight else 2
        
        self.draw.rectangle([x, y, x+width, y+height], 
                          fill=bg_color, outline=border_color, width=border_width)
        
        # 번호 - 더 크고 눈에 띄게
        font_number = self.get_font(self.font_sizes['large'])  # 20pt
        number_bg_size = 35
        # 번호 배경 원
        self.draw.ellipse([x+10, y+8, x+10+number_bg_size, y+8+number_bg_size], 
                         fill=self.colors['number'], outline=self.colors['text'], width=2)
        
        # 번호 텍스트를 중앙에 정렬
        bbox = self.draw.textbbox((0, 0), number, font=font_number)
        number_width = bbox[2] - bbox[0]
        number_height = bbox[3] - bbox[1]
        number_x = x + 10 + (number_bg_size - number_width) // 2
        number_y = y + 8 + (number_bg_size - number_height) // 2
        self.draw.text((number_x, number_y), number, fill='white', font=font_number)
        
        # 제목 - 더 크고 진하게
        font_title = self.get_font(self.font_sizes['normal'])  # 18pt
        self.draw.text((x+60, y+12), title, fill=self.colors['title'], font=font_title)
        
        # 내용 - 더 크고 읽기 쉽게
        font_content = self.get_font(self.font_sizes['small'])  # 16pt
        self.draw.text((x+60, y+40), content, fill=self.colors['text'], font=font_content)
        
        return height
    
    def generate_diagram(self):
        """전체 다이어그램 생성 (개선된 버전)"""
        current_y = 20
        
        # 제목
        current_y = self.draw_title("🎯 고급 위치 조정 기능 가이드")
        current_y += 30
        
        # 섹션 1: 전체 구조
        current_y = self.draw_subtitle("📐 전체 레이아웃 구조", current_y)
        current_y += 10
        
        # 템플릿 영역 표시 (더 눈에 띄게)
        template_y = current_y
        self.draw.rectangle([50, template_y, 900, template_y+100], 
                          fill=self.colors['background'], 
                          outline=self.colors['border'], width=3)
        # 템플릿 영역 라벨
        font_template = self.get_font(self.font_sizes['normal'])
        self.draw.text((70, template_y+35), "📄 템플릿 이미지 영역 (로고, 헤더 등)", 
                      fill=self.colors['text'], font=font_template)
        
        # 시작 Y 좌표 표시 (더 명확하게)
        start_y_pos = template_y + 130
        self.draw_arrow_with_label(30, template_y+100, 30, start_y_pos, 
                                 "시작 Y 좌표\n(기본: 480.9px)", offset=40)
        
        # 레이어들 그리기 (더 큰 크기)
        layer_y = start_y_pos
        layer_width = 700
        layer_height = 80  # 높이 증가
        
        # 첫 번째 레이어
        self.draw_layer_example(120, layer_y, layer_width, layer_height, "01", "안전수칙 준수", 
                               "작업 시 반드시 안전모를 착용하세요")
        
        # 레이어 간격 표시 (더 명확하게)
        gap_y = layer_y + layer_height
        gap_height = 50  # 간격 증가
        self.draw_dimension_line(870, gap_y, 870, gap_y+gap_height, 
                               "레이어 간격\n(기본: 40px)")
        
        # 두 번째 레이어 (강조)
        layer_y += layer_height + gap_height
        self.draw_layer_example(120, layer_y, layer_width, layer_height, "02", "작업 전 점검", 
                               "장비 상태를 확인하고 이상 유무를 점검하세요", True)
        
        # X 좌표 표시 (겹치지 않게 수정)
        arrow_start_y = layer_y - 60  # 더 위쪽으로 이동
        
        # 번호 X 좌표 (왼쪽)
        self.draw_arrow_with_label(40, arrow_start_y, 135, layer_y+15, 
                                 "번호 X\n(67.25px)", offset=-100)
        
        # 제목 X 좌표 (중간)
        self.draw_arrow_with_label(40, arrow_start_y+25, 180, layer_y+15, 
                                 "제목 X\n(145.25px)", offset=-100)
        
        # 내용 X 좌표 (아래쪽에서 표시)
        self.draw_arrow_with_label(40, layer_y+50, 180, layer_y+50, 
                                 "내용 X\n(146.77px)", offset=-100)
        
        # 제목-내용 간격 표시 (더 명확하게)
        self.draw_dimension_line(850, layer_y+30, 850, layer_y+50, 
                               "제목-내용 간격\n(기본: 10px)")
        
        # 구분선 (더 눈에 띄게)
        separator_y = layer_y + layer_height + 30
        self.draw.line([(120, separator_y), (820, separator_y)], 
                      fill=self.colors['separator'], width=3)
        self.draw_text("▲ 구분선 (전체 너비로 확장)", 120, separator_y+10, 'dimension')
        
        current_y = separator_y + 60
        
        # 섹션 2: 개별 레이어 조정 (더 명확하게)
        current_y = self.draw_subtitle("🎛️ 개별 레이어 위치 조정", current_y)
        current_y += 10
        
        # 일반 레이어
        normal_layer_y = current_y
        self.draw_layer_example(120, normal_layer_y, layer_width, layer_height, "03", "일반 레이어", 
                              "기본 위치에 배치된 레이어")
        
        # 조정된 레이어 (더 많이 이동)
        offset_x = 40  # 20 → 40
        offset_y = 20  # 10 → 20
        adjusted_layer_y = normal_layer_y + layer_height + 40
        self.draw_layer_example(120 + offset_x, adjusted_layer_y + offset_y, layer_width, layer_height, 
                              "04", "조정된 레이어", 
                              f"X 오프셋 +{offset_x}px, Y 오프셋 +{offset_y}px 적용", True)
        
        # 오프셋 표시 (겹치지 않게 수정)
        # X 오프셋 화살표 (가로)
        middle_y = adjusted_layer_y + offset_y + layer_height//2
        self.draw_arrow_with_label(120, middle_y, 
                                 120 + offset_x, middle_y, 
                                 f"X 오프셋\n+{offset_x}px", offset=10)
        
        # Y 오프셋 화살표 (세로) - 왼쪽으로 이동
        self.draw_arrow_with_label(50, normal_layer_y + layer_height, 
                                 50, adjusted_layer_y + offset_y, 
                                 f"Y 오프셋\n+{offset_y}px", offset=15)
        
        current_y = adjusted_layer_y + offset_y + layer_height + 30
        
        # 섹션 3: 핵심 포인트 (간결하게)
        current_y = self.draw_subtitle("💡 핵심 사용법", current_y)
        current_y += 10
        
        # 핵심 포인트들을 박스로 표시 (새로운 기능 추가)
        tips = [
            "🔧 기본 설정: 전체적인 위치 조정",
            "🎯 개별 조정: 특정 레이어만 따로 이동",
            "📏 세밀한 간격: 제목 상단/내용 하단 간격 개별 조정",
            "💾 저장/불러오기: 프리셋으로 관리",
            "🔄 실시간 조정: 도움말 보며 동시 수정 가능"
        ]
        
        tip_y = current_y
        for i, tip in enumerate(tips):
            # 팁 박스 배경
            tip_height = 35
            self.draw.rectangle([80, tip_y, 880, tip_y + tip_height], 
                              fill=self.colors['layer'], 
                              outline=self.colors['border'], width=2)
            
            # 팁 텍스트
            font_tip = self.get_font(self.font_sizes['normal'])
            self.draw.text((100, tip_y + 8), tip, fill=self.colors['text'], font=font_tip)
            tip_y += tip_height + 10
        
        return self.image
    
    def save_diagram(self, file_path):
        """다이어그램을 파일로 저장"""
        diagram = self.generate_diagram()
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        diagram.save(file_path, 'PNG', dpi=(96, 96))
        return file_path


def create_help_diagram(output_path):
    """도움말 다이어그램 생성 함수"""
    generator = HelpDiagramGenerator()
    return generator.save_diagram(output_path)


if __name__ == "__main__":
    # 테스트용
    output_path = "help_diagram.png"
    create_help_diagram(output_path)
    print(f"도움말 다이어그램이 생성되었습니다: {output_path}")