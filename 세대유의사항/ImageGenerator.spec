# -*- mode: python ; coding: utf-8 -*-
# Updated spec for Image Generator with Company Colors and .jpg template support

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),  # 모든 assets 폴더 (폰트 + 템플릿)
        ('src', 'src'),        # 소스 코드
    ],
    hiddenimports=[
        'src.utils.company_colors',  # 새로 추가된 색상 관리 모듈
        'src.core.excel_to_json',
        'src.core.json_to_image', 
        'src.core.local_file_manager',
        'src.core.position_settings',
        'src.gui.gui_app',
        'src.utils.text_utils',
        'pandas',
        'pandas._libs',
        'pandas._libs.tslibs',
        'pandas._libs.tslibs.base',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.tslibs.timezones',
        'numpy',
        'numpy.core',
        'numpy.core.multiarray',
        'numpy.core.numeric',
        'numpy.core.umath',
        'numpy.core._multiarray_umath',
        'numpy.fft',
        'numpy.linalg',
        'numpy.random',
        'PIL',
        'openpyxl',
        'io',
        'tempfile',
        'shutil',
        'threading',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',  # 불필요한 대용량 모듈 제외
        'scipy',
        'numpy.testing',
        'pytest'
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='이미지생성기',  # 한국어 파일명으로 변경
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 시작 속도 향상을 위해 압축 비활성화
    console=False,  # GUI 모드 (콘솔 창 숨김)
    disable_windowed_traceback=False,
    icon=None,  # 필요시 아이콘 추가 가능
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='이미지생성기',
)
