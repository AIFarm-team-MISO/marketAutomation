import webview
import threading
import time

EXTRACT_TAG_JS = """
new Promise((resolve, reject) => {
    const tryExtract = () => {
        const tagList = document.querySelector("ul._3Vox1DKZiA");
        if (tagList) {
            const anchors = tagList.querySelectorAll("li > a");
            const tags = [];
            anchors.forEach(a => {
                const text = a.innerText.trim();
                if (text) tags.push(text);
            });
            resolve(tags);
        } else {
            setTimeout(tryExtract, 500);
        }
    };
    tryExtract();

    setTimeout(() => {
        reject("⏰ Timeout: 검색 태그가 나타나지 않음");
    }, 10000);
});
"""

CHECK_IFRAME_JS = r"""
(function() {
    const iframes = Array.from(document.getElementsByTagName('iframe'));
    if (iframes.length === 0) return '✅ iframe 없음';
    return '❗ iframe 존재:\n' + iframes.map(f => '   - ' + (f.src || 'src 없음')).join('\n');
})()
"""

CHECK_ALL_LINKS_JS = r"""
(function() {
    const anchors = Array.from(document.getElementsByTagName('a'));
    const links = anchors.map(a => a.href).filter(href => href);
    return links;
})()
"""

class API:
    def __init__(self):
        self.tags = []

    def receive_tags(self, tags):
        print(f"\n🏷️ 추출된 검색 태그 {len(tags)}개:")
        for i, tag in enumerate(tags, start=1):
            print(f"[{i}] {tag}")
        self.tags = tags

def run_extract_js(window, api_obj):
    time.sleep(3)
    print("\n🕵️ JavaScript 실행 중...")

    iframe_info = window.evaluate_js(CHECK_IFRAME_JS)
    print(f"\n{iframe_info}")

    all_links = window.evaluate_js(CHECK_ALL_LINKS_JS)
    print(f"\n🌐 현재 페이지의 링크 {len(all_links)}개:")
    for i, link in enumerate(all_links[:20], 1):
        print(f"[{i}] {link}")

    try:
        tags = window.evaluate_js(EXTRACT_TAG_JS)
        if tags:
            api_obj.receive_tags(tags)
        else:
            print("⚠️ 태그가 비어 있습니다.")
    except Exception as e:
        print(f"❌ JavaScript 실행 실패: {e}")

def start_webview():
    api = API()
    # 기존 검색 URL
    # search_url = f"https://search.shopping.naver.com/ns/search?query=귀고무"
    # 스마트스토어 상세페이지로 변경
    product_url = "https://smartstore.naver.com/glasslen/products/10785920819?NaPm=ct%3Dmaapax21%7Cci%3DER5bbcbca8%2D297a%2D11f0%2D9b6c%2D6ee735a78598%7Ctr%3Dplan%7Chk%3D9d3de64fd673236072669993a5a385dbdf9923be%7Cnacn%3DJIKpBUAQfAG6A"

    window = webview.create_window(
        title="🏷️ 네이버 스마트스토어 검색태그 추출기",
        url=product_url,
        js_api=api,
        width=1200,
        height=900
    )
    threading.Thread(target=run_extract_js, args=(window, api), daemon=True).start()
    webview.start(debug=True, gui="edgechromium")

if __name__ == "__main__":
    start_webview()
