document.addEventListener('DOMContentLoaded', () => {
    const nav = document.getElementById('mainNav');
    if (!nav || !nav.classList.contains('navbar-transparent')) return;

    const toggle = () => {
        nav.classList.toggle('scrolled', window.scrollY > 50);
    };

    toggle();
    window.addEventListener('scroll', toggle);
});

let searchResults = [];
let currentIndex = -1;

function clearSearch() {
    document.querySelectorAll("mark.search-highlight").forEach(mark => {
        mark.replaceWith(mark.textContent);
    });
    searchResults = [];
    currentIndex = -1;
    updateCounter();
}

function searchAndScroll() {
    const input = document.getElementById("searchInput");
    if (!input) return false;

    const keyword = input.value.trim();
    if (!keyword) return false;

    clearSearch();

    const root = document.querySelector("main") || document.body;
    const textNodes = [];

    const walker = document.createTreeWalker(
        root,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode(node) {
                if (!node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
                if (node.parentElement.closest("script, style, nav"))
                    return NodeFilter.FILTER_REJECT;
                return NodeFilter.FILTER_ACCEPT;
            }
        }
    );

    let node;
    while ((node = walker.nextNode())) {
        textNodes.push(node);
    }


    const regex = new RegExp(`(${keyword})`, "gi");

    textNodes.forEach(textNode => {
        if (!regex.test(textNode.nodeValue)) return;

        const span = document.createElement("span");
        span.innerHTML = textNode.nodeValue.replace(
            regex,
            `<mark class="search-highlight">$1</mark>`
        );

        textNode.parentNode.replaceChild(span, textNode);

        span.querySelectorAll("mark.search-highlight").forEach(mark => {
            searchResults.push(mark);
        });
    });

    if (searchResults.length === 0) {
        alert("Không tìm thấy nội dung trên trang");
        return false;
    }

    currentIndex = 0;
    focusResult(currentIndex);
    updateCounter();
    return false;
}

function focusResult(index) {
    searchResults.forEach(el =>
        el.classList.remove("active-search")
    );

    const el = searchResults[index];
    el.classList.add("active-search");

    el.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });
}

function nextResult() {
    if (!searchResults.length) return;
    currentIndex = (currentIndex + 1) % searchResults.length;
    focusResult(currentIndex);
    updateCounter();
}

function prevResult() {
    if (!searchResults.length) return;
    currentIndex =
        (currentIndex - 1 + searchResults.length) % searchResults.length;
    focusResult(currentIndex);
    updateCounter();
}

function updateCounter() {
    const counter = document.getElementById("searchCounter");
    if (!counter) return;

    counter.textContent = searchResults.length
        ? `${currentIndex + 1}/${searchResults.length}`
        : "";
}
