#!/usr/bin/env python3
"""
간단한 빌드 스크립트 - 한글 인코딩 문제 해결
Image Generator v2.0 Builder
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """명령어 실행 및 결과 확인"""
    print(f"\n📋 {description}")
    print(f"🔧 실행 중: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True, encoding='utf-8')
        print("✅ 성공!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 실패: {e}")
        print(f"출력: {e.stdout}")
        print(f"오류: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        return False

def check_files():
    """필수 파일 확인"""
    # 스크립트가 있는 디렉토리를 기준으로 경로 계산
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)  # 작업 디렉토리를 스크립트 위치로 변경
    
    required_files = [
        'main.py',
        'ImageGenerator.spec',
        'config/requirements.txt',
        'src/utils/company_colors.py'
    ]
    
    print("📁 필수 파일 확인 중...")
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - 파일이 없습니다!")
            return False
    return True

def clean_previous_builds():
    """이전 빌드 정리"""
    print("\n🧹 이전 빌드 정리 중...")
    dirs_to_remove = ['dist', 'build']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✅ {dir_name} 폴더 삭제됨")
            except Exception as e:
                print(f"⚠️ {dir_name} 삭제 실패: {e}")

def install_dependencies():
    """의존성 설치 - 기존 환경 사용"""
    print("\n📦 의존성 확인 중...")
    print("✅ 기존 anaconda 환경의 패키지 사용 (재설치 건너뛰기)")
    
    # PyInstaller만 필요시 설치 확인
    try:
        import PyInstaller
        print("✅ PyInstaller 이미 설치됨")
    except ImportError:
        print("📋 PyInstaller 설치 중...")
        return run_command("python -m pip install pyinstaller==5.13.2", "PyInstaller 설치")
    
    return True

def build_exe():
    """PyInstaller로 EXE 빌드"""
    return run_command("python -m PyInstaller ImageGenerator.spec", 
                      "PyInstaller로 EXE 파일 빌드")

def check_build_result():
    """빌드 결과 확인"""
    exe_path = "dist/이미지생성기/이미지생성기.exe"  # onedir 모드 경로
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"✅ EXE 파일 생성 성공!")
        print(f"📁 위치: {exe_path}")
        print(f"📊 크기: {size_mb:.1f} MB")
        return True
    else:
        print("❌ EXE 파일을 찾을 수 없습니다!")
        return False

def create_deployment_package():
    """배포 패키지 생성"""
    print("\n📦 배포 패키지 생성 중...")
    
    # 배포 폴더 생성
    deploy_path = Path("deploy")
    deploy_path.mkdir(exist_ok=True)
    
    # EXE 폴더 전체 복사 (onedir 모드)
    source_dir = "dist/이미지생성기"
    if os.path.exists(source_dir):
        shutil.copytree(source_dir, "deploy/이미지생성기", dirs_exist_ok=True)
        print("✅ EXE 폴더 복사됨")
    else:
        print("❌ EXE 폴더를 찾을 수 없습니다!")
    
    # 디렉토리 구조 생성
    (deploy_path / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    (deploy_path / "assets" / "templates").mkdir(parents=True, exist_ok=True)
    (deploy_path / "output").mkdir(exist_ok=True)
    
    # 폰트 파일 복사
    fonts_src = Path("assets/fonts")
    if fonts_src.exists():
        for font_file in fonts_src.glob("*.ttf"):
            shutil.copy2(font_file, deploy_path / "assets" / "fonts")
            print(f"✅ 폰트 복사: {font_file.name}")
        for font_file in fonts_src.glob("*.otf"):
            shutil.copy2(font_file, deploy_path / "assets" / "fonts")
            print(f"✅ 폰트 복사: {font_file.name}")
    
    # 템플릿 파일 복사
    templates_src = Path("assets/templates")
    template_count = 0
    if templates_src.exists():
        for template_file in templates_src.glob("*.jpg"):
            shutil.copy2(template_file, deploy_path / "assets" / "templates")
            template_count += 1
        for template_file in templates_src.glob("*.png"):
            shutil.copy2(template_file, deploy_path / "assets" / "templates")
            template_count += 1
    
    print(f"✅ 템플릿 파일 {template_count}개 복사됨")
    
    # 사용법 파일 생성 (UTF-8 인코딩으로)
    usage_content = """주의사항 이미지 생성기 v2.0 사용법

========================================
  주의사항 이미지 생성기 v2.0
========================================

1. 실행 방법:
   - 이미지생성기.exe 더블클릭

2. 지원 건설사 (15개):
   계룡, 극동, 남광토건, 남해, 동원
   모아주택산업, 서영, 서한, 서희, 신세계
   제주특별자치도개발공사, 진흥, 호반, 화성, 효성

3. 새로운 기능:
   - 건설사별 브랜드 색상 자동 적용
   - .jpg 템플릿 파일 지원
   - 실시간 색상 미리보기
   - 템플릿 선택 시 색상 자동 변경

4. 사용 방법:
   a) 엑셀 파일 선택 (번호, 제목, 설명 컬럼 필요)
   b) 건설사 템플릿 선택 (자동으로 색상 적용됨)
   c) 저장 위치 선택
   d) '이미지 생성하기' 버튼 클릭

5. 결과물:
   - output 폴더에 PNG 파일들 저장
   - 건설사명_날짜시간_파일명.png 형태

6. Windows 보안 경고 시:
   - '추가 정보' 클릭 후 '실행' 선택
   - 또는 파일 우클릭 > 속성 > '차단 해제' 체크

7. 문제 해결:
   - 폰트 파일이 없으면 assets/fonts/에 NotoSansKR 폰트 추가
   - 새 템플릿 추가: assets/templates/에 건설사명.jpg 파일 추가
"""
    
    with open(deploy_path / "사용법.txt", "w", encoding="utf-8") as f:
        f.write(usage_content)
    
    print("✅ 사용법.txt 생성됨")
    
    return True

def show_results():
    """결과 출력"""
    print("\n" + "="*50)
    print("🎉 빌드 완료!")
    print("="*50)
    print("\n📁 배포 폴더: deploy/")
    print("🚀 실행 파일: deploy/이미지생성기/이미지생성기.exe")
    print("📖 사용법: deploy/사용법.txt")
    
    # 폴더 내용 확인
    deploy_path = Path("deploy")
    if deploy_path.exists():
        print(f"\n📋 배포 폴더 내용:")
        for item in deploy_path.rglob("*"):
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f"   {item.relative_to(deploy_path)} ({size_mb:.1f} MB)")
    
    print(f"\n🏢 지원되는 15개 건설사:")
    companies = [
        "계룡", "극동", "남광토건", "남해", "동원",
        "모아주택산업", "서영", "서한", "서희", "신세계", 
        "제주특별자치도개발공사", "진흥", "호반", "화성", "효성"
    ]
    print("   " + ", ".join(companies))
    
    print(f"\n✨ 새로운 기능: 건설사별 브랜드 색상 자동 적용, .jpg 템플릿 지원")
    print(f"\n💡 이제 'deploy' 폴더를 다른 Windows 컴퓨터에 복사하여 사용할 수 있습니다!")
    print(f"   Python 설치가 필요하지 않습니다!")

def main():
    """메인 실행 함수"""
    print("🏗️ 주의사항 이미지 생성기 v2.0 빌더")
    print("="*50)
    
    # 1. 필수 파일 확인
    if not check_files():
        print("\n❌ 필수 파일이 없습니다. 프로젝트 루트 디렉토리에서 실행하세요.")
        input("아무 키나 눌러서 종료...")
        return False
    
    # 2. 이전 빌드 정리
    clean_previous_builds()
    
    # 3. 의존성 설치
    if not install_dependencies():
        print("\n❌ 의존성 설치 실패")
        input("아무 키나 눌러서 종료...")
        return False
    
    # 4. EXE 빌드
    if not build_exe():
        print("\n❌ EXE 빌드 실패")
        input("아무 키나 눌러서 종료...")
        return False
    
    # 5. 빌드 결과 확인
    if not check_build_result():
        print("\n❌ 빌드 결과 확인 실패")
        input("아무 키나 눌러서 종료...")
        return False
    
    # 6. 배포 패키지 생성
    if not create_deployment_package():
        print("\n❌ 배포 패키지 생성 실패")
        input("아무 키나 눌러서 종료...")
        return False
    
    # 7. 결과 출력
    show_results()
    
    print("\n" + "="*50)
    input("아무 키나 눌러서 종료...")
    return True

if __name__ == "__main__":
    main()