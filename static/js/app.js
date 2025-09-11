/**
 * 財商成長思維平台前端應用
 */

// 全域變數
let currentArticles = [];
let currentGeneratedArticle = null;
let categories = [];

// API 基礎路徑
const API_BASE = '/api/v1/financial-wisdom';

// 通知系統
class NotificationManager {
    constructor() {
        this.container = document.getElementById('notificationContainer');
    }
    
    showLoading(message = '載入中...', showProgress = false) {
        const loadingId = 'loading-' + Date.now();
        const loadingHTML = `
            <div id="${loadingId}" class="enhanced-loading show">
                <div class="loading-spinner"></div>
                <div class="loading-text">${message}</div>
                ${showProgress ? '<div class="progress-bar"><div class="progress-fill"></div></div>' : ''}
            </div>
        `;
        
        this.container.innerHTML = loadingHTML;
        return loadingId;
    }
    
    hideLoading(loadingId) {
        const element = document.getElementById(loadingId);
        if (element) {
            element.remove();
        }
    }
    
    showError(title, message, actions = null, autoHide = true) {
        const errorId = 'error-' + Date.now();
        const actionsHTML = actions ? `
            <div class="error-actions">
                ${actions.map(action => 
                    `<button class="btn btn-sm btn-outline-danger me-2" onclick="${action.onClick}">${action.text}</button>`
                ).join('')}
            </div>
        ` : '';
        
        const errorHTML = `
            <div id="${errorId}" class="error-alert show">
                <div class="error-title">${title}</div>
                <div class="error-message">${message}</div>
                ${actionsHTML}
            </div>
        `;
        
        this.container.innerHTML = errorHTML;
        
        if (autoHide) {
            setTimeout(() => this.hideError(errorId), 5000);
        }
        
        return errorId;
    }
    
    hideError(errorId) {
        const element = document.getElementById(errorId);
        if (element) {
            element.classList.remove('show');
            setTimeout(() => element.remove(), 300);
        }
    }
    
    showSuccess(title, message, autoHide = true) {
        const successId = 'success-' + Date.now();
        const successHTML = `
            <div id="${successId}" class="success-alert show">
                <div class="success-title">${title}</div>
                <div class="success-message">${message}</div>
            </div>
        `;
        
        this.container.innerHTML = successHTML;
        
        if (autoHide) {
            setTimeout(() => this.hideSuccess(successId), 3000);
        }
        
        return successId;
    }
    
    hideSuccess(successId) {
        const element = document.getElementById(successId);
        if (element) {
            element.classList.remove('show');
            setTimeout(() => element.remove(), 300);
        }
    }
    
    clear() {
        this.container.innerHTML = '';
    }
}

// 創建全局通知管理器
const notifications = new NotificationManager();

// 文章內容緩存系統
class ArticleCache {
    constructor(maxSize = 50) {
        this.cache = new Map();
        this.maxSize = maxSize;
        this.loadingStates = new Set(); // 追蹤正在載入的文章
    }
    
    get(articleId) {
        return this.cache.get(articleId);
    }
    
    set(articleId, article) {
        if (this.cache.size >= this.maxSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        this.cache.set(articleId, article);
    }
    
    has(articleId) {
        return this.cache.has(articleId);
    }
    
    isLoading(articleId) {
        return this.loadingStates.has(articleId);
    }
    
    setLoading(articleId) {
        this.loadingStates.add(articleId);
    }
    
    clearLoading(articleId) {
        this.loadingStates.delete(articleId);
    }
}

// 創建全局文章緩存
const articleCache = new ArticleCache();

// API 請求包裝器，帶有自動錯誤處理
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`API請求失敗: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API請求錯誤:', error);
        throw error;
    }
}

// 骨架屏載入效果
function showSkeletonCards(containerId, count = 3) {
    const container = document.getElementById(containerId);
    const skeletonHTML = Array(count).fill().map(() => `
        <div class="skeleton-card">
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text medium"></div>
            <div class="skeleton skeleton-text short"></div>
        </div>
    `).join('');
    
    container.innerHTML = skeletonHTML;
}

// 應用初始化
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    loadCategories();
    loadArticles();
    
    // 綁定事件處理器
    setupEventListeners();
});

function setupEventListeners() {
    // 文章生成表單
    document.getElementById('generateForm').addEventListener('submit', handleGenerateArticle);
    
    // 搜尋功能
    document.getElementById('searchInput').addEventListener('input', debounce(loadArticles, 500));
    document.getElementById('categoryFilter').addEventListener('change', loadArticles);
}

// 工具函數：防抖動
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 載入儀表板統計資料
async function loadDashboard() {
    try {
        showSkeletonCards('statsCards', 4);
        
        const stats = await apiRequest(`${API_BASE}/stats`);
        renderStatsCards(stats);
        
    } catch (error) {
        console.error('載入統計資料錯誤:', error);
        notifications.showError('載入失敗', '無法載入統計資料，請檢查網路連接或稍後重試', [
            { text: '重試', onClick: 'loadDashboard()' }
        ]);
        document.getElementById('statsCards').innerHTML = '<div class="col-12"><div class="alert alert-warning text-center">統計資料載入失敗</div></div>';
    }
}

// 渲染統計卡片
function renderStatsCards(stats) {
    const container = document.getElementById('statsCards');
    
    const cardsHTML = `
        <div class="col-md-3 mb-3">
            <div class="card card-hover stats-card">
                <div class="card-body text-center">
                    <i class="fas fa-file-alt fa-2x mb-2"></i>
                    <h3>${stats.total_articles || 0}</h3>
                    <p class="mb-0">總文章數</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card card-hover stats-card">
                <div class="card-body text-center">
                    <i class="fas fa-font fa-2x mb-2"></i>
                    <h3>${(stats.total_words || 0).toLocaleString()}</h3>
                    <p class="mb-0">總字數</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card card-hover stats-card">
                <div class="card-body text-center">
                    <i class="fas fa-chart-line fa-2x mb-2"></i>
                    <h3>${stats.average_words || 0}</h3>
                    <p class="mb-0">平均字數</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card card-hover stats-card">
                <div class="card-body text-center">
                    <i class="fas fa-tags fa-2x mb-2"></i>
                    <h3>${Object.keys(stats.categories || {}).length}</h3>
                    <p class="mb-0">分類數量</p>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = cardsHTML;
    
    // 如果有分類統計，顯示詳細信息
    if (stats.categories) {
        const categoriesInfo = Object.entries(stats.categories)
            .map(([category, count]) => `<span class="badge bg-primary me-1">${category}: ${count}</span>`)
            .join('');
        
        container.innerHTML += `
            <div class="col-12 mt-3">
                <div class="card">
                    <div class="card-body">
                        <h6><i class="fas fa-chart-pie me-2"></i>分類統計</h6>
                        ${categoriesInfo}
                    </div>
                </div>
            </div>
        `;
    }
}

// 載入分類選項
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories`);
        if (!response.ok) throw new Error('載入分類失敗');
        
        const data = await response.json();
        categories = data.categories || [];
        
        // 更新分類下拉選單
        const categoryFilter = document.getElementById('categoryFilter');
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        });
        
    } catch (error) {
        console.error('載入分類錯誤:', error);
    }
}

// 載入文章列表
async function loadArticles() {
    try {
        console.log('📚 開始載入文章列表...');
        showLoading('articlesList');
        
        // 構建查詢參數
        const params = new URLSearchParams({
            limit: 50  // 增加到50以確保載入所有文章
        });
        
        const searchTerm = document.getElementById('searchInput').value;
        if (searchTerm) {
            params.append('search', searchTerm);
        }
        
        const selectedCategory = document.getElementById('categoryFilter').value;
        if (selectedCategory) {
            params.append('category', selectedCategory);
        }
        
        const url = `${API_BASE}/articles?${params}`;
        console.log('🌐 請求URL:', url);
        
        const response = await fetch(url);
        console.log('📡 API響應狀態:', response.status);
        
        if (!response.ok) throw new Error('載入文章失敗');
        
        const data = await response.json();
        currentArticles = data.articles || [];
        
        console.log('📄 載入文章數量:', currentArticles.length);
        console.log('🔍 文章數據樣本:', currentArticles.length > 0 ? currentArticles[0] : '無數據');
        
        renderArticlesList(currentArticles);
        
    } catch (error) {
        console.error('載入文章錯誤:', error);
        showError('articlesList', '無法載入文章列表');
    }
}

// 渲染文章列表
function renderArticlesList(articles) {
    console.log('🎨 開始渲染文章列表，文章數量:', articles.length);
    const container = document.getElementById('articlesList');
    
    if (!container) {
        console.error('❌ 找不到文章列表容器 #articlesList');
        return;
    }
    
    if (articles.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-file-alt fa-3x mb-3"></i>
                <h5>沒有找到相關文章</h5>
                <p>嘗試調整搜尋條件或創建新文章</p>
            </div>
        `;
        return;
    }
    
    const articlesHTML = articles.map((article, index) => `
        <div class="card card-hover article-card mb-3" onclick="handleArticleClick('${article.id}', this)" style="cursor: pointer;" data-article-id="${article.id}">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-1 text-center">
                        <span class="badge bg-secondary fs-6">${index + 1}</span>
                    </div>
                    <div class="col-md-7">
                        <h5 class="card-title mb-2 text-primary">${escapeHtml(article.title)}</h5>
                        <p class="card-text text-muted mb-2 small">${escapeHtml(article.summary || '點擊查看完整文章內容...')}</p>
                        <div class="mb-2">
                            <span class="badge category-badge bg-primary me-2">${escapeHtml(article.category)}</span>
                            ${article.tags && article.tags.length > 0 ? article.tags.map(tag => `<span class="tag text-primary">#${escapeHtml(tag)}</span>`).join('') : '<span class="text-muted small">暫無標籤</span>'}
                        </div>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="small text-muted">
                            <div class="mb-1"><i class="fas fa-font me-2"></i><strong>${article.word_count || 0}</strong> 字</div>
                            <div class="mb-1"><i class="fas fa-clock me-2"></i><strong>${article.reading_time || Math.ceil((article.word_count || 800) / 300)}</strong> 分鐘閱讀</div>
                            <div class="mb-1"><i class="fas fa-calendar me-2"></i>${formatDate(article.publish_date)}</div>
                            <div class="mt-2">
                                <span class="badge bg-success">✅ ${article.status || '已發布'}</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-12">
                        <small class="text-muted">
                            <i class="fas fa-mouse-pointer me-1"></i>點擊查看完整文章內容
                            ${articleCache.has(article.id) ? '<span class="badge bg-info ms-2"><i class="fas fa-download me-1"></i>已緩存</span>' : ''}
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = articlesHTML;
    console.log('✅ 文章列表渲染完成，HTML長度:', articlesHTML.length);
}

// 處理文章卡片點擊事件
async function handleArticleClick(articleId, cardElement) {
    // 防止重複點擊
    if (cardElement.classList.contains('loading')) {
        return;
    }
    
    // 添加載入狀態到卡片
    cardElement.classList.add('loading');
    cardElement.style.transform = 'scale(0.98)';
    cardElement.style.transition = 'all 0.2s ease';
    
    // 添加載入指示器
    const originalContent = cardElement.querySelector('.col-md-7 h5').innerHTML;
    cardElement.querySelector('.col-md-7 h5').innerHTML = '<i class="fas fa-spinner fa-spin me-2 text-primary"></i>' + originalContent;
    
    try {
        await showArticleDetail(articleId);
    } finally {
        // 移除載入狀態
        cardElement.classList.remove('loading');
        cardElement.style.transform = '';
        cardElement.style.transition = '';
        cardElement.querySelector('.col-md-7 h5').innerHTML = originalContent;
    }
}

// 顯示文章詳情
async function showArticleDetail(articleId) {
    // 防止重複點擊 - 如果正在載入，直接返回
    if (articleCache.isLoading(articleId)) {
        console.log('文章正在載入中，請稍候...');
        return;
    }
    
    try {
        let article;
        
        // 檢查緩存
        if (articleCache.has(articleId)) {
            console.log('從緩存載入文章:', articleId);
            article = articleCache.get(articleId);
        } else {
            // 標記為載入中
            articleCache.setLoading(articleId);
            
            // 顯示載入狀態
            const loadingId = notifications.showLoading('載入文章內容中...', false);
            
            try {
                console.log('從 API 載入文章:', articleId);
                const response = await fetch(`${API_BASE}/articles/${articleId}`);
                if (!response.ok) throw new Error('載入文章內容失敗');
                
                article = await response.json();
                
                // 緩存文章內容
                articleCache.set(articleId, article);
                
                // 隱藏載入狀態
                notifications.hideLoading(loadingId);
                
            } finally {
                // 清除載入狀態
                articleCache.clearLoading(articleId);
            }
        }
        
        // 渲染文章內容（從緩存或新載入）
        renderArticleModal(article, articleId);
        
    } catch (error) {
        console.error('載入文章詳情錯誤:', error);
        articleCache.clearLoading(articleId);
        
        notifications.showError(
            '載入失敗', 
            '無法載入文章詳情，請檢查網路連接', 
            [
                { text: '重試', onClick: `showArticleDetail('${articleId}')` },
                { text: '關閉', onClick: `notifications.clear()` }
            ]
        );
    }
}

// 渲染文章模態框內容
function renderArticleModal(article, articleId) {
    // 設置模態框內容
    const modalTitle = document.getElementById('modalTitle');
    if (modalTitle) {
        modalTitle.textContent = article.title;
    }
    
    const modalContent = document.getElementById('modalContent');
    if (modalContent) {
        modalContent.innerHTML = `
            <div class="article-content">
                <div class="mb-3">
                    <strong>分類：</strong>
                    <span class="badge bg-primary">${escapeHtml(article.properties?.主題類別?.select?.name || '未分類')}</span>
                </div>
                <div class="mb-3">
                    <strong>狀態：</strong>
                    <span class="badge bg-success">${escapeHtml(article.properties?.發布狀態?.select?.name || '未知')}</span>
                </div>
                <div class="mb-3">
                    <strong>標籤：</strong>
                    ${(article.properties?.標籤?.multi_select || []).map(tag => 
                        `<span class="tag">#${escapeHtml(tag.name)}</span>`
                    ).join('')}
                </div>
                <div class="mb-3">
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>
                        ${articleCache.has(articleId) ? '從緩存載入' : '新載入'}
                    </small>
                </div>
                <hr>
                <div style="white-space: pre-wrap; line-height: 1.6;">${escapeHtml(article.content)}</div>
            </div>
        `;
    } else {
        console.error('modalContent element not found');
        return;
    }
    
    // 設置 Notion 連結
    const notionLink = document.getElementById('notionLink');
    if (notionLink) {
        notionLink.href = `https://notion.so/${articleId.replace(/-/g, '')}`;
    }
    
    // 顯示模態框
    const articleModalElement = document.getElementById('articleModal');
    if (articleModalElement) {
        const modal = new bootstrap.Modal(articleModalElement);
        modal.show();
    } else {
        console.error('articleModal element not found');
    }
}

// 處理文章生成
async function handleGenerateArticle(event) {
    event.preventDefault();
    
    const generateBtn = document.querySelector('#generateForm button[type="submit"]');
    const loadingId = notifications.showLoading('正在生成財商文章，請稍候...', true);
    
    try {
        console.log('🤖 開始生成文章...');
        
        // 顯示載入狀態
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>生成中...';
        
        // 收集表單資料
        const formData = {
            title: document.getElementById('articleTitle').value,
            topic: document.getElementById('articleTopic').value,
            target_audience: document.getElementById('targetAudience').value,
            writing_style: document.getElementById('writingStyle').value,
            word_count_target: parseInt(document.getElementById('wordCountTarget').value),
            include_case_study: document.getElementById('includeCaseStudy').checked,
            focus_areas: document.getElementById('focusAreas').value
                .split(',')
                .map(area => area.trim())
                .filter(area => area.length > 0)
        };
        
        // 發送生成請求
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '生成失敗');
        }
        
        const result = await response.json();
        currentGeneratedArticle = result;
        
        // 顯示預覽
        showGeneratedPreview(result);
        
        // 滾動到預覽區域
        const previewEl = document.getElementById('generateResult');
        if (previewEl) {
            previewEl.scrollIntoView({ behavior: 'smooth' });
        }
        
        console.log('✅ 文章生成完成');
        
    } catch (error) {
        console.error('❌ 文章生成錯誤:', error);
        alert(`文章生成失敗: ${error.message}`);
    } finally {
        // 恢復按鈕狀態
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic me-2"></i>生成文章';
    }
}

// 顯示生成的文章預覽
function showGeneratedPreview(article) {
    console.log('🎨 顯示文章預覽:', article.title);
    const previewContainer = document.getElementById('generateResult');
    
    previewContainer.innerHTML = `
        <div class="border p-3 rounded bg-white">
            <div class="d-flex justify-content-between align-items-start mb-3">
                <div class="flex-grow-1 me-3">
                    <input type="text" id="editTitle" class="form-control form-control-lg fw-bold text-primary border-0 p-0" 
                           value="${escapeHtml(article.title)}" style="background: transparent;">
                </div>
                <div class="text-end">
                    <select id="editCategory" class="form-select form-select-sm d-inline-block w-auto">
                        <option value="風險管理" ${article.category === '風險管理' ? 'selected' : ''}>風險管理</option>
                        <option value="思維轉換" ${article.category === '思維轉換' ? 'selected' : ''}>思維轉換</option>
                        <option value="實戰技巧" ${article.category === '實戰技巧' ? 'selected' : ''}>實戰技巧</option>
                        <option value="心理素質" ${article.category === '心理素質' ? 'selected' : ''}>心理素質</option>
                        <option value="財富建構" ${article.category === '財富建構' ? 'selected' : ''}>財富建構</option>
                    </select>
                    <div class="small text-muted mt-1">
                        <span id="wordCountDisplay">${article.word_count}</span> 字 • ${article.reading_time} 分鐘閱讀
                    </div>
                    <div class="small">
                        品質分數: <span class="badge bg-success">${article.quality_score.toFixed(1)}</span>
                    </div>
                </div>
            </div>
            
            <div class="mb-3">
                <input type="text" id="editTags" class="form-control form-control-sm" 
                       placeholder="標籤 (用逗號分隔)" 
                       value="${article.tags.join(', ')}">
            </div>
            
            <div class="mb-3">
                <label class="form-label small fw-bold">文章內容:</label>
                <textarea id="editContent" class="form-control" rows="12" 
                          style="font-family: system-ui; line-height: 1.6;"
                          oninput="updateWordCount()">${escapeHtml(article.content)}</textarea>
            </div>
            
            <div class="d-flex justify-content-between">
                <div>
                    <button class="btn btn-outline-secondary btn-sm" onclick="resetToOriginal()">
                        <i class="fas fa-undo me-1"></i>重置
                    </button>
                </div>
                <div class="gap-2 d-flex">
                    <button class="btn btn-outline-primary" onclick="previewChanges()">
                        <i class="fas fa-eye me-1"></i>預覽
                    </button>
                    <button class="btn btn-success" onclick="saveEditedArticle()">
                        <i class="fas fa-save me-1"></i>保存到 Notion
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // 儲存原始文章資料以供重置使用
    window.originalArticle = { ...article };
}

// 顯示保存模態框
function showSaveModal() {
    if (!currentGeneratedArticle) {
        alert('沒有可保存的文章');
        return;
    }
    
    // 設置保存預覽
    const savePreview = document.getElementById('savePreview');
    if (savePreview) {
        savePreview.innerHTML = `
            <h6>${escapeHtml(currentGeneratedArticle.title)}</h6>
            <p class="small text-muted mb-2">
                分類: ${escapeHtml(currentGeneratedArticle.category)} | 
                字數: ${currentGeneratedArticle.word_count} | 
                品質: ${currentGeneratedArticle.quality_score.toFixed(1)}
            </p>
            <div style="max-height: 150px; overflow-y: auto;">
                ${escapeHtml(currentGeneratedArticle.content.substring(0, 200))}...
            </div>
        `;
    } else {
        console.error('savePreview element not found');
        return;
    }
    
    // 顯示模態框
    const saveModalElement = document.getElementById('saveModal');
    if (saveModalElement) {
        const modal = new bootstrap.Modal(saveModalElement);
        modal.show();
    } else {
        console.error('saveModal element not found');
    }
}

// 確認保存文章
async function confirmSaveArticle() {
    if (!currentGeneratedArticle) {
        alert('沒有可保存的文章');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/save-generated`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentGeneratedArticle)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '保存失敗');
        }
        
        const result = await response.json();
        
        // 關閉模態框
        const saveModalElement = document.getElementById('saveModal');
        if (saveModalElement) {
            const modal = bootstrap.Modal.getInstance(saveModalElement);
            if (modal) {
                modal.hide();
            }
        }
        
        // 顯示成功訊息
        alert('文章已成功保存到 Notion 資料庫！');
        
        // 重新載入文章列表
        loadArticles();
        loadDashboard();
        
        // 清空預覽
        const generateResult = document.getElementById('generateResult');
        if (generateResult) {
            generateResult.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
                    <p>文章已成功保存到 Notion 資料庫</p>
                </div>
            `;
        }
        
        currentGeneratedArticle = null;
        
    } catch (error) {
        console.error('保存文章錯誤:', error);
        alert(`保存失敗: ${error.message}`);
    }
}

// 編輯生成的文章（簡單實現）
function editGeneratedArticle() {
    if (!currentGeneratedArticle) return;
    
    const newContent = prompt('請編輯文章內容:', currentGeneratedArticle.content);
    if (newContent !== null) {
        currentGeneratedArticle.content = newContent;
        currentGeneratedArticle.word_count = newContent.length;
        currentGeneratedArticle.reading_time = Math.max(1, Math.round(newContent.length / 250));
        
        showGeneratedPreview(currentGeneratedArticle);
    }
}

// 工具函數

function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
                <p>載入中...</p>
            </div>
        `;
    } else {
        console.warn(`Element with id '${containerId}' not found`);
    }
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger text-center">
                <i class="fas fa-exclamation-circle me-2"></i>
                ${escapeHtml(message)}
            </div>
        `;
    } else {
        console.warn(`Element with id '${containerId}' not found`);
    }
}

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = text.toString();
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '未知';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-TW');
}

// 全域函數（供 HTML 呼叫）
// 編輯相關函數

// 更新字數統計
function updateWordCount() {
    const content = document.getElementById('editContent')?.value || '';
    const wordCount = content.replace(/\s/g, '').length;
    const wordCountDisplay = document.getElementById('wordCountDisplay');
    if (wordCountDisplay) {
        wordCountDisplay.textContent = wordCount;
    }
}

// 重置到原始內容
function resetToOriginal() {
    if (!window.originalArticle) {
        alert('沒有原始文章可以重置');
        return;
    }
    
    const titleInput = document.getElementById('editTitle');
    const categorySelect = document.getElementById('editCategory');
    const tagsInput = document.getElementById('editTags');
    const contentTextarea = document.getElementById('editContent');
    
    if (titleInput) titleInput.value = window.originalArticle.title;
    if (categorySelect) categorySelect.value = window.originalArticle.category;
    if (tagsInput) tagsInput.value = window.originalArticle.tags.join(', ');
    if (contentTextarea) contentTextarea.value = window.originalArticle.content;
    
    updateWordCount();
}

// 預覽變更
function previewChanges() {
    const titleInput = document.getElementById('editTitle');
    const categorySelect = document.getElementById('editCategory');
    const tagsInput = document.getElementById('editTags');
    const contentTextarea = document.getElementById('editContent');
    
    if (!titleInput || !categorySelect || !tagsInput || !contentTextarea) {
        alert('無法讀取編輯內容');
        return;
    }
    
    const title = titleInput.value.trim();
    const category = categorySelect.value;
    const tags = tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    const content = contentTextarea.value.trim();
    const wordCount = content.replace(/\s/g, '').length;
    
    if (!title || !content) {
        alert('標題和內容不能為空');
        return;
    }
    
    // 更新當前生成的文章資料
    currentGeneratedArticle = {
        ...window.originalArticle,
        title: title,
        category: category,
        tags: tags,
        content: content,
        word_count: wordCount,
        reading_time: Math.ceil(wordCount / 300)
    };
    
    // 顯示預覽模態框
    showPreviewModal();
}

// 顯示預覽模態框
function showPreviewModal() {
    const article = currentGeneratedArticle;
    const modalContent = document.getElementById('modalContent');
    
    if (modalContent) {
        modalContent.innerHTML = `
            <div class="article-content">
                <div class="mb-3">
                    <strong>分類：</strong>
                    <span class="badge bg-primary">${escapeHtml(article.category)}</span>
                </div>
                <div class="mb-3">
                    <strong>標籤：</strong>
                    ${article.tags.map(tag => `<span class="tag">#${escapeHtml(tag)}</span>`).join('')}
                </div>
                <div class="mb-3">
                    <strong>字數：</strong> ${article.word_count} 字 • 
                    <strong>閱讀時間：</strong> ${article.reading_time} 分鐘
                </div>
                <hr>
                <div style="white-space: pre-wrap;">${escapeHtml(article.content)}</div>
            </div>
        `;
    }
    
    const modalTitle = document.getElementById('modalTitle');
    if (modalTitle) {
        modalTitle.textContent = article.title;
    }
    
    const articleModalElement = document.getElementById('articleModal');
    if (articleModalElement) {
        const modal = new bootstrap.Modal(articleModalElement);
        modal.show();
    }
}

// 保存編輯後的文章
async function saveEditedArticle() {
    const titleInput = document.getElementById('editTitle');
    const categorySelect = document.getElementById('editCategory');
    const tagsInput = document.getElementById('editTags');
    const contentTextarea = document.getElementById('editContent');
    
    if (!titleInput || !categorySelect || !tagsInput || !contentTextarea) {
        alert('無法讀取編輯內容');
        return;
    }
    
    const title = titleInput.value.trim();
    const category = categorySelect.value;
    const tags = tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    const content = contentTextarea.value.trim();
    const wordCount = content.replace(/\s/g, '').length;
    
    if (!title || !content) {
        alert('標題和內容不能為空');
        return;
    }
    
    try {
        // 更新當前生成的文章資料
        currentGeneratedArticle = {
            ...window.originalArticle,
            title: title,
            category: category,
            tags: tags,
            content: content,
            word_count: wordCount,
            reading_time: Math.ceil(wordCount / 300)
        };
        
        // 顯示載入狀態
        const saveBtn = document.querySelector('button[onclick="saveEditedArticle()"]');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>保存中...';
        }
        
        // 調用保存API
        const response = await fetch(`${API_BASE}/save-generated`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(currentGeneratedArticle)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '保存失敗');
        }
        
        const result = await response.json();
        
        // 顯示成功訊息
        alert('文章已成功保存到 Notion 資料庫！');
        
        // 重新載入文章列表和統計
        loadArticles();
        loadDashboard();
        
        // 顯示成功狀態
        const generateResult = document.getElementById('generateResult');
        if (generateResult) {
            generateResult.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
                    <p>文章已成功保存到 Notion 資料庫</p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fas fa-plus me-1"></i>生成新文章
                    </button>
                </div>
            `;
        }
        
        currentGeneratedArticle = null;
        
    } catch (error) {
        console.error('保存文章錯誤:', error);
        alert(`保存失敗: ${error.message}`);
    } finally {
        // 恢復按鈕狀態
        const saveBtn = document.querySelector('button[onclick="saveEditedArticle()"]');
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>保存到 Notion';
        }
    }
}

// 全域函數暴露
window.showArticleDetail = showArticleDetail;
window.confirmSaveArticle = confirmSaveArticle;
window.showSaveModal = showSaveModal;
window.editGeneratedArticle = editGeneratedArticle;
window.loadArticles = loadArticles;
window.updateWordCount = updateWordCount;
window.resetToOriginal = resetToOriginal;
window.previewChanges = previewChanges;
window.saveEditedArticle = saveEditedArticle;