import webview

CHECK_JS = """
new Promise((resolve, reject) => {
    function waitForProducts(attempts = 0) {
        const list = document.querySelector("ul[class*='compositeCardList_product_list']");
        if (list || attempts > 20) {
            resolve(list ? list.innerHTML : "❌ 상품 리스트 DOM 없음");
        } else {
            setTimeout(() => waitForProducts(attempts + 1), 500);
        }
    }
    waitForProducts();
});
"""

def on_loaded(window):
    print("🕵️ JavaScript 실행 중...")
    html = window.evaluate_js(CHECK_JS)

    with open("debug_product_list.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ HTML 저장 완료: debug_product_list.html")


if __name__ == "__main__":
    url = "https://search.shopping.naver.com/ns/search?query=귀고무"
    window = webview.create_window("상품 리스트 확인", url)
    webview.start(on_loaded, window, gui="cef")
