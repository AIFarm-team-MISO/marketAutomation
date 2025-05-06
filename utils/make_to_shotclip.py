import os
from glob import glob
from moviepy.editor import (
    ImageClip, VideoFileClip, AudioFileClip, concatenate_videoclips,
    concatenate_audioclips, CompositeVideoClip, ColorClip, TextClip
)

def load_image_clips(image_folder: str, duration: float) -> list:
    image_files = sorted(glob(os.path.join(image_folder, "*.jpg")) +
                         glob(os.path.join(image_folder, "*.png")))
    if not image_files:
        print("❌ 이미지 없음")
        return []

    clips = [ImageClip(path).set_duration(duration) for path in image_files]
    return clips

def fit_to_resolution(clip, width=1080, height=1920):
    clip = clip.resize(height=height)  # 세로 고정
    background = ColorClip(size=(width, height), color=(255, 255, 255), duration=clip.duration)
    return CompositeVideoClip([background, clip.set_position("center")])

def save_video(clips, output_path: str, fps=24, total_duration=None):
    final = concatenate_videoclips(clips, method="compose")
    if total_duration:
        final = final.subclip(0, total_duration)

    final.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        bitrate="5000k"
    )
    print(f"✅ 숏클립 생성 완료: {output_path}")




def add_bgm_to_video(video_path: str, audio_path: str, output_path: str, volume: float = 1.0):
    try:
        with VideoFileClip(video_path) as video:
            audio = AudioFileClip(audio_path).volumex(volume)

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


from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, ColorClip

def overlay_watermark(clip: ImageClip, watermark_text: str, fontsize=40) -> CompositeVideoClip:
    """
    🔖 클립에 워터마크 텍스트 오버레이
    """
    watermark = (
        TextClip(watermark_text, fontsize=fontsize, color='white', font="Arial-Bold", method='caption')
        .set_duration(clip.duration)
        .margin(right=30, bottom=30, opacity=0)  # 여백
        .set_position(("right", "bottom"))
        .set_opacity(0.3)
    )
    return CompositeVideoClip([clip, watermark])

def make_shorts(image_folder,
                output_filename="shortclip.mp4",
                duration=None, total_duration=None,
                width=1080, height=1920,
                bgm_path=None, bgm_volume=1.0):

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

    processed_clips = [fit_to_resolution(clip, width, height) for clip in clips]

    # processed_clips = [
    # overlay_watermark(fit_to_resolution(clip, width, height), watermark_text="원스톱리빙")
    # for clip in clips
    # ] ImageMagick  설치하기 
 


    temp_video_path = os.path.join(image_folder, "temp_video_no_bgm.mp4")
    final_output_path = os.path.join(image_folder, output_filename)

    save_video(processed_clips, temp_video_path)

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
    bgm_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "music", "Rave Spark.mp3"))
    test_folder = r"F:\work\#쇼핑몰\#대량등록\#상품순환 엑셀파일\#팔린거최적화-네이버\오늘담음\파라브러\SPG-PRB_1000000867"

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
