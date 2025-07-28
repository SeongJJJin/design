"""
건설사별 테마 색상 관리 클래스
각 건설사별로 정의된 브랜드 색상을 RGB 값으로 관리합니다.
"""

from typing import List, Dict, Optional


class CompanyColorManager:
    """건설사별 테마 색상을 관리하는 클래스"""
    
    # 건설사별 색상 맵핑 (HEX → RGB 변환)
    COMPANY_COLORS = {
        '계룡': [9, 114, 206],        # #0972CE
        '극동': [17, 100, 168],       # #1164A8
        '남광토건': [14, 81, 101],    # #0E5165
        '남해': [24, 48, 118],        # #183076
        '동원': [144, 21, 73],        # #901549
        '모아주택산업': [0, 4, 108],  # #00046C
        '서영': [85, 185, 93],        # #55B95D
        '서한': [29, 144, 207],       # #1D90CF
        '서희': [0, 80, 146],         # #005092
        '신세계': [216, 12, 24],      # #D80C18
        '제주특별자치도개발공사': [60, 61, 61],  # #3C3D3D
        '호반': [238, 117, 0],        # #EE7500 (기존 기본값)
        '화성': [201, 22, 31],        # #C9161F
        '효성': [32, 42, 104],        # #202A68
        '진흥': [34, 71, 153],        # #224799
    }
    
    # 기본 색상 (호반건설)
    DEFAULT_COLOR = [238, 117, 0]  # #EE7500
    
    @classmethod
    def get_color(cls, company_name: str) -> List[int]:
        """
        건설사명으로 테마 색상을 조회합니다.
        
        Args:
            company_name (str): 건설사명
            
        Returns:
            List[int]: RGB 색상 값 [R, G, B]
        """
        if not company_name:
            return cls.DEFAULT_COLOR.copy()
            
        # 정확한 매치 먼저 시도
        if company_name in cls.COMPANY_COLORS:
            return cls.COMPANY_COLORS[company_name].copy()
        
        # 부분 매치 시도 (건설사명이 포함된 경우)
        for company, color in cls.COMPANY_COLORS.items():
            if company in company_name or company_name in company:
                return color.copy()
        
        # 매치되지 않으면 기본값 반환
        return cls.DEFAULT_COLOR.copy()
    
    @classmethod
    def get_available_companies(cls) -> List[str]:
        """
        지원되는 모든 건설사 목록을 반환합니다.
        
        Returns:
            List[str]: 건설사명 목록
        """
        return list(cls.COMPANY_COLORS.keys())
    
    @classmethod
    def get_color_info(cls, company_name: str) -> Dict[str, any]:
        """
        건설사의 상세 색상 정보를 반환합니다.
        
        Args:
            company_name (str): 건설사명
            
        Returns:
            Dict: 색상 정보 딕셔너리
        """
        rgb_color = cls.get_color(company_name)
        hex_color = cls._rgb_to_hex(rgb_color)
        
        return {
            'company': company_name,
            'rgb': rgb_color,
            'hex': hex_color,
            'is_default': company_name not in cls.COMPANY_COLORS,
            'matched_company': cls._find_matched_company(company_name)
        }
    
    @classmethod
    def _rgb_to_hex(cls, rgb: List[int]) -> str:
        """RGB 값을 HEX 문자열로 변환"""
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    
    @classmethod
    def _find_matched_company(cls, company_name: str) -> Optional[str]:
        """실제로 매치된 건설사명을 찾아 반환"""
        if company_name in cls.COMPANY_COLORS:
            return company_name
            
        for company in cls.COMPANY_COLORS.keys():
            if company in company_name or company_name in company:
                return company
                
        return None
    
    @classmethod
    def add_custom_color(cls, company_name: str, rgb_color: List[int]):
        """
        사용자 정의 건설사 색상을 추가합니다.
        
        Args:
            company_name (str): 건설사명
            rgb_color (List[int]): RGB 색상 값 [R, G, B]
        """
        if len(rgb_color) != 3 or not all(0 <= c <= 255 for c in rgb_color):
            raise ValueError("RGB 색상은 [R, G, B] 형태의 0-255 범위 값이어야 합니다.")
        
        cls.COMPANY_COLORS[company_name] = rgb_color.copy()
    
    @classmethod
    def get_color_preview_text(cls, company_name: str) -> str:
        """색상 미리보기용 텍스트 반환"""
        color_info = cls.get_color_info(company_name)
        rgb = color_info['rgb']
        hex_val = color_info['hex']
        
        if color_info['is_default']:
            return f"기본 색상: {hex_val} (RGB: {rgb})"
        else:
            matched = color_info['matched_company']
            if matched == company_name:
                return f"{company_name}: {hex_val} (RGB: {rgb})"
            else:
                return f"{matched} 색상 적용: {hex_val} (RGB: {rgb})"