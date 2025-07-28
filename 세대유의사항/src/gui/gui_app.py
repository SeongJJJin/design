import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import tempfile
import shutil
import zipfile
import threading
from datetime import datetime
import gc
# pandas는 필요시에만 지연 임포트
import io
import subprocess
import platform

from src.core.local_file_manager import LocalFileManager
from src.core.json_to_image import JsonToImage
from src.core.excel_to_json import ExelToJson
from src.core.position_settings import PositionSettings
from src.utils.company_colors import CompanyColorManager


class ImageGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("이미지 생성기")
        self.root.geometry("600x500")  # 단순화된 GUI에 맞는 기본 크기
        self.root.minsize(600, 450)  # 최소 창 크기 설정
        self.root.resizable(True, True)

        # 파일 관리자 초기화
        self.file_manager = LocalFileManager()

        # 위치 설정 초기화
        self.position_settings = PositionSettings()
        # self.position_settings.enable_manual_adjustment(True)  # 간격 설정값 적용을 위해 활성화

        # 변수 초기화
        self.excel_file_path = tk.StringVar()
        self.template_file_path = tk.StringVar()
        self.construction_name = tk.StringVar()
        self.selected_template = tk.StringVar()
        self.output_directory = tk.StringVar()
        self.current_company_color = tk.StringVar(value="기본 색상: #EE7500")
        # 기본값 설정 - 프로젝트 폴더의 output 디렉토리
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        output_dir = os.path.join(project_root, "output")
        os.makedirs(output_dir, exist_ok=True)
        self.output_directory.set(output_dir)

        self.setup_ui()
        self.check_requirements()
        self.refresh_template_list()
        
        # 초기 색상 표시 설정
        self.update_color_display("호반")

    def setup_ui(self):
        """UI 구성"""
        # 스크롤 가능한 메인 영역 생성
        self.setup_scrollable_main_area()

        # 메인 프레임을 스크롤 가능한 영역에 생성
        main_frame = ttk.Frame(self.scrollable_frame, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 그리드 설정 - 반응형 레이아웃
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)  # 메인 콘텐츠 열 확장
        main_frame.columnconfigure(2, weight=0)  # 버튼 열은 고정 크기

        row = 0

        # 제목
        title_label = ttk.Label(main_frame, text="주의사항 이미지 생성기", font=("맑은 고딕", 16, "bold"))
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 20))
        row += 1

        # 엑셀 파일 선택
        ttk.Label(main_frame, text="엑셀 파일:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.excel_file_path).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="파일 선택", command=self.select_excel_file).grid(row=row, column=2, pady=5)
        row += 1

        # 템플릿 선택
        ttk.Label(main_frame, text="템플릿 선택:").grid(row=row, column=0, sticky=tk.W, pady=5)
        template_frame = ttk.Frame(main_frame)
        template_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        template_frame.columnconfigure(0, weight=1)

        # 템플릿 콤보박스
        self.template_combobox = ttk.Combobox(template_frame, textvariable=self.selected_template, state="readonly")
        self.template_combobox.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.template_combobox.bind('<<ComboboxSelected>>', self.on_template_selected)

        # 새로고침 및 직접 선택 버튼
        button_frame = ttk.Frame(template_frame)
        button_frame.grid(row=0, column=1)
        ttk.Button(button_frame, text="새로고침", command=self.refresh_template_list).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="직접 선택", command=self.select_template_file).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        # 선택된 건설사 색상 정보 표시
        ttk.Label(main_frame, text="테마 색상:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        # 색상 표시 프레임 생성
        color_frame = ttk.Frame(main_frame)
        color_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=(10, 5), pady=5)
        
        # 색상 미리보기 Canvas (20x20 픽셀)
        self.color_preview_canvas = tk.Canvas(color_frame, width=20, height=20, highlightthickness=1, highlightbackground="gray")
        self.color_preview_canvas.pack(side=tk.LEFT, padx=(0, 10))
        
        # 색상 정보 라벨 (동적 색상 적용)
        self.color_info_label = tk.Label(color_frame, textvariable=self.current_company_color, font=("맑은 고딕", 9))
        self.color_info_label.pack(side=tk.LEFT)
        row += 1

        # 건설사명 입력 (참고용)
        ttk.Label(main_frame, text="건설사명 (참고):").grid(row=row, column=0, sticky=tk.W, pady=5)
        construction_entry = ttk.Entry(main_frame, textvariable=self.construction_name)
        construction_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        row += 1

        # 출력 디렉토리 선택
        ttk.Label(main_frame, text="저장 위치:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_directory).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="폴더 선택", command=self.select_output_directory).grid(row=row, column=2, pady=5)
        row += 1

        # 구분선
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        row += 1

        # 생성 버튼
        self.generate_button = ttk.Button(
            main_frame,
            text="이미지 생성하기",
            command=self.start_generation,
            state="disabled"
        )
        self.generate_button.grid(row=row, column=0, columnspan=3, pady=10)
        row += 1

        # 진행률 표시
        self.progress_var = tk.StringVar(value="준비됨")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=row, column=0, columnspan=3, pady=5)
        row += 1

        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # 로그 영역
        log_frame = ttk.LabelFrame(main_frame, text="처리 로그", padding="10")
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        main_frame.rowconfigure(row, weight=1)

        # 고급 설정 제거로 초기화 생략

    def setup_scrollable_main_area(self):
        """스크롤 가능한 메인 영역 설정"""
        # 캔버스와 스크롤바 생성
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # 스크롤 가능한 프레임의 크기가 변경될 때 캔버스의 스크롤 영역 업데이트
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # 캔버스 너비 변경 시 scrollable_frame 너비 동적 조정
        def on_canvas_configure(event):
            # scrollable_frame의 너비를 canvas 너비에 맞춤
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window_id, width=canvas_width)
        
        self.canvas.bind('<Configure>', on_canvas_configure)
        
        # 스크롤 가능한 프레임을 캔버스에 추가
        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 캔버스와 스크롤바 배치
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 마우스 휠 스크롤 이벤트 바인딩
        self.bind_mousewheel()

    def bind_mousewheel(self):
        """마우스 휠 스크롤 이벤트 바인딩"""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")

        # 마우스가 캔버스 위에 있을 때만 스크롤 활성화
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)

    def log_message(self, message):
        """로그 메시지 추가"""
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def check_requirements(self):
        """필수 파일 확인"""
        missing_files = self.file_manager.validate_files()
        if missing_files:
            message = "다음 파일들이 누락되어 있습니다:\n" + "\n".join(missing_files)
            message += "\n\n폰트 파일과 템플릿 파일을 해당 폴더에 넣어주세요."
            self.log_message("⚠️ 필수 파일 누락 확인됨")
            messagebox.showwarning("필수 파일 누락", message)
        else:
            self.log_message("✅ 모든 필수 파일이 준비되었습니다")

    def refresh_template_list(self):
        """템플릿 목록 새로고침"""
        try:
            available_templates = self.file_manager.get_available_templates()

            # 콤보박스 값 설정
            self.template_combobox['values'] = available_templates

            if available_templates:
                self.log_message(f"📂 {len(available_templates)}개의 템플릿을 찾았습니다")

                # 기본 선택 (첫 번째 템플릿)
                if not self.selected_template.get() or self.selected_template.get() not in available_templates:
                    self.selected_template.set(available_templates[0])
                    self.on_template_selected()
            else:
                self.log_message("⚠️ templates/ 폴더에 템플릿 파일이 없습니다")
                self.template_combobox['values'] = ["템플릿 없음"]
                self.selected_template.set("템플릿 없음")
                self.template_file_path.set("")
                
        except Exception as e:
            self.log_message(f"⚠️ 템플릿 목록 로드 중 오류: {str(e)}")

    def on_template_selected(self, event=None):
        """템플릿 선택 시 호출"""
        selected = self.selected_template.get()
        if selected and selected != "템플릿 없음":
            # 실제 템플릿 파일 경로 찾기 (.jpg 및 .png 지원)
            template_path = self.file_manager.find_template_file_path(selected)

            if template_path:
                self.template_file_path.set(template_path)
                self.construction_name.set(selected)  # 건설사명도 자동 설정
                
                # 건설사별 색상 정보 업데이트
                color_info = CompanyColorManager.get_color_preview_text(selected)
                self.current_company_color.set(color_info)
                self.update_color_display(selected)  # 시각적 색상 업데이트
                
                template_filename = os.path.basename(template_path)
                self.log_message(f"✅ 템플릿 선택됨: {template_filename}")
                self.log_message(f"🎨 {color_info}")
            else:
                self.template_file_path.set("")
                self.current_company_color.set("기본 색상: #EE7500")
                self.update_color_display("호반")  # 기본 색상으로 복원
                self.log_message(f"❌ 템플릿 파일을 찾을 수 없음: {selected}")
        else:
            self.template_file_path.set("")
            self.current_company_color.set("기본 색상: #EE7500")
            self.update_color_display("호반")  # 기본 색상으로 복원

        self.update_generate_button_state()

    def update_color_display(self, company_name):
        """건설사별 색상을 GUI에 동적으로 표시"""
        try:
            # 건설사 색상 정보 가져오기
            color_info = CompanyColorManager.get_color_info(company_name)
            rgb_color = color_info['rgb']
            hex_color = color_info['hex']
            
            # Canvas에 색상 사각형 그리기
            self.color_preview_canvas.delete("all")
            self.color_preview_canvas.create_rectangle(2, 2, 18, 18, fill=hex_color, outline="gray")
            
            # 색상 밝기 계산하여 텍스트 색상 결정
            brightness = (rgb_color[0] * 0.299 + rgb_color[1] * 0.587 + rgb_color[2] * 0.114)
            text_color = "white" if brightness < 128 else "black"
            
            # 라벨 색상 업데이트
            self.color_info_label.configure(foreground=hex_color, background="white")
            
        except Exception as e:
            # 오류 시 기본 색상으로 복원
            self.color_preview_canvas.delete("all")
            self.color_preview_canvas.create_rectangle(2, 2, 18, 18, fill="#EE7500", outline="gray")
            self.color_info_label.configure(foreground="#EE7500", background="white")

    def select_excel_file(self):
        """엑셀 파일 선택"""
        file_path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.excel_file_path.set(file_path)
            self.log_message(f"엑셀 파일 선택됨: {os.path.basename(file_path)}")
            self.update_generate_button_state()

            # 자동으로 컬럼 분석
            self.analyze_excel_columns(file_path)

    def analyze_excel_columns(self, file_path):
        """엑셀 파일의 컬럼 구조 분석"""
        try:
            # 더미 ExelToJson 객체로 컬럼 매핑 테스트
            with open(file_path, 'rb') as f:
                excel_file = io.BytesIO(f.read())

            # 현재 선택된 건설사명 가져오기
            current_company = self.construction_name.get().strip()
            processor = ExelToJson(excel_file, position_settings=self.position_settings, company_name=current_company)

            # 여러 헤더 위치 테스트
            file_contents = excel_file.getvalue()
            file_like = io.BytesIO(file_contents)

            for header_row in [0, 1, 2]:
                try:
                    import pandas as pd  # 지연 임포트
                    temp_df = pd.read_excel(file_like, header=header_row)
                    file_like.seek(0)

                    mapping = processor.find_column_mapping(temp_df)
                    if len(mapping) >= 2:
                        self.log_message(f"📊 컬럼 매핑 (헤더 행 {header_row}): {mapping}")
                        break
                except Exception as e:
                    print(e)
                    continue
            else:
                self.log_message("⚠️ 적절한 컬럼을 찾을 수 없습니다")

        except Exception as e:
            self.log_message(f"⚠️ 엑셀 분석 중 오류: {str(e)}")

    def select_template_file(self):
        """템플릿 파일 직접 선택"""
        file_path = filedialog.askopenfilename(
            title="템플릿 이미지 선택",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("PNG files", "*.png"), ("JPG files", "*.jpg *.jpeg"), ("All files", "*.*")]
        )
        if file_path:
            self.template_file_path.set(file_path)

            # 파일명에서 건설사명 추출 시도
            filename = os.path.basename(file_path)
            filename_no_ext = os.path.splitext(filename)[0]
            
            # "_템플릿" 제거하여 건설사명 추출
            if filename_no_ext.endswith('_템플릿'):
                company_name = filename_no_ext.replace('_템플릿', '')
            else:
                company_name = filename_no_ext
            
            # 콤보박스를 "직접 선택됨"으로 설정
            self.selected_template.set(f"직접 선택: {filename}")
            self.construction_name.set(company_name)
            
            # 추출된 건설사명으로 색상 정보 업데이트
            color_info = CompanyColorManager.get_color_preview_text(company_name)
            self.current_company_color.set(color_info)
            self.update_color_display(company_name)  # 시각적 색상 업데이트

            self.log_message(f"📁 템플릿 파일 직접 선택됨: {filename}")
            self.log_message(f"🎨 {color_info}")
            self.update_generate_button_state()

    def select_output_directory(self):
        """출력 디렉토리 선택"""
        directory = filedialog.askdirectory(title="저장 위치 선택")
        if directory:
            self.output_directory.set(directory)
            self.log_message(f"저장 위치 변경됨: {directory}")

    def update_generate_button_state(self):
        """생성 버튼 활성화 상태 업데이트"""
        excel_selected = bool(self.excel_file_path.get().strip())
        template_selected = bool(self.template_file_path.get().strip())
        template_is_valid = self.selected_template.get() != "템플릿 없음"

        if excel_selected and template_selected and template_is_valid:
            self.generate_button.config(state="normal")
        else:
            self.generate_button.config(state="disabled")

    def start_generation(self):
        """이미지 생성 시작"""
        # 버튼 비활성화
        self.generate_button.config(state="disabled")
        self.progress_bar.start(10)
        self.progress_var.set("이미지 생성 중...")

        # 별도 스레드에서 실행
        thread = threading.Thread(target=self.generate_images, daemon=True)
        thread.start()

    def generate_images(self):
        """이미지 생성 (별도 스레드에서 실행)"""
        temp_dir = None
        try:
            # 임시 디렉토리 생성
            temp_dir = tempfile.mkdtemp()
            temp_fonts_path = os.path.join(temp_dir, 'fonts')
            temp_result_path = os.path.join(temp_dir, 'result')

            os.makedirs(temp_result_path, exist_ok=True)

            self.root.after(0, lambda: self.log_message("🔄 폰트 파일 준비 중..."))
            self.file_manager.setup_fonts(temp_fonts_path)

            self.root.after(0, lambda: self.log_message("📊 엑셀 파일 처리 중..."))
            # 건설사명 가져오기
            company_name = self.construction_name.get().strip()
            if company_name:
                color_info = CompanyColorManager.get_color_info(company_name)
                self.root.after(0, lambda: self.log_message(f"🎨 {company_name} 테마 색상 적용: {color_info['hex']}"))
            
            excel_file_json = self.file_manager.process_excel(self.excel_file_path.get(), self.position_settings, company_name)

            self.root.after(0, lambda: self.log_message("🖼️ 템플릿 파일 준비 중..."))
            template_path = self.template_file_path.get()

            # 이미지 생성
            self.root.after(0, lambda: self.log_message("🎨 이미지 생성 중..."))
            output_file_path = os.path.join(temp_result_path, 'output.png')

            image_generator = JsonToImage(
                excel_file_json,
                output_file_path,
                template_path,
                split_chunks=True,
                chunk_height=2000,
                fonts_path=temp_fonts_path,
                output_dir=temp_result_path,
                position_settings=self.position_settings
            )

            result_files = image_generator.generate_image_from_json()

            if result_files and len(result_files) > 0:
                self.root.after(0, lambda: self.log_message("📁 이미지 파일을 바탕화면에 저장 중..."))
                
                # 바탕화면에 직접 PNG 파일들 복사
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 건설사명 결정
                selected_template = self.selected_template.get()
                if selected_template.startswith("직접 선택:"):
                    construction_name = self.construction_name.get().strip() or "사용자지정"
                else:
                    construction_name = selected_template
                
                # 바탕화면에 PNG 파일들 직접 저장
                saved_files = []
                for i, png_file in enumerate([f for f in os.listdir(temp_result_path) if f.endswith('.png')], 1):
                    src_path = os.path.join(temp_result_path, png_file)
                    if png_file == 'output.png':
                        # 원본 이미지
                        dest_filename = f'{construction_name}_{timestamp}_전체.png'
                    else:
                        # 청크 파일들 (1.png, 2.png 등)
                        dest_filename = f'{construction_name}_{timestamp}_{png_file}'
                    
                    dest_path = os.path.join(self.output_directory.get(), dest_filename)
                    shutil.copy2(src_path, dest_path)
                    saved_files.append(dest_filename)
                
                # 생성된 파일 정보 로깅
                total_files = len(saved_files)
                self.root.after(0, lambda: self.log_message(f"✅ 완료! 총 {total_files}개 이미지가 바탕화면에 저장됨"))
                for filename in saved_files:
                    self.root.after(0, lambda f=filename: self.log_message(f"📁 저장됨: {f}"))
                
                # 완료 메시지
                file_list = "\n".join(saved_files[:3])  # 처음 3개만 표시
                if len(saved_files) > 3:
                    file_list += f"\n... 외 {len(saved_files)-3}개"
                
                self.root.after(0, lambda: messagebox.showinfo(
                    "완료", 
                    f"이미지 생성이 완료되었습니다!\n\n총 {total_files}개 이미지 생성\n저장 위치: 바탕화면\n\n생성된 파일:\n{file_list}",
                ))
            else:
                self.root.after(0, lambda: self.log_message("❌ 이미지 생성 실패"))
                self.root.after(0, lambda: messagebox.showerror("오류", "이미지 생성에 실패했습니다."))
                
        except Exception as e:
            error_msg = f"오류 발생: {str(e)}"
            self.root.after(0, lambda: self.log_message(f"❌ {error_msg}"))
            self.root.after(0, lambda: messagebox.showerror("오류", error_msg))
        
        finally:
            # 정리
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            # UI 복원
            self.root.after(0, self._finish_generation)
            
            # 메모리 정리
            gc.collect()

    def _finish_generation(self):
        """생성 완료 후 UI 복원"""
        self.progress_bar.stop()
        self.progress_var.set("완료")
        self.generate_button.config(state="normal")

    def _open_file_safely(self, file_path):
        """크로스 플랫폼 파일 열기 (WSL 환경 지원)"""
        try:
            # WSL 환경 감지
            is_wsl = "microsoft" in platform.uname().release.lower()
            
            if is_wsl:
                # WSL에서 Windows 파일 열기
                # Windows 경로를 WSL 경로로 변환하지 말고 explorer.exe 사용
                subprocess.run(['explorer.exe', file_path], check=False)
                self.log_message(f"📁 파일 위치: {file_path}")
            elif os.name == 'nt':
                # 순수 Windows 환경
                os.startfile(file_path)
            elif platform.system() == 'Darwin':
                # macOS
                subprocess.run(['open', file_path], check=False)
            else:
                # Linux
                subprocess.run(['xdg-open', file_path], check=False)
                
        except Exception as e:
            # 파일 열기 실패 시 경로만 안내
            self.log_message(f"📁 파일이 생성되었습니다: {file_path}")
            self.log_message(f"⚠️ 자동으로 열 수 없습니다: {str(e)}")


def main():
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
