import os
from glob import glob

from moviepy.video.fx.all import resize

# ⬇️ MoviePy의 ImageMagick 설정 변경 (텍스트 클립 렌더링에 필요)
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

# MoviePy 주요 컴포넌트 임포트
from moviepy.editor import (
    ImageClip, VideoFileClip, AudioFileClip, concatenate_videoclips,
    concatenate_audioclips, CompositeVideoClip, ColorClip, TextClip
)

# 📥 이미지 로드 함수
def load_image_clips(image_folder: str, duration: float) -> list:
    image_files = sorted(glob(os.path.join(image_folder, "*.jpg")) +
                         glob(os.path.join(image_folder, "*.png")))
    
    """
    지정된 폴더 내 JPG 및 PNG 파일을 로드하여 ImageClip 리스트로 반환
    :param image_folder: 이미지가 저장된 폴더 경로
    :param duration: 각 이미지의 지속 시간 (초)
    :return: ImageClip 리스트
    """

    if not image_files:
        print("❌ 이미지 없음")
        return []

    # ✅ 이미지 불러올 때 해상도 줄이기 (예: 세로 기준 1080)
    clips = [
        ImageClip(path)
        .resize(height=1080)  # ⬅️ 핵심 리사이즈 적용
        .set_duration(duration)
        for path in image_files
    ]
    return clips


# 📐 영상 해상도 비율 맞춤 함수
def fit_to_resolution(clip, width=1080, height=1920):
    """
    클립의 해상도를 세로 고정 기준으로 리사이즈하고, 흰색 배경에 중앙 정렬
    :param clip: 원본 ImageClip
    :param width: 최종 해상도 너비
    :param height: 최종 해상도 높이
    :return: CompositeVideoClip
    """
    clip = clip.resize(height=height)
    background = ColorClip(size=(width, height), color=(255, 255, 255), duration=clip.duration)
    return CompositeVideoClip([background, clip.set_position("center")])

# 📐 영상 해상도 비율 맞춤 + 줌인효과
def fit_to_resolution_zoomin(clip, width=1080, height=1920):
    """
    이미지 클립을 지정된 해상도에 맞추고, 재생 시간 동안 점점 확대되는 효과를 부여
    """
    # 시작 크기: 원본 높이에 맞춤
    clip = clip.resize(height=height)

    # 확대 효과 (예: 1배 → 1.2배 확대)
    zoomed = clip.fx(resize, lambda t: 1 + 0.2 * (t / clip.duration))  # t: 현재 시점, 0.2는 확대 비율

    # 흰색 배경 위 중앙 정렬
    background = ColorClip(size=(width, height), color=(255, 255, 255), duration=clip.duration)
    return CompositeVideoClip([background, zoomed.set_position("center")])


# 💾 영상 저장 함수
def save_video(clips, output_path: str, fps=24, total_duration=None):
    """
    여러 클립을 연결하고 영상으로 저장
    :param clips: 영상 클립 리스트
    :param output_path: 저장할 MP4 파일 경로
    :param fps: 프레임 속도
    :param total_duration: 전체 영상 길이 제한 (선택적)
    """
    final = concatenate_videoclips(clips, method="compose")
    if total_duration:
        final = final.subclip(0, total_duration)

    final.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        #bitrate="5000k"
        bitrate="3000k",
        threads=4  # 💡 CPU 코어 수에 맞게 조정
    )
    print(f"✅ 숏클립 생성 완료: {output_path}")


# 🎧 BGM 삽입 함수
def add_bgm_to_video(video_path: str, audio_path: str, output_path: str, volume: float = 1.0):
    """
    기존 무음 영상에 배경음악(BGM)을 입히고 저장
    :param video_path: 기존 영상 경로
    :param audio_path: 배경음악 파일 경로
    :param output_path: 최종 저장 경로
    :param volume: 오디오 볼륨 (0.0 ~ 1.0)
    """
    try:
        with VideoFileClip(video_path) as video:
            audio = AudioFileClip(audio_path).volumex(volume)

            # 오디오가 짧으면 반복, 길면 자르기
            if audio.duration < video.duration:
                n_loops = int(video.duration // audio.duration) + 1
                audio = concatenate_audioclips([audio] * n_loops)
            audio = audio.subclip(0, video.duration)

            final = video.set_audio(audio)
            final.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast"
            )
            print(f"✅ BGM 추가 완료: {output_path}")
    except Exception as e:
        print(f"❌ BGM 처리 중 오류 발생: {e}")


# 🚫 (현재 사용 안함) 영상 클립에 워터마크 오버레이
def overlay_watermark(clip, watermark_text="원스톱리빙", fontsize=40, opacity=0.3, position=("right", "bottom")):
    """
    워터마크를 텍스트로 클립 위에 겹쳐 표시 (ImageMagick 필요)
    :param clip: 원본 영상 클립
    :param watermark_text: 표시할 텍스트
    :param fontsize: 텍스트 크기
    :param opacity: 투명도
    :param position: 위치
    :return: CompositeVideoClip
    """
    try:
        watermark = (
            TextClip(watermark_text, fontsize=fontsize, color='white', method='caption', font='Malgun-Gothic')
            .set_duration(clip.duration)
            .set_position(position)
            .set_opacity(opacity)
        )
        return CompositeVideoClip([clip, watermark])
    except Exception as e:
        print(f"❌ 워터마크 생성 실패: {e}")
        return clip


# 🏁 브랜드 엔딩 클립 생성
def create_ending_clip(text: str, duration: float, width: int, height: int):
    """
    영상 마지막에 브랜드명 등 텍스트 클립을 삽입
    :param text: 표시할 텍스트
    :param duration: 지속 시간
    :param width: 해상도 너비
    :param height: 해상도 높이
    :return: CompositeVideoClip

    !폰트 변경시 : cmd에서 폰트확인  magick -list font

    """
    try:
        print("📌 엔딩 클립 생성 중")

        # 검정 배경 생성
        bg = ColorClip(size=(width, height), color=(0, 0, 0)).set_duration(duration)

        # 텍스트 생성
        txt = (
            TextClip(
                text,
                fontsize=120,
                color='white',
                method='label',
                #font='Malgun-Gothic'
                font='Noto-Sans-KR'
            )
            .set_duration(duration)
            .set_position('center')
            .fadein(0.1)   # 첫 0.5초 동안 서서히 나타남
            .fadeout(0.9)  # 마지막 0.5초 동안 서서히 사라짐
        )

        return CompositeVideoClip([bg, txt])

    except Exception as e:
        print(f"❌ 엔딩 클립 생성 실패: {e}")
        return ColorClip(size=(width, height), color=(0, 0, 0), duration=duration)



# 🎬 메인 함수: 숏클립 생성
def make_shorts(image_folder,
                output_filename="shortclip.mp4",
                duration=None, total_duration=None,
                width=1080, height=1920,
                bgm_path=None, 
                bgm_volume=1.0):
    """
    숏클립 제작 전체 프로세스 (이미지 → 영상 → 엔딩 → BGM 추가)
    :param image_folder: 이미지가 저장된 폴더
    :param output_filename: 최종 영상 파일명
    :param duration: 각 이미지의 재생 시간
    :param total_duration: 전체 영상 길이 제한
    :param width: 출력 영상 너비
    :param height: 출력 영상 높이
    :param bgm_path: 배경음악 파일 경로
    :param bgm_volume: BGM 볼륨
    """
    if bgm_path is None:
        bgm_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "music", "Rave Spark.mp3"))


    original_clips = load_image_clips(image_folder, duration=1.0)


    if not original_clips:
        return

    n_images = len(original_clips)

    if duration is None and total_duration:
        duration = total_duration / n_images

    clips = load_image_clips(image_folder, duration)

    if total_duration:
        n_total = int(total_duration / duration)
        clips = (clips * ((n_total + len(clips) - 1) // len(clips)))[:n_total]


    # 📏 이미지 클립 리사이즈 + 줌아웃
    processed_clips = [fit_to_resolution_zoomin(clip, width, height) for clip in clips]


    # ✅ 워터마크포함
    # processed_clips = [
    #     overlay_watermark(fit_to_resolution(clip, width, height), watermark_text="원스톱리빙")
    #     for clip in clips
    # ] 

    # 🔚 엔딩 텍스트 클립 추가
    processed_clips.append(
        create_ending_clip(text="원스톱리빙", duration=1.0, width=width, height=height)
    )

    # 💾 영상 저장 경로 설정
    temp_video_path = os.path.join(image_folder, "temp_video_no_bgm.mp4")
    final_output_path = os.path.join(image_folder, output_filename)

    # 🎥 영상 저장
    save_video(processed_clips, temp_video_path)

    # 🎧 BGM 삽입 및 최종 저장
    try:
        if bgm_path and os.path.exists(bgm_path):
            add_bgm_to_video(temp_video_path, bgm_path, final_output_path, volume=bgm_volume)
            os.remove(temp_video_path)
        else:
            os.replace(temp_video_path, final_output_path)
    except Exception as e:
        print(f"❌ 최종 저장 처리 중 오류 발생: {e}")
        os.replace(temp_video_path, final_output_path)


# ✅ 테스트 실행
if __name__ == "__main__":
    # 테스트용 경로 설정
    bgm_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "music", "Rave Spark.mp3"))
    test_folder = r"F:\work\#쇼핑몰\#대량등록\#상품순환 엑셀파일\#팔린거최적화-네이버\오늘담음\파라브러\SP-PRB_1000000018"

    # 숏클립 생성 실행
    make_shorts(
        image_folder=test_folder,
        output_filename="zoomed_shorts.mp4",
        duration=0.8,
        total_duration=6,
        width=1080,
        height=1920,
        bgm_path=bgm_path,
        bgm_volume=0.8
    )
