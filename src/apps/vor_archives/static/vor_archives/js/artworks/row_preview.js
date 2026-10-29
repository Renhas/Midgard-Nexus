(function initArtworkRowPreview() {
    const OFFSET = 14;
    const PAD = 12;
    const SHOW_DELAY = 180;
    let preview = null;
    let currentItem = null;
    let showTimer = 0;

    function ensurePreview() {
        if (preview) {
            return preview;
        }
        preview = document.createElement("div");
        preview.id = "artwork-row-preview";
        preview.className = "artwork-row-preview";
        preview.innerHTML = `
            <div class="artwork-row-preview-cover">
                <img alt="">
                <div class="artwork-row-preview-cover-empty"><i></i></div>
            </div>
            <div class="artwork-row-preview-body">
                <div class="artwork-row-preview-title"></div>
                <div class="artwork-row-preview-desc"></div>
            </div>
        `;
        document.body.appendChild(preview);
        return preview;
    }

    function hidePreview() {
        window.clearTimeout(showTimer);
        showTimer = 0;
        currentItem = null;
        if (preview) {
            preview.classList.remove("is-visible");
        }
    }

    function canShow(row) {
        if (!row) {
            return false;
        }
        if (document.body.classList.contains("vor-artworks-dragging")) {
            return false;
        }
        const list = row.closest(".artwork-list");
        if (!list || list.classList.contains("is-grid")) {
            return false;
        }
        if (window.Alpine?.store("vorArtworks")?.searchOpen) {
            return false;
        }
        if (window.Alpine?.store("vorArtworks")?.menu?.open) {
            return false;
        }
        return true;
    }

    function fillPreview(item) {
        const el = ensurePreview();
        const title = item.dataset.previewTitle || "";
        const cover = item.dataset.previewCover || "";
        el.querySelector(".artwork-row-preview-title").textContent = title;
        el.querySelector(".artwork-row-preview-desc").textContent =
            (item.dataset.previewDesc || "").replace(/\s+/g, " ").trim();
        const img = el.querySelector("img");
        img.alt = title;
        if (cover) {
            img.src = cover;
            el.classList.remove("is-empty");
        } else {
            img.removeAttribute("src");
            el.classList.add("is-empty");
            const icon = el.querySelector(".artwork-row-preview-cover-empty i");
            if (icon) {
                icon.className = item.dataset.previewIcon || "";
            }
        }
    }

    function placePreview(clientX, clientY) {
        const el = ensurePreview();
        el.classList.add("is-visible");
        const width = el.offsetWidth;
        const height = el.offsetHeight;
        let x = clientX + OFFSET;
        let y = clientY + OFFSET;
        if (x + width > window.innerWidth - PAD) {
            x = clientX - width - OFFSET;
        }
        if (y + height > window.innerHeight - PAD) {
            y = clientY - height - OFFSET;
        }
        x = Math.max(PAD, x);
        y = Math.max(PAD, y);
        el.style.left = `${x}px`;
        el.style.top = `${y}px`;
    }

    document.addEventListener("pointermove", (event) => {
        const row = event.target.closest(".artwork-row");
        const item = row?.closest(".artwork-item");
        if (!canShow(row) || !item) {
            hidePreview();
            return;
        }
        if (currentItem !== item) {
            currentItem = item;
            fillPreview(item);
            window.clearTimeout(showTimer);
            if (preview?.classList.contains("is-visible")) {
                placePreview(event.clientX, event.clientY);
                return;
            }
            showTimer = window.setTimeout(() => {
                if (currentItem === item) {
                    placePreview(event.clientX, event.clientY);
                }
            }, SHOW_DELAY);
            return;
        }
        if (preview?.classList.contains("is-visible")) {
            placePreview(event.clientX, event.clientY);
        }
    });

    document.addEventListener("pointerdown", hidePreview);
    window.addEventListener("blur", hidePreview);
    window.addEventListener("scroll", hidePreview, true);
})();
